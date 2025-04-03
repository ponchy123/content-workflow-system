from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel, ServiceProvider, BaseCalculation
from apps.products.models import Product
from apps.postal_codes.models import ZipZone
from apps.fuel_rates.models import FuelRate
from decimal import Decimal
from apps.core.decorators import db_connection_retry
import os
import logging
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from apps.core.config import get_setting

logger = logging.getLogger(__name__)

def validate_dimensions(value):
    """验证尺寸是否在合理范围内"""
    if value <= 0 or value > 999999.99:
        raise ValidationError('尺寸必须大于0且小于999999.99')

def validate_weight(value):
    """验证重量是否在合理范围内"""
    if value <= 0 or value > 999999.99:
        raise ValidationError('重量必须大于0且小于999999.99')

class CalculationRequest(BaseModel):
    """
    计算请求记录
    """
    REQUEST_TYPES = [
        ('SINGLE', '单件计算'),
        ('BATCH', '批量计算'),
    ]

    request_type = models.CharField('请求类型', max_length=20, choices=REQUEST_TYPES)
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='服务商'
    )
    zone = models.CharField('分区', max_length=10)
    dimensional_weight = models.DecimalField(
        '体积重',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='根据尺寸计算的体积重'
    )
    chargeable_weight = models.DecimalField(
        '计费重量',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='实际计费重量'
    )
    original_filename = models.CharField(
        '原始文件名',
        max_length=255,
        null=True,
        blank=True,
        help_text='批量计算时的上传文件名'
    )

    class Meta:
        verbose_name = '计算请求'
        verbose_name_plural = verbose_name
        db_table = 'calculation_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_type', 'created_at']),
            models.Index(fields=['provider', 'zone']),
        ]

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.request_id}"

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def save(self, *args, **kwargs):
        """保存前的处理"""
        if not self.pk:  # 只在创建时执行
            # 计算体积重
            if all([self.length, self.width, self.height]):
                dim_factor = self.provider.dim_factor if self.provider else get_setting('DEFAULT_DIM_FACTOR', 139)
                self.dimensional_weight = (self.length * self.width * self.height) / dim_factor
                
                # 设置计费重量（取体积重和实际重量的较大值）
                self.chargeable_weight = max(self.weight, self.dimensional_weight)
        
        super().save(*args, **kwargs)


