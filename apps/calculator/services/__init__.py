"""
计算器服务模块
包含各种计算服务的实现
"""

# 导出基础服务，供外部使用
from apps.calculator.services.base_calculation_service import BaseCalculationService
from apps.calculator.services.batch_service import BatchService
from apps.calculator.services.cache_service import CacheService
from apps.calculator.services.validation_service import ValidationService
from apps.calculator.services.audit_service import AuditService

# 创建兼容旧API的服务类，实现无缝过渡
class CalculationService:
    """
    兼容旧版API的计算服务
    该类将调用请求路由到相应的新服务模块
    """
    
    def __init__(self):
        self.base_service = BaseCalculationService()
        self.batch_service = BatchService()
        self.cache_service = CacheService()
        self.validation_service = ValidationService()
        self.audit_service = AuditService()
    
    def calculate_single(self, data):
        """单件运费计算，兼容旧版API"""
        return self.base_service.calculate(data)
    
    def calculate_batch(self, items):
        """批量运费计算，兼容旧版API"""
        return self.batch_service.process_batch(items)
    
    def compare_products(self, data):
        """产品比较，兼容旧版API"""
        return self.base_service.compare_products(data)

# 保持导出兼容性
__all__ = [
    "BaseCalculationService",
    "BatchService",
    "CacheService",
    "ValidationService",
    "AuditService",
    "CalculationService",
] 