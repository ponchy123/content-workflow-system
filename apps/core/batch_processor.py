from django.conf import settings
import logging
import time
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import psutil
from typing import Optional, List, Dict, Any, Callable, Tuple
from datetime import datetime, timedelta
import pandas as pd
from multiprocessing import cpu_count
import json
from decimal import Decimal
from django.utils import timezone
from apps.core.constants import (
    MAX_WORKERS,
    BATCH_CHUNK_SIZE,
    MAX_BATCH_RECORDS,
    BULK_INSERT_SIZE,
    PROCESSING_TIMEOUT,
    OPTIMAL_CHUNK_SIZE
)
from apps.core.utils import chunk_list
from apps.core.exceptions import BatchProcessingException
from apps.core.decorators import db_connection_retry

logger = logging.getLogger(__name__)

class BaseBatchProcessor:
    """批量处理基类"""
    
    def __init__(self, max_records: int = MAX_BATCH_RECORDS, chunk_size: int = BATCH_CHUNK_SIZE):
        self.max_records = max_records
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)
        self._results = []
        self._errors = []
        self._lock = threading.Lock()

    def validate_batch(self, records: List[Dict]) -> None:
        """
        验证批量数据
        Args:
            records: 记录列表
        Raises:
            BatchProcessingException: 当验证失败时抛出
        """
        if not records:
            raise BatchProcessingException("记录列表为空")
        
        if len(records) > self.max_records:
            raise BatchProcessingException(f"记录数量超过最大限制: {self.max_records}")

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def process_single(self, record: Dict) -> Dict:
        """
        处理单条记录，子类必须实现此方法
        Args:
            record: 单条记录
        Returns:
            Dict: 处理结果
        """
        raise NotImplementedError("子类必须实现process_single方法")

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _process_chunk(self, chunk: List[Dict]) -> None:
        """
        处理数据块
        Args:
            chunk: 数据块
        """
        for record in chunk:
            try:
                result = self.process_single(record)
                with self._lock:
                    self._results.append(result)
            except Exception as e:
                self.logger.error(f"处理记录失败: {str(e)}", exc_info=True)
                with self._lock:
                    self._errors.append({
                        'record': record,
                        'error': str(e)
                    })

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def process_batch(self, task_id: str, records: List[Dict]) -> Dict[str, Any]:
        """
        批量处理记录
        Args:
            task_id: 任务ID
            records: 记录列表
        Returns:
            Dict: 处理结果
        """
        try:
            # 验证输入数据
            self.validate_batch(records)
            
            # 清空上次的结果
            self._results = []
            self._errors = []
            
            # 分块处理
            chunks = chunk_list(records, self.chunk_size)
            
            # 使用线程池处理数据块
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [
                    executor.submit(self._process_chunk, chunk)
                    for chunk in chunks
                ]
                concurrent.futures.wait(futures)
            
            return {
                'task_id': task_id,
                'total': len(records),
                'success': len(self._results),
                'failed': len(self._errors),
                'results': self._results,
                'errors': self._errors
            }
            
        except Exception as e:
            self.logger.error(f"批量处理失败: {str(e)}", exc_info=True)
            raise BatchProcessingException(str(e))

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """
        获取处理进度
        Args:
            task_id: 任务ID
        Returns:
            Dict: 进度信息
        """
        total = len(self._results) + len(self._errors)
        return {
            'task_id': task_id,
            'total': total,
            'processed': len(self._results),
            'success': len(self._results),
            'failed': len(self._errors),
            'progress': (total / self.max_records) * 100 if self.max_records > 0 else 0
        }


