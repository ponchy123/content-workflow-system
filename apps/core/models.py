from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
from .decorators import db_connection_retry
import json
import uuid

# 移除全局 get_user_model() 调用，在需要时延迟导入
# User = get_user_model()


class BaseModel(models.Model):
    """基础模型"""
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.CharField('创建人', max_length=100, null=True, blank=True)
    updated_by = models.CharField('更新人', max_length=100, null=True, blank=True)
    is_deleted = models.BooleanField('是否删除', default=False)

    class Meta:
        abstract = True


class ServiceProvider(BaseModel):
    """
    服务商模型
    """
    name = models.CharField('服务商名称', max_length=100)
    code = models.CharField('服务商代码', max_length=50, unique=True)
    contact_person = models.CharField('联系人', max_length=50, null=True, blank=True)
    contact_phone = models.CharField('联系电话', max_length=20, null=True, blank=True)
    contact_email = models.EmailField('联系邮箱', null=True, blank=True)
    status = models.BooleanField('状态', default=True)
    api_key = models.CharField('API密钥', max_length=100, null=True, blank=True)
    api_secret = models.CharField('API密钥', max_length=100, null=True, blank=True)
    config = models.JSONField('配置信息', default=dict, blank=True)

    class Meta:
        verbose_name = '服务商'
        verbose_name_plural = verbose_name
        db_table = 'core_service_provider'

    def __str__(self):
        return self.name


class SystemConfig(BaseModel):
    """
    系统配置模型
    """
    CONFIG_TYPES = (
        ('basic', _('基础设置')),
        ('calculation', _('计算设置')),
        ('notification', _('通知设置')),
        ('api', _('API设置')),
    )

    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.JSONField('配置值')
    description = models.TextField('配置说明', null=True, blank=True)
    is_public = models.BooleanField('是否公开', default=False)
    config_type = models.CharField('配置类型', max_length=20, choices=CONFIG_TYPES, default='basic')
    validation_rules = models.JSONField('验证规则', null=True, blank=True)
    
    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name
        db_table = 'core_system_config'

    def __str__(self):
        return self.key

    def clean(self):
        """验证配置值"""
        if self.validation_rules:
            try:
                self._validate_config_value()
            except ValidationError as e:
                raise ValidationError({'value': e.message})

    def _validate_config_value(self):
        """根据验证规则验证配置值"""
        rules = self.validation_rules
        value = self.value

        if rules.get('type'):
            if rules['type'] == 'number':
                try:
                    float(value)
                except (TypeError, ValueError):
                    raise ValidationError(_('值必须是数字类型'))
                
                if 'min' in rules and float(value) < rules['min']:
                    raise ValidationError(_('值不能小于 %(min)s') % {'min': rules['min']})
                if 'max' in rules and float(value) > rules['max']:
                    raise ValidationError(_('值不能大于 %(max)s') % {'max': rules['max']})
                    
            elif rules['type'] == 'boolean':
                if not isinstance(value, bool):
                    raise ValidationError(_('值必须是布尔类型'))
                    
            elif rules['type'] == 'string':
                if not isinstance(value, str):
                    raise ValidationError(_('值必须是字符串类型'))
                if 'max_length' in rules and len(value) > rules['max_length']:
                    raise ValidationError(_('字符串长度不能超过 %(max_length)s') % {'max_length': rules['max_length']})
                if 'pattern' in rules:
                    import re
                    if not re.match(rules['pattern'], value):
                        raise ValidationError(_('值格式不正确'))
                        
            elif rules['type'] == 'email':
                from django.core.validators import validate_email
                try:
                    validate_email(value)
                except ValidationError:
                    raise ValidationError(_('邮箱格式不正确'))
                    
            elif rules['type'] == 'array':
                if not isinstance(value, list):
                    raise ValidationError(_('值必须是数组类型'))
                if 'max_items' in rules and len(value) > rules['max_items']:
                    raise ValidationError(_('数组长度不能超过 %(max_items)s') % {'max_items': rules['max_items']})

    @classmethod
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_config(cls, key, default=None):
        """获取配置值，优先从缓存获取"""
        from django.core.cache import cache
        cache_key = f'system_config_{key}'
        
        # 尝试从缓存获取
        value = cache.get(cache_key)
        if value is not None:
            return value
            
        try:
            config = cls.objects.get(key=key)
            value = config.value
            # 设置缓存
            cache.set(cache_key, value, timeout=3600)  # 缓存1小时
            return value
        except cls.DoesNotExist:
            return default

    @classmethod
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def set_config(cls, key, value, config_type='basic', description=None, is_public=False, validation_rules=None):
        """设置配置值"""
        config, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'config_type': config_type,
                'description': description,
                'is_public': is_public,
                'validation_rules': validation_rules
            }
        )
        
        # 更新缓存
        from django.core.cache import cache
        cache_key = f'system_config_{key}'
        cache.set(cache_key, value, timeout=3600)  # 缓存1小时
        
        return config

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # 更新缓存
        from django.core.cache import cache
        cache_key = f'system_config_{self.key}'
        cache.set(cache_key, self.value, timeout=3600)  # 缓存1小时


