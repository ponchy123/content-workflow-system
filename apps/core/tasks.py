from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import connection, connections
from datetime import timedelta
import logging
from deploy.backup_script import DatabaseBackup
from .models import ShardedBaseModel
from .cache_warmer import cache_manager
import psutil
import os
import time
from MySQLdb import OperationalError

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5分钟后重试
    rate_limit='1/h',  # 限制每小时执行一次
    queue='maintenance'
)
def backup_database(self):
    """数据库备份任务"""
    try:
        backup = DatabaseBackup()
        backup.run()
        return True
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    rate_limit='1/d',  # 限制每天执行一次
    queue='maintenance'
)
def cleanup_old_data(self):
    """清理旧数据任务"""
    try:
        # 获取所有分表模型
        sharded_models = [
            model for model in apps.get_models()
            if issubclass(model, ShardedBaseModel)
        ]
        
        # 获取需要保留的最早日期（例如：保留最近12个月的数据）
        cutoff_date = timezone.now().date() - timedelta(days=365)
        
        for model in sharded_models:
            # 获取所有分表
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name LIKE %s
                """, [f"{model._meta.db_table}_%"])
                tables = cursor.fetchall()
            
            # 删除旧表
            for (table_name,) in tables:
                try:
                    table_date = datetime.strptime(
                        table_name.split('_')[-1],
                        '%Y%m'
                    ).date()
                    if table_date < cutoff_date:
                        with connection.cursor() as cursor:
                            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                            logger.info(f"Dropped old table: {table_name}")
                except Exception as e:
                    logger.error(f"Failed to drop table {table_name}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        raise self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1分钟后重试
    rate_limit='1/h',  # 限制每小时执行一次
    queue='maintenance'
)
def warm_cache(self):
    """缓存预热任务"""
    try:
        cache_manager.warm_all_caches()
        return True
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit='12/h',  # 限制每5分钟执行一次
    queue='monitoring'
)
def monitor_system_health(self):
    """
    监控系统健康状态
    检查CPU、内存、磁盘使用率，以及数据库连接
    """
    try:
        # 检查CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:  # CPU使用率超过80%
            logger.warning(f"High CPU usage: {cpu_percent}%")
        
        # 检查内存使用率
        memory = psutil.virtual_memory()
        if memory.percent > 80:  # 内存使用率超过80%
            logger.warning(f"High memory usage: {memory.percent}%")
        
        # 检查磁盘使用率
        disk = psutil.disk_usage('/')
        if disk.percent > 80:  # 磁盘使用率超过80%
            logger.warning(f"High disk usage: {disk.percent}%")
        
        # 检查数据库连接
        try:
            # 关闭旧连接并重新创建
            for conn in connections.all():
                conn.close_if_unusable_or_obsolete()
                
            # 尝试执行简单查询
            max_attempts = 3
            retry_delay = 1
            
            for attempt in range(max_attempts):
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                    break  # 成功执行后退出循环
                except OperationalError as e:
                    if attempt < max_attempts - 1:
                        logger.warning(f"Database connection attempt {attempt+1} failed, retrying: {e}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        logger.error(f"Database connection failed after {max_attempts} attempts: {e}")
                        raise  # 重新抛出异常，触发任务重试
        except Exception as db_error:
            logger.error(f"Database health check failed: {db_error}")
            # 记录错误但继续执行其他检查
        
        # 检查缓存服务
        try:
            cache.get('health_check')
        except Exception as cache_error:
            logger.error(f"Cache health check failed: {cache_error}")
            # 记录错误但继续执行
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # 增加重试次数，最多重试5次
        if self.request.retries < 5:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        return {
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5分钟后重试
    rate_limit='1/d',  # 限制每天执行一次
    queue='maintenance'
)
def clean_old_records(self):
    """清理过期数据记录"""
    try:
        logger.info("开始清理过期数据记录")
        
        # 获取配置的保留期限（默认30天）
        retention_days = getattr(settings, 'DATA_RETENTION_DAYS', 30)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # 清理过期的日志记录
        from apps.core.models import SystemLog, ApiRequestLog
        deleted_logs = SystemLog.objects.filter(created_at__lt=cutoff_date).delete()
        deleted_api_logs = ApiRequestLog.objects.filter(request_time__lt=cutoff_date).delete()
        
        # 清理过期的临时文件
        from apps.core.models import TemporaryFile
        deleted_files = TemporaryFile.objects.filter(expiry_time__lt=timezone.now()).delete()
        
        # 清理过期的Token
        from apps.core.models import TokenBlacklist
        deleted_tokens = TokenBlacklist.objects.filter(expiry_time__lt=timezone.now()).delete()
        
        logger.info(f"清理完成: {deleted_logs[0]}条系统日志, {deleted_api_logs[0]}条API日志, "
                   f"{deleted_files[0]}个临时文件, {deleted_tokens[0]}个过期Token")
        
        return {
            'deleted_logs': deleted_logs[0] if isinstance(deleted_logs, tuple) else 0,
            'deleted_api_logs': deleted_api_logs[0] if isinstance(deleted_api_logs, tuple) else 0,
            'deleted_files': deleted_files[0] if isinstance(deleted_files, tuple) else 0,
            'deleted_tokens': deleted_tokens[0] if isinstance(deleted_tokens, tuple) else 0,
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"清理过期数据记录失败: {e}")
        raise self.retry(exc=e)