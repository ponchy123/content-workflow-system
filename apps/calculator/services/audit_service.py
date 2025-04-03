"""
审计日志服务
负责记录计算操作相关的操作日志
"""

import logging
import json
from typing import Dict, Any, Optional, List
from decimal import Decimal

from django.utils import timezone
from django.contrib.auth.models import User

from apps.core.models import AuditLog
from apps.calculator.models import Calculation

logger = logging.getLogger(__name__)

class AuditService:
    """
    审计日志服务类
    负责记录计算操作相关的操作日志
    """
    
    def __init__(self):
        """初始化审计日志服务"""
        self.logger = logging.getLogger(__name__)
    
    def log_calculation(self, calculation: Calculation, user: User = None, 
                       request_data: Dict[str, Any] = None, success: bool = True,
                       error_message: str = None) -> Optional[AuditLog]:
        """
        记录计算操作日志
        
        Args:
            calculation: 计算结果对象
            user: 用户对象，默认为None
            request_data: 请求数据，默认为None
            success: 是否成功，默认为True
            error_message: 错误消息，默认为None
            
        Returns:
            Optional[AuditLog]: 审计日志对象，如果记录失败则为None
        """
        try:
            # 掩码敏感数据
            masked_data = self._mask_sensitive_data(request_data) if request_data else {}
            
            # 准备日志数据
            log_data = {
                'module': 'calculator',
                'operation': 'calculate_freight',
                'status': 'success' if success else 'failed',
                'result_code': calculation.request_id if calculation else None,
                'user_id': user.id if user else None,
                'username': user.username if user else 'system',
                'request_data': json.dumps(masked_data, default=self._json_serializer),
                'response_data': json.dumps({
                    'request_id': calculation.request_id if calculation else None,
                    'product_id': calculation.product_id if calculation else None,
                    'total_fee': str(calculation.total_fee) if calculation else None,
                    'currency': calculation.currency if calculation else None,
                    'status': calculation.status if calculation else None
                }, default=self._json_serializer),
                'error_message': error_message,
                'client_ip': None,  # 可以在视图层获取并传入
                'created_at': timezone.now()
            }
            
            # 创建审计日志
            audit_log = AuditLog.objects.create(**log_data)
            
            self.logger.info(f"已记录计算操作日志: {audit_log.id}")
            return audit_log
        
        except Exception as e:
            self.logger.error(f"记录审计日志失败: {str(e)}")
            return None
    
    def log_batch_calculation(self, task_id: str, user: User = None,
                           record_count: int = 0, success_count: int = 0,
                           failed_count: int = 0, error_message: str = None) -> Optional[AuditLog]:
        """
        记录批量计算操作日志
        
        Args:
            task_id: 任务ID
            user: 用户对象，默认为None
            record_count: 记录总数，默认为0
            success_count: 成功记录数，默认为0
            failed_count: 失败记录数，默认为0
            error_message: 错误消息，默认为None
            
        Returns:
            Optional[AuditLog]: 审计日志对象，如果记录失败则为None
        """
        try:
            # 准备日志数据
            log_data = {
                'module': 'calculator',
                'operation': 'batch_calculate_freight',
                'status': 'success' if not error_message else 'failed',
                'result_code': task_id,
                'user_id': user.id if user else None,
                'username': user.username if user else 'system',
                'request_data': json.dumps({
                    'task_id': task_id,
                    'record_count': record_count
                }),
                'response_data': json.dumps({
                    'task_id': task_id,
                    'record_count': record_count,
                    'success_count': success_count,
                    'failed_count': failed_count
                }),
                'error_message': error_message,
                'client_ip': None,
                'created_at': timezone.now()
            }
            
            # 创建审计日志
            audit_log = AuditLog.objects.create(**log_data)
            
            self.logger.info(f"已记录批量计算操作日志: {audit_log.id}")
            return audit_log
        
        except Exception as e:
            self.logger.error(f"记录批量计算审计日志失败: {str(e)}")
            return None
    
    def log_cache_operation(self, operation_type: str, cache_key: str = None,
                         user: User = None, success: bool = True,
                         error_message: str = None) -> Optional[AuditLog]:
        """
        记录缓存操作日志
        
        Args:
            operation_type: 操作类型（如'invalidate', 'warm'）
            cache_key: 缓存键，默认为None
            user: 用户对象，默认为None
            success: 是否成功，默认为True
            error_message: 错误消息，默认为None
            
        Returns:
            Optional[AuditLog]: 审计日志对象，如果记录失败则为None
        """
        try:
            # 准备日志数据
            log_data = {
                'module': 'calculator',
                'operation': f'cache_{operation_type}',
                'status': 'success' if success else 'failed',
                'result_code': None,
                'user_id': user.id if user else None,
                'username': user.username if user else 'system',
                'request_data': json.dumps({
                    'cache_key': cache_key,
                    'operation': operation_type
                }),
                'response_data': json.dumps({
                    'success': success
                }),
                'error_message': error_message,
                'client_ip': None,
                'created_at': timezone.now()
            }
            
            # 创建审计日志
            audit_log = AuditLog.objects.create(**log_data)
            
            self.logger.info(f"已记录缓存操作日志: {audit_log.id}")
            return audit_log
        
        except Exception as e:
            self.logger.error(f"记录缓存操作审计日志失败: {str(e)}")
            return None
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        掩码敏感数据
        
        Args:
            data: 原始数据
            
        Returns:
            Dict[str, Any]: 掩码后的数据
        """
        if not data:
            return {}
        
        masked_data = data.copy()
        
        # 掩码邮编
        for field in ['from_postal', 'to_postal']:
            if field in masked_data and masked_data[field]:
                postal = str(masked_data[field])
                if len(postal) > 3:
                    masked_data[field] = postal[:2] + '*' * (len(postal) - 3) + postal[-1]
        
        return masked_data
    
    def _json_serializer(self, obj):
        """
        自定义JSON序列化处理器
        
        Args:
            obj: 要序列化的对象
            
        Returns:
            合适的可JSON序列化的值
        """
        if isinstance(obj, Decimal):
            return str(obj)
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj) 