class AuditLog(models.Model):
    """审计日志模型"""
    ACTION_TYPES = (
        ('CREATE', _('创建')),
        ('UPDATE', _('更新')),
        ('DELETE', _('删除')),
        ('LOGIN', _('登录')),
        ('LOGOUT', _('登出')),
        ('EXPORT', _('导出')),
        ('IMPORT', _('导入')),
        ('OTHER', _('其他')),
    )

    RISK_LEVELS = (
        ('LOW', _('低')),
        ('MEDIUM', _('中')),
        ('HIGH', _('高')),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_('操作用户'))
    action = models.CharField(max_length=50, choices=ACTION_TYPES, verbose_name=_('操作类型'))
    content_type = models.CharField(max_length=100, verbose_name=_('内容类型'))
    object_id = models.CharField(max_length=50, verbose_name=_('对象ID'))
    object_repr = models.CharField(max_length=200, verbose_name=_('对象描述'))
    action_time = models.DateTimeField(auto_now_add=True, verbose_name=_('操作时间'))
    ip_addr = models.GenericIPAddressField(verbose_name=_('IP地址'))
    user_agent = models.CharField(max_length=200, verbose_name=_('用户代理'))
    change_message = models.JSONField(verbose_name=_('变更信息'))
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='LOW', verbose_name=_('风险等级'))
    module = models.CharField(max_length=50, verbose_name=_('功能模块'), null=True, blank=True)
    status = models.CharField(max_length=20, default='SUCCESS', verbose_name=_('操作状态'))
    error_message = models.TextField(null=True, blank=True, verbose_name=_('错误信息'))
    duration = models.FloatField(default=0.0, verbose_name=_('执行时长(ms)'))

    class Meta:
        verbose_name = _('审计日志')
        verbose_name_plural = verbose_name
        ordering = ['action_time']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.action_time}"

    @classmethod
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def log_action(cls, user, action, content_type, object_id, object_repr, change_message, 
                  ip_addr=None, user_agent=None, risk_level='LOW', module=None, 
                  status='SUCCESS', error_message=None, duration=0.0):
        """
        记录审计日志的便捷方法
        
        Args:
            user: 用户对象，可以是User实例或None
            action: 操作类型
            content_type: 内容类型
            object_id: 对象ID
            object_repr: 对象描述
            change_message: 变更信息
            ip_addr: IP地址
            user_agent: 用户代理
            risk_level: 风险等级
            module: 功能模块
            status: 操作状态
            error_message: 错误信息
            duration: 执行时长
        """
        return cls.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            change_message=change_message,
            ip_addr=ip_addr,
            user_agent=user_agent,
            risk_level=risk_level,
            module=module,
            status=status,
            error_message=error_message,
            duration=duration
        )

    def get_risk_level_display_color(self):
        """获取风险等级显示颜色"""
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red'
        }
        return colors.get(self.risk_level, 'gray')

    def get_formatted_duration(self):
        """获取格式化的执行时长"""
        if self.duration < 1000:
            return f"{self.duration:.2f}ms"
        return f"{(self.duration/1000):.2f}s"