class CalculationDetail(BaseModel):
    """
    计算明细
    """
    FEE_TYPES = [
        ('BASE', '基础运费'),
        ('FUEL', '燃油费'),
        ('REMOTE', '偏远费'),
        ('OTHER', '其他费用'),
    ]

    calculation = models.ForeignKey(
        'Calculation',  # 使用字符串引用解决循环引用问题
        on_delete=models.CASCADE,
        verbose_name='计算结果',
        related_name='details'
    )
    fee_type = models.CharField('费用类型', max_length=50, choices=FEE_TYPES)
    fee_name = models.CharField('费用名称', max_length=50)
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    weight_used = models.DecimalField(
        '计费重量',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    rate = models.DecimalField(
        '费率',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    unit_price = models.DecimalField(
        '单价',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    zone_info = models.CharField(
        '区域信息',
        max_length=100,
        null=True,
        blank=True
    )
    calculation_formula = models.TextField(
        '计算公式',
        null=True,
        blank=True,
        help_text='描述费用的计算过程'
    )

    class Meta:
        verbose_name = '计算明细'
        verbose_name_plural = verbose_name
        db_table = 'calculation_details'
        ordering = ['calculation', 'fee_type']

    def __str__(self):
        return f"{self.calculation.request_id} - {self.get_fee_type_display()}"


class BatchCalculationTask(BaseModel):
    """批量计算任务"""
    TASK_STATUS = [
        ('PENDING', '等待处理'),
        ('PROCESSING', '处理中'),
        ('COMPLETED', '已完成'),
        ('FAILED', '处理失败'),
        ('CANCELLED', '已取消'),
    ]
    
    PRIORITY_LEVELS = [
        (0, '低'),
        (1, '中'),
        (2, '高'),
    ]

    task_id = models.CharField('任务ID', max_length=36, unique=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name='产品'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='用户'
    )
    original_filename = models.CharField('原始文件名', max_length=255, null=True, blank=True)
    original_file = models.CharField('原始文件路径', max_length=255)
    total_records = models.IntegerField('总记录数', default=0)
    processed_records = models.IntegerField('已处理记录数', default=0)
    success_records = models.IntegerField('成功记录数', default=0)
    error_records = models.IntegerField('错误记录数', default=0)
    status = models.CharField('状态', max_length=20, choices=TASK_STATUS, default='PENDING')
    error_file = models.CharField('错误记录文件', max_length=255, null=True, blank=True)
    result_file = models.CharField('结果文件', max_length=255, null=True, blank=True)
    current_chunk = models.IntegerField('当前处理块', default=0)
    total_chunks = models.IntegerField('总块数', default=0)
    priority = models.IntegerField('优先级', choices=PRIORITY_LEVELS, default=1)
    retry_count = models.IntegerField('重试次数', default=0)
    max_retries = models.IntegerField('最大重试次数', default=3)
    last_error = models.TextField('最后错误信息', null=True, blank=True)
    cancelled_at = models.DateTimeField('取消时间', null=True, blank=True)
    expires_at = models.DateTimeField('过期时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    class Meta:
        verbose_name = '批量计算任务'
        verbose_name_plural = verbose_name
        db_table = 'batch_calculation_tasks'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.task_id} - {self.get_status_display()}"

    @property
    def progress(self) -> int:
        """计算进度百分比"""
        if self.total_records == 0:
            return 0
        return int((self.processed_records / self.total_records) * 100)

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return (
            self.status == 'FAILED' and 
            self.retry_count < self.max_retries
        )

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def mark_cancelled(self):
        """标记任务为已取消"""
        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.save(update_fields=['status', 'cancelled_at'])

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def save(self, *args, **kwargs):
        """保存时确保所有必要字段都有值"""
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        
        if not self.status:
            self.status = 'PENDING'
        
        if not self.total_records:
            self.total_records = 0
        
        if not self.processed_records:
            self.processed_records = 0
        
        if not self.success_records:
            self.success_records = 0
        
        if not self.error_records:
            self.error_records = 0
        
        # 设置过期时间
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        
        # 如果任务完成，设置完成时间
        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def clean_files(self):
        """清理任务相关文件"""
        files_to_clean = [
            self.original_file,
            self.error_file,
            self.result_file
        ]
        
        for file_path in files_to_clean:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"清理文件失败: {file_path}, 错误: {str(e)}")


class Calculation(BaseCalculation):
    """
    运费计算记录
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='calculations',
        verbose_name='产品',
        null=True,
        blank=True
    )
    zone = models.CharField('分区', max_length=10, null=True, blank=True)
    remote_level = models.CharField('偏远等级', max_length=10, null=True, blank=True)
    fuel_fee = models.DecimalField(
        '燃油附加费',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    currency = models.CharField(
        '货币',
        max_length=3,
        default=''
    )
    weight_unit = models.CharField(
        '重量单位',
        max_length=5,
        default=''
    )
    dimension_unit = models.CharField(
        '尺寸单位',
        max_length=5,
        default=''
    )

    class Meta:
        verbose_name = '运费计算'
        verbose_name_plural = verbose_name
        db_table = 'calculations'
        ordering = ['-created_at']

    def __str__(self):
        product_info = f" - {self.product.product_id}" if self.product else ""
        return f"{self.request_id}{product_info}"

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
            
        # 计算体积重和计费重量
        if not self.volume_weight and hasattr(self, 'calculate_volume_weight'):
            self.volume_weight = self.calculate_volume_weight()
        if not self.chargeable_weight and hasattr(self, 'calculate_chargeable_weight'):
            self.chargeable_weight = self.calculate_chargeable_weight()
            
        super().save(*args, **kwargs)

class FreightOrder(BaseModel):
    """运费订单表"""
    order_id = models.AutoField('订单ID', primary_key=True)
    order_no = models.CharField('订单号', max_length=32, unique=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='user_id',
        verbose_name='用户'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        db_column='product_id',
        to_field='product_id',
        verbose_name='产品'
    )
    from_postal_code = models.CharField('发件邮编', max_length=20)
    to_postal_code = models.CharField('收件邮编', max_length=20)
    weight = models.DecimalField('重量', max_digits=10, decimal_places=3)
    volume_weight = models.DecimalField('体积重', max_digits=10, decimal_places=3, null=True, blank=True)
    charge_weight = models.DecimalField('计费重量', max_digits=10, decimal_places=3)
    zone = models.CharField('分区', max_length=10)
    base_fee = models.DecimalField('基础运费', max_digits=10, decimal_places=2)
    fuel_fee = models.DecimalField('燃油费', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remote_fee = models.DecimalField('偏远费', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_fee = models.DecimalField('总费用', max_digits=10, decimal_places=2)
    currency = models.CharField('货币单位', max_length=3)
    status = models.BooleanField('状态', default=True)

    class Meta:
        db_table = 'freight_orders'
        verbose_name = '运费订单'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['order_no']),
            models.Index(fields=['user']),
            models.Index(fields=['product']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.order_no} - {self.product.product_id}"

class FreightOrderDetail(BaseModel):
    """运费订单明细表"""
    detail_id = models.AutoField('明细ID', primary_key=True)
    order = models.ForeignKey(
        'FreightOrder',
        on_delete=models.CASCADE,
        db_column='order_id',
        to_field='order_id',
        verbose_name='订单'
    )
    fee_type = models.CharField('费用类型', max_length=50)
    fee_name = models.CharField('费用名称', max_length=100)
    fee_amount = models.DecimalField('费用金额', max_digits=10, decimal_places=2)
    currency = models.CharField('货币单位', max_length=3)
    description = models.TextField('描述', null=True, blank=True)
    status = models.BooleanField('状态', default=True)

    class Meta:
        db_table = 'freight_order_details'
        verbose_name = '运费订单明细'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['order', 'fee_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.order.order_no} - {self.fee_name}" 