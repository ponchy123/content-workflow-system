import os
import pandas as pd
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .services import CalculationService
from .models import BatchCalculationTask
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from django.db import models, transaction
import gc
from celery.app import default_app
from apps.core.batch_processor import BatchProcessor
from apps.core.utils import generate_request_id

logger = logging.getLogger('freight.app')

def send_task_update(task_id: str, data: dict):
    """发送任务更新到WebSocket"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"task_{task_id}",
            {
                "type": "task.update",
                "data": data
            }
        )
    except Exception as e:
        logger.error(f"发送任务更新失败: {str(e)}")

@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def process_calculation_chunk(self, task_id: str, chunk_start: int, chunk_size: int):
    """处理计算块（优化版本）"""
    try:
        task = BatchCalculationTask.objects.select_related('product').get(task_id=task_id)
        
        # 检查任务是否已取消
        if task.status == 'CANCELLED':
            return False
            
        service = CalculationService(task.product_id)
        
        # 使用优化的Excel读取设置
        df = pd.read_excel(
            task.original_file,
            skiprows=chunk_start,
            nrows=chunk_size,
            dtype={
                '长': 'float32',
                '宽': 'float32',
                '高': 'float32',
                '实重': 'float32',
                '起始邮编': 'str',
                '收件邮编': 'str'
            },
            engine='openpyxl'
        )
        
        # 创建批量处理器
        processor = BatchProcessor(
            processor_func=service.calculate_single,
            progress_callback=lambda task_id, progress: send_task_update(task_id, progress)
        )
        
        # 预处理数据
        processed_df, errors = service._preprocess_data(df)
        
        if not processed_df.empty:
            # 优化数据分块
            processed_df = processor.optimize_data_chunks(processed_df)
            records = processed_df.to_dict('records')
            
            # 处理数据块
            with transaction.atomic():
                result = processor.process_batch(task_id, records)
                
                # 更新任务状态
                task.processed_records += len(df)
                task.success_records += len(result['results'])
                task.error_records += len(result['errors'])
                task.current_chunk += 1
                task.save()
                
                # 记录错误信息
                if result['errors']:
                    error_file = os.path.join(settings.MEDIA_ROOT, f'errors_{task_id}_{chunk_start}.csv')
                    pd.DataFrame(result['errors']).to_csv(error_file, index=False)
        
        # 清理内存
        del df
        gc.collect()
            
        return True
    except Exception as e:
        logger.error(f"处理计算块失败: {str(e)}", exc_info=True)
        if self.request.retries >= self.max_retries:
            task.status = 'FAILED'
            task.last_error = str(e)
            task.save()
            send_task_update(task_id, {'status': 'FAILED', 'error': str(e)})
        raise self.retry(exc=e)

@shared_task
def process_batch_calculation(task_id: str):
    """处理批量计算任务（优化版本）"""
    try:
        task = BatchCalculationTask.objects.get(task_id=task_id)
        task.status = 'PROCESSING'
        task.save()
        
        # 设置过期时间（15天后）
        task.expires_at = timezone.now() + timedelta(days=15)
        task.save()
        
        # 计算总块数
        total_records = task.total_records
        total_chunks = (total_records + settings.OPTIMAL_CHUNK_SIZE - 1) // settings.OPTIMAL_CHUNK_SIZE
        task.total_chunks = total_chunks
        task.save()
        
        # 发送任务开始通知
        send_task_update(task_id, {
            'status': 'PROCESSING',
            'total_records': total_records,
            'total_chunks': total_chunks
        })
        
        # 根据优先级和CPU核心数调整并发数
        queue = 'high' if task.priority == 2 else 'low' if task.priority == 0 else 'default'
        concurrent_chunks = getattr(settings, 'OPTIMAL_WORKER_COUNT', os.cpu_count()) * (
            2 if task.priority == 2 else  # 高优先级使用2倍并发
            1 if task.priority == 1 else  # 普通优先级使用标准并发
            0.5  # 低优先级使用一半并发
        )
        concurrent_chunks = int(max(1, concurrent_chunks))  # 确保至少1个并发
        
        # 分批启动处理任务
        for i in range(0, total_chunks, concurrent_chunks):
            chunk_group = []
            for j in range(concurrent_chunks):
                if i + j < total_chunks:
                    chunk_start = (i + j) * settings.OPTIMAL_CHUNK_SIZE
                    chunk_group.append(
                        process_calculation_chunk.s(task_id, chunk_start, settings.OPTIMAL_CHUNK_SIZE)
                    )
            
            # 使用group执行并等待结果
            from celery import group
            group(chunk_group).apply_async(queue=queue)
        
        return True
    except Exception as e:
        logger.error(f"启动批量计算任务失败: {str(e)}", exc_info=True)
        task.status = 'FAILED'
        task.last_error = str(e)
        task.save()
        send_task_update(task_id, {'status': 'FAILED', 'error': str(e)})
        return False

@shared_task
def retry_failed_tasks():
    """重试失败任务"""
    try:
        with transaction.atomic():
            tasks = BatchCalculationTask.objects.select_for_update().filter(
                status='FAILED',
                retry_count__lt=models.F('max_retries')
            )
            
            for task in tasks:
                task.retry_count += 1
                task.status = 'PENDING'
                task.save()
                
                # 使用延迟队列避免立即重试
                process_batch_calculation.apply_async(
                    args=[task.task_id],
                    countdown=300 * task.retry_count  # 递增延迟时间
                )
    except Exception as e:
        logger.error(f"重试失败任务时出错: {str(e)}", exc_info=True)

@shared_task
def cleanup_expired_tasks():
    """清理过期任务"""
    try:
        expired_tasks = BatchCalculationTask.objects.filter(
            expires_at__lt=timezone.now()
        ).exclude(
            status__in=['PROCESSING']
        ).select_for_update(skip_locked=True)
        
        for task in expired_tasks:
            try:
                with transaction.atomic():
                    # 清理文件
                    task.clean_files()
                    # 记录清理操作
                    logger.info(f"已清理过期任务: {task.task_id}")
                    # 删除任务记录
                    task.delete()
            except Exception as e:
                logger.error(f"清理任务失败: {task.task_id}, 错误: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"清理过期任务时出错: {str(e)}", exc_info=True)

@shared_task
def export_calculation_results(task_id: str):
    """导出计算结果"""
    try:
        task = BatchCalculationTask.objects.get(task_id=task_id)
        
        # 分批获取计算结果
        calculations = task.calculationrequest_set.all()
        batch_size = 5000
        total = calculations.count()
        
        # 创建Excel写入器
        result_file = os.path.join(settings.MEDIA_ROOT, f'results_{task_id}.xlsx')
        writer = pd.ExcelWriter(result_file, engine='xlsxwriter')
        
        for offset in range(0, total, batch_size):
            batch = calculations[offset:offset + batch_size].prefetch_related('details')
            
            results = []
            for calc in batch:
                result = {
                    '请求ID': calc.request_id,
                    '长': float(calc.length),
                    '宽': float(calc.width),
                    '高': float(calc.height),
                    '实重': float(calc.weight),
                    '体积重': float(calc.volume_weight),
                    '计费重量': float(calc.chargeable_weight),
                    '起始邮编': calc.from_postal,
                    '目的邮编': calc.to_postal,
                    '总费用': float(calc.total_fee)
                }
                
                for detail in calc.details.all():
                    result[detail.fee_name] = float(detail.amount)
                
                results.append(result)
            
            # 写入当前批次数据
            if offset == 0:
                pd.DataFrame(results).to_excel(writer, index=False, sheet_name='计算结果')
            else:
                pd.DataFrame(results).to_excel(writer, index=False, sheet_name=f'计算结果_{offset//batch_size + 1}')
        
        writer.close()
        
        # 更新任务状态
        task.result_file = result_file
        task.status = 'EXPORTED'
        task.save()
        
        return True
    except Exception as e:
        logger.error(f"导出计算结果失败: {str(e)}", exc_info=True)
        task.status = 'EXPORT_FAILED'
        task.last_error = str(e)
        task.save()
        return False 