class Report(BaseModel):
    """报表模型"""
    REPORT_TYPES = (
        ('order', _('订单报表')),
        ('product', _('产品报表')),
        ('finance', _('财务报表')),
        ('operation', _('运营报表')),
    )
    
    name = models.CharField(max_length=100, verbose_name=_('报表名称'))
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name=_('报表类型'))
    query_params = models.JSONField(verbose_name=_('查询参数'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_('创建人'))
    is_scheduled = models.BooleanField(default=False, verbose_name=_('是否定时'))
    schedule_config = models.JSONField(null=True, blank=True, verbose_name=_('定时配置'))
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('报表')
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def __str__(self):
        return self.name


class AccessLog(BaseModel):
    """访问日志"""
    url = models.CharField('访问URL', max_length=255)
    method = models.CharField('请求方法', max_length=10)
    ip_address = models.CharField('IP地址', max_length=50, default='0.0.0.0')
    user_agent = models.CharField('用户代理', max_length=255, default='Unknown')
    status_code = models.IntegerField('状态码')
    response_time = models.FloatField('响应时间(ms)')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    cache_hit = models.BooleanField('缓存命中', default=False)
    remarks = models.TextField('备注', null=True, blank=True)
    module = models.CharField('模块', max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'access_logs'
        verbose_name = '访问日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.product} - {self.url} - {self.created_at}"


class BaseCalculation(BaseModel):
    """基础计算模型，用于统一计算相关的字段定义"""
    request_id = models.CharField('请求ID', max_length=32, unique=True)
    weight = models.DecimalField(
        '实重',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    length = models.DecimalField(
        '长',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,
        blank=True
    )
    width = models.DecimalField(
        '宽',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,
        blank=True
    )
    height = models.DecimalField(
        '高',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,
        blank=True
    )
    from_postal = models.CharField('起始邮编', max_length=10)
    to_postal = models.CharField('目的邮编', max_length=10)
    base_fee = models.DecimalField(
        '基础费用',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    total_fee = models.DecimalField(
        '总费用',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    volume_weight = models.DecimalField(
        '体积重',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    chargeable_weight = models.DecimalField(
        '计费重量',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    status = models.CharField('状态', max_length=20, default='SUCCESS')
    error_message = models.TextField('错误信息', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人'
    )

    class Meta:
        abstract = True

    def calculate_volume_weight(self):
        """计算体积重"""
        if all([self.length, self.width, self.height]):
            volume_weight_coefficient = self.product.dim_factor
            self.volume_weight = (
                self.length * self.width * self.height / volume_weight_coefficient
            ).quantize(Decimal('0.01'))
            return self.volume_weight
        return None

    def calculate_chargeable_weight(self):
        """计算计费重量"""
        if self.volume_weight:
            self.chargeable_weight = max(
                self.weight,
                self.volume_weight
            ).quantize(Decimal('0.01'))
        else:
            self.chargeable_weight = self.weight.quantize(Decimal('0.01'))
        return self.chargeable_weight


class ShardedBaseModel(BaseModel):
    """分表基类"""
    shard_key = models.DateField('分表键', db_index=True)
    
    class Meta:
        abstract = True
    
    @classmethod
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_table_name(cls, date):
        """获取分表名称"""
        return f"{cls._meta.db_table}_{date.strftime('%Y%m')}"
    
    @classmethod
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_table_for_date(cls, date):
        """获取指定日期的表"""
        table_name = cls.get_table_name(date)
        return type(f"{cls.__name__}_{date.strftime('%Y%m')}", (cls,), {
            '__module__': cls.__module__,
            'Meta': type('Meta', (), {
                'db_table': table_name,
                'managed': False  # 让Django不管理这个表的创建和删除
            })
        })
    
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def save(self, *args, **kwargs):
        if not self.shard_key:
            self.shard_key = timezone.now().date()
        super().save(*args, **kwargs)


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('system', '系统通知'),
        ('business', '业务通知'),
        ('warning', '警告通知'),
        ('error', '错误通知'),
    )

    id = models.CharField(max_length=32, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    link = models.URLField(null=True, blank=True)
    read = models.BooleanField(default=False)
    module = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']


class NotificationSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_settings')
    max_count = models.IntegerField(default=50)
    expiration_days = models.IntegerField(default=7)
    sound_enabled = models.BooleanField(default=True)
    desktop_notification = models.BooleanField(default=False)
    group_by_module = models.BooleanField(default=False)
    auto_cleanup = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'notification settings'
        verbose_name_plural = 'notification settings'


class RequestLog(BaseModel):
    """请求日志"""
    request_id = models.CharField('请求ID', max_length=50, db_index=True)
    url = models.CharField('URL', max_length=255)
    method = models.CharField('请求方法', max_length=10)
    headers = models.JSONField('请求头', default=dict)
    params = models.JSONField('请求参数', default=dict, null=True, blank=True)
    body = models.TextField('请求体', null=True, blank=True)
    ip = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.CharField('User Agent', max_length=255, null=True, blank=True)
    status_code = models.IntegerField('状态码', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='用户', on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.FloatField('请求耗时(秒)', null=True, blank=True)
    
    class Meta:
        verbose_name = '请求日志'
        verbose_name_plural = verbose_name
        db_table = 'core_request_log'

    def __str__(self):
        return f"{self.request_id} - {self.url[:30]}{'...' if len(self.url) > 30 else ''}"


class ResponseLog(BaseModel):
    """响应日志模型"""
    request = models.OneToOneField(RequestLog, on_delete=models.CASCADE, related_name='response', verbose_name='请求')
    status_code = models.IntegerField('状态码', db_index=True)
    headers = models.JSONField('响应头', default=dict)
    body = models.JSONField('响应体', null=True, blank=True)
    duration = models.FloatField('响应时间(ms)', db_index=True)
    error_message = models.TextField('错误信息', null=True, blank=True)
    cache_hit = models.BooleanField('缓存命中', default=False)

    class Meta:
        verbose_name = '响应日志'
        verbose_name_plural = verbose_name
        db_table = 'core_response_log'

    def __str__(self):
        return f"{self.request.method} {self.request.path} - {self.status_code}"


class SystemLog(BaseModel):
    """系统日志模型"""
    LOG_LEVELS = (
        ('DEBUG', _('调试')),
        ('INFO', _('信息')),
        ('WARNING', _('警告')),
        ('ERROR', _('错误')),
        ('CRITICAL', _('严重')),
    )
    
    level = models.CharField('日志级别', max_length=10, choices=LOG_LEVELS)
    message = models.TextField('日志消息')
    module = models.CharField('模块', max_length=50, null=True, blank=True)
    trace = models.TextField('堆栈跟踪', null=True, blank=True)
    
    class Meta:
        verbose_name = '系统日志'
        verbose_name_plural = verbose_name
        db_table = 'core_system_log'

    def __str__(self):
        return f"{self.level} - {self.message[:50]}... - {self.created_at}"


class ApiRequestLog(BaseModel):
    """API请求日志"""
    request_id = models.CharField('请求ID', max_length=50, db_index=True)
    endpoint = models.CharField('API端点', max_length=255)
    request_time = models.DateTimeField('请求时间', auto_now_add=True)
    method = models.CharField('请求方法', max_length=10)
    params = models.JSONField('请求参数', null=True, blank=True)
    headers = models.JSONField('请求头', null=True, blank=True)
    response = models.JSONField('响应内容', null=True, blank=True)
    status_code = models.IntegerField('状态码')
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    processing_time = models.FloatField('处理时间(毫秒)')
    
    class Meta:
        verbose_name = 'API请求日志'
        verbose_name_plural = verbose_name
        db_table = 'core_api_request_log'

    def __str__(self):
        return f"{self.endpoint} - {self.status_code} - {self.request_time}"


class TemporaryFile(models.Model):
    """
    临时文件模型
    """
    file = models.FileField('文件', upload_to='temp_files/')
    access_token = models.CharField('访问令牌', max_length=100)
    file_name = models.CharField('文件名', max_length=255)
    file_type = models.CharField('文件类型', max_length=50)
    file_size = models.IntegerField('文件大小')
    expiry_time = models.DateTimeField('过期时间')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = '临时文件'
        verbose_name_plural = verbose_name
        db_table = 'core_temporary_file'

    def __str__(self):
        return self.file_name

    def delete(self, *args, **kwargs):
        # 删除文件
        self.file.delete()
        super().delete(*args, **kwargs)


class TokenBlacklist(models.Model):
    """
    令牌黑名单
    """
    token = models.CharField('Token', max_length=255)
    expiry_time = models.DateTimeField('过期时间')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '令牌黑名单'
        verbose_name_plural = verbose_name
        db_table = 'core_token_blacklist'
        
    def __str__(self):
        return f"{self.token[:10]}... - {self.expiry_time}" 