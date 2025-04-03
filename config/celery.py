from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
import multiprocessing
from datetime import timedelta

# 获取CPU核心数
cpu_count = multiprocessing.cpu_count()

# 根据CPU核心数优化配置
OPTIMAL_WORKER_COUNT = max(2, min(cpu_count * 2, 16))  # 确保至少2个worker，最多16个
OPTIMAL_THREAD_COUNT = max(4, min(cpu_count * 4, 32))  # 确保至少4个线程，最多32个
OPTIMAL_CHUNK_SIZE = 5000 * (cpu_count // 4 + 1)  # 根据CPU核心数调整块大小

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('freight')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# 配置定时任务
app.conf.beat_schedule = {
    'backup-database': {
        'task': 'apps.core.tasks.backup_database',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
        'options': {'queue': 'maintenance'}
    },
    'clean-old-records': {
        'task': 'apps.core.tasks.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨3点执行
        'options': {'queue': 'maintenance'}
    },
    'warm-cache': {
        'task': 'apps.core.tasks.warm_cache',
        'schedule': crontab(minute=0, hour='*/4'),  # 每4小时执行一次
        'options': {'queue': 'maintenance'}
    },
    'monitor-system-resources': {
        'task': 'apps.core.tasks.monitor_system_health',
        'schedule': crontab(minute='*/5'),  # 每5分钟执行一次
        'options': {'queue': 'monitoring'}
    },
}

# 配置任务队列
app.conf.task_queues = {
    'high': {
        'exchange': 'high',
        'routing_key': 'high',
        'queue_arguments': {'x-max-priority': 10}
    },
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
        'queue_arguments': {'x-max-priority': 5}
    },
    'low': {
        'exchange': 'low',
        'routing_key': 'low',
        'queue_arguments': {'x-max-priority': 1}
    },
    'maintenance': {
        'exchange': 'maintenance',
        'routing_key': 'maintenance',
    },
    'monitoring': {
        'exchange': 'monitoring',
        'routing_key': 'monitoring',
    },
}

# 配置任务路由
app.conf.task_routes = {
    'apps.calculator.tasks.process_calculation_chunk': {
        'queue': lambda task, args, kwargs: (
            'high' if args and args[0].get('priority') == 2
            else 'low' if args and args[0].get('priority') == 0
            else 'default'
        ),
    },
    'apps.core.tasks.backup_database': {'queue': 'maintenance'},
    'apps.core.tasks.cleanup_old_data': {'queue': 'maintenance'},
    'apps.core.tasks.warm_cache': {'queue': 'maintenance'},
    'apps.core.tasks.monitor_system_health': {'queue': 'monitoring'},
}

# 配置任务默认设置
app.conf.update(
    # 基本配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务执行配置
    task_track_started=True,
    task_time_limit=7200,        # 2小时
    task_soft_time_limit=6900,   # 1小时55分钟
    
    # Worker配置 - 根据CPU核心数优化
    worker_max_tasks_per_child=1000 * (cpu_count // 4 + 1),  # 根据CPU核心数调整最大任务数
    worker_prefetch_multiplier=1,    # 禁用预取，确保公平分配
    worker_concurrency=OPTIMAL_WORKER_COUNT,  # 使用优化后的worker数
    
    # 性能优化
    task_acks_late=True,              # 任务完成后再确认
    task_reject_on_worker_lost=True,  # worker丢失时拒绝任务
    task_default_rate_limit=f'{2000 * (cpu_count // 4 + 1)}/m',  # 根据CPU核心数调整速率限制
    
    # 结果后端配置
    result_backend='django-db',
    result_expires=timedelta(days=7),  # 结果保存7天
    
    # 错误处理
    task_annotations={
        '*': {
            'rate_limit': f'{2000 * (cpu_count // 4 + 1)}/m',  # 动态调整速率限制
            'max_retries': 5,
            'default_retry_delay': 300,
            'retry_backoff': True,  # 使用指数退避
        }
    },
    
    # 优化设置
    broker_transport_options={
        'visibility_timeout': 7200,
        'max_retries': 5,
        'interval_start': 0,
        'interval_step': 0.5,
        'interval_max': 3,
    },
)

# 导出配置供其他模块使用
app.conf.OPTIMAL_WORKER_COUNT = OPTIMAL_WORKER_COUNT
app.conf.OPTIMAL_THREAD_COUNT = OPTIMAL_THREAD_COUNT
app.conf.OPTIMAL_CHUNK_SIZE = OPTIMAL_CHUNK_SIZE

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 