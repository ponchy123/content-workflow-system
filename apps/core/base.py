from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    基础模型类，包含通用字段
    """
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    is_deleted = models.BooleanField('是否删除', default=False)
    remarks = models.TextField('备注', null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at'] 