class BatchProcessor:
    """通用批处理器"""
    
    def __init__(self, 
                 processor_func: Callable,
                 max_workers: int = MAX_WORKERS,
                 chunk_size: int = BATCH_CHUNK_SIZE,
                 progress_callback: Optional[Callable] = None):
        """
        初始化批处理器
        Args:
            processor_func: 处理函数
            max_workers: 最大工作线程数
            chunk_size: 数据块大小
            progress_callback: 进度回调函数
        """
        self.processor_func = processor_func
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def process_batch(self, task_id: str, records: list, **kwargs) -> dict:
        """
        批量处理记录
        Args:
            task_id: 任务ID
            records: 记录列表
            **kwargs: 额外参数
        Returns:
            dict: 处理结果
        """
        try:
            # 根据记录数量决定使用并行还是串行处理
            if len(records) > self.chunk_size:
                return self._process_batch_parallel(task_id, records, **kwargs)
            else:
                return self._process_batch_sequential(task_id, records, **kwargs)
        except Exception as e:
            self.logger.error(f"批量处理失败: {str(e)}", exc_info=True)
            raise BatchProcessingException(str(e))

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _process_batch_parallel(self, task_id: str, records: list, **kwargs) -> dict:
        """
        并行处理批量记录
        """
        results = []
        errors = []
        processed = 0
        total = len(records)
        
        # 分块处理
        chunks = chunk_list(records, self.chunk_size)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for chunk in chunks:
                future = executor.submit(self._process_chunk_parallel, chunk, **kwargs)
                futures.append(future)
            
            # 处理结果
            for future in concurrent.futures.as_completed(futures):
                try:
                    chunk_result = future.result()
                    results.extend(chunk_result.get('results', []))
                    errors.extend(chunk_result.get('errors', []))
                    processed += len(chunk_result.get('results', []))
                    
                    # 更新进度
                    if self.progress_callback:
                        progress = (processed / total) * 100
                        self.progress_callback(task_id, progress)
                        
                except Exception as e:
                    self.logger.error(f"处理数据块失败: {str(e)}", exc_info=True)
                    errors.append({
                        'error': str(e),
                        'type': 'chunk_processing_error'
                    })
        
        return {
            'task_id': task_id,
            'total': total,
            'processed': processed,
            'success': len(results),
            'failed': len(errors),
            'results': results,
            'errors': errors
        }

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _process_chunk_parallel(self, chunk: list, **kwargs) -> dict:
        """
        并行处理数据块
        """
        results = []
        errors = []
        
        for record in chunk:
            try:
                result = self.processor_func(record, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"处理记录失败: {str(e)}", exc_info=True)
                errors.append({
                    'record': record,
                    'error': str(e)
                })
        
        return {
            'results': results,
            'errors': errors
        }

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _process_batch_sequential(self, task_id: str, records: list, **kwargs) -> dict:
        """
        串行处理批量记录
        """
        results = []
        errors = []
        processed = 0
        total = len(records)
        
        for record in records:
            try:
                result = self.processor_func(record, **kwargs)
                results.append(result)
                processed += 1
                
                # 更新进度
                if self.progress_callback:
                    progress = (processed / total) * 100
                    self.progress_callback(task_id, progress)
                    
            except Exception as e:
                self.logger.error(f"处理记录失败: {str(e)}", exc_info=True)
                errors.append({
                    'record': record,
                    'error': str(e)
                })
        
        return {
            'task_id': task_id,
            'total': total,
            'processed': processed,
            'success': len(results),
            'failed': len(errors),
            'results': results,
            'errors': errors
        }

    @staticmethod
    def optimize_data_chunks(df: pd.DataFrame) -> pd.DataFrame:
        """
        优化数据块，按照特定规则分组
        Args:
            df: 待优化的DataFrame
        Returns:
            pd.DataFrame: 优化后的DataFrame
        """
        # 按邮编对分组
        df['postal_group'] = df['from_postal'].astype(str).str[:2]
        
        # 按重量范围分组
        df['weight_group'] = pd.qcut(df['weight'], 
                                   q=min(10, len(df)), 
                                   labels=False,
                                   duplicates='drop')
        
        # 按分组排序
        df.sort_values(['postal_group', 'weight_group'], inplace=True)
        
        # 删除辅助列
        df.drop(['postal_group', 'weight_group'], axis=1, inplace=True)
        
        return df 