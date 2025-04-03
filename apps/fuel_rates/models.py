from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from apps.core.models import BaseModel, ServiceProvider
from decimal import Decimal
import datetime


def generate_rate_id():
    """生成费率ID：FR + 年月日 + 2位序号"""
    today = datetime.date.today()
    base = f"FR{today.strftime('%y%m%d')}"
    # 查找当天最大序号
    existing = FuelRate.objects.filter(rate_id__startswith=base).order_by('-rate_id').first()
    if existing:
        seq = int(existing.rate_id[-2:]) + 1
    else:
        seq = 1
    return f"{base}{seq:02d}"


class FuelRate(BaseModel):
    """燃油费率表"""
    rate_id = models.AutoField('费率ID', primary_key=True)
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        db_column='provider_id',
        verbose_name='服务商'
    )
    rate_value = models.DecimalField('费率值', max_digits=10, decimal_places=4)
    effective_date = models.DateField('生效日期')
    expiration_date = models.DateField('失效日期')
    description = models.TextField('描述', null=True, blank=True)
    status = models.BooleanField('状态', default=True)

    class Meta:
        db_table = 'fuel_rates'
        verbose_name = '燃油费率'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['provider'], name='fuel_rates_provider_idx'),
            models.Index(fields=['effective_date', 'expiration_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.provider.name} ({self.rate_value})"


class FuelRateHistory(BaseModel):
    """
    燃油费率历史记录
    """
    CHANGE_TYPES = [
        ('MANUAL', '手动修改'),
        ('SYSTEM', '系统调整'),
    ]

    fuel_rate = models.ForeignKey(
        FuelRate,
        on_delete=models.CASCADE,
        verbose_name='燃油费率',
        to_field='rate_id',
        db_column='fuel_rate_id',
        related_name='histories'
    )
    old_rate = models.DecimalField(
        '原费率',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    new_rate = models.DecimalField(
        '新费率',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    change_type = models.CharField('变更类型', max_length=10, choices=CHANGE_TYPES)
    change_reason = models.TextField('变更原因', null=True, blank=True)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='操作人',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = '费率历史'
        verbose_name_plural = verbose_name
        db_table = 'fuel_rate_history'
        ordering = ['-created_at']

    def __str__(self):
        """
        字符串表示
        """
        return f"{self.fuel_rate} (从{self.old_rate}%变更为{self.new_rate}%)"
