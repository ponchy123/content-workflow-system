"""
批量处理服务
处理运费批量计算相关功能
"""

import logging
import sys
from typing import Dict, List, Any
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.contrib.auth.models import User
from django.utils import timezone

from apps.core.batch_processor import BaseBatchProcessor
from apps.calculator.calculator import Calculator
from apps.core.exceptions import CalculationException
from apps.calculator.models import BatchCalculationTask

logger = logging.getLogger(__name__)

class BatchService(BaseBatchProcessor):
    """
    批量计算服务类
    处理批量运费计算请求
    """
    
    def __init__(self, max_workers: int = 5):
        """
        初始化批量处理服务
        
        Args:
            max_workers: 最大工作线程数，默认为5
        """
        super().__init__()
        self.max_workers = max_workers
        self.calculator = Calculator()
        self.logger = logging.getLogger(__name__)
    
    def process_batch(self, records: List[Dict], task_id: str = None, 
                    user: User = None) -> Dict:
        """
        批量处理计算请求
        
        Args:
            records: 计算记录列表
            task_id: 任务ID，默认为None
            user: 用户对象，默认为None
            
        Returns:
            Dict: 批量处理结果
        """
        if not records:
            return {
                'status': 'success',
                'code': 'SUCCESS',
                'message': '批量计算完成',
                'data': {
                    'results': [],
                    'total': 0,
                    'success': 0,
                    'failed': 0
                },
                'timestamp': timezone.now().isoformat()
            }
        
        print(f"\n========== 开始批量计算 ==========", file=sys.stdout)
        print(f"总记录数: {len(records)}", file=sys.stdout)
        
        # 初始化任务
        if task_id and BatchCalculationTask.objects.filter(task_id=task_id).exists():
            task = BatchCalculationTask.objects.get(task_id=task_id)
            task.status = 'PROCESSING'
            task.total_records = len(records)
            task.processed_records = 0
            task.success_records = 0
            task.failed_records = 0
            task.save()
        else:
            task = None
        
        results = []
        success_count = 0
        failed_count = 0
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 创建future对象
            future_to_record = {
                executor.submit(self.process_single, record): record 
                for record in records
            }
            
            # 处理完成的future
            for i, future in enumerate(as_completed(future_to_record)):
                record = future_to_record[future]
                processed_count = i + 1
                
                try:
                    result = future.result()
                    results.append({
                        'status': 'success',
                        'data': result,
                        'error': None
                    })
                    success_count += 1
                    
                    print(f"处理成功 [{processed_count}/{len(records)}]", file=sys.stdout)
                except Exception as e:
                    results.append({
                        'status': 'error',
                        'data': None,
                        'error': str(e)
                    })
                    failed_count += 1
                    
                    print(f"处理失败 [{processed_count}/{len(records)}]: {str(e)}", file=sys.stdout)
                
                # 更新任务进度
                if task:
                    task.processed_records = processed_count
                    task.success_records = success_count
                    task.failed_records = failed_count
                    task.save()
                
                # 输出进度信息
                if processed_count % 10 == 0 or processed_count == len(records):
                    print(f"进度: {processed_count}/{len(records)}", file=sys.stdout)
                    print(f"成功: {success_count}, 失败: {failed_count}", file=sys.stdout)
        
        # 更新任务状态
        if task:
            task.status = 'COMPLETED'
            task.save()
        
        print(f"\n========== 批量计算完成 ==========", file=sys.stdout)
        print(f"总记录数: {len(records)}", file=sys.stdout)
        print(f"成功记录数: {success_count}", file=sys.stdout)
        print(f"失败记录数: {failed_count}", file=sys.stdout)
        
        return {
            'status': 'success',
            'code': 'SUCCESS',
            'message': '批量计算完成',
            'data': {
                'results': results,
                'total': len(records),
                'success': success_count,
                'failed': failed_count
            },
            'timestamp': timezone.now().isoformat()
        }
    
    def process_single(self, record: Dict) -> Dict:
        """
        处理单条记录
        
        Args:
            record: 单条记录数据
            
        Returns:
            Dict: 计算结果
        """
        try:
            # 使用新的Calculator类计算
            return self.calculator.calculate(record)
        except Exception as e:
            logger.error(f"处理记录时发生错误: {str(e)}")
            raise CalculationException(str(e)) 