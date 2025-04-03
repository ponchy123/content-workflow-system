from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CalculationRequest, BatchCalculationTask

@receiver(post_save, sender=CalculationRequest)
def calculation_request_post_save(sender, instance, created, **kwargs):
    """处理计算请求保存后的操作"""
    pass

@receiver(post_save, sender=BatchCalculationTask)
def batch_task_post_save(sender, instance, created, **kwargs):
    """处理批量任务保存后的操作"""
    pass 