from rest_framework import serializers
from .models import ServiceProvider, SystemConfig, Notification, NotificationSettings
from django.core.cache import cache
from django_celery_results.models import TaskResult
from django.contrib.auth import get_user_model


class ServiceProviderSerializer(serializers.ModelSerializer):
    """
    服务商序列化器
    """
    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'name', 'code', 'contact_person', 'contact_phone',
            'contact_email', 'status', 'config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        """
        自定义数据展示
        """
        data = super().to_representation(instance)
        # 隐藏敏感信息
        data.pop('api_key', None)
        data.pop('api_secret', None)
        return data


class SystemConfigSerializer(serializers.ModelSerializer):
    """
    系统配置序列化器
    """
    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'description', 'is_public', 
            'config_type', 'validation_rules', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """
        验证配置数据
        """
        # 如果更新操作，合并现有的验证规则
        if self.instance:
            validation_rules = data.get('validation_rules', self.instance.validation_rules)
        else:
            validation_rules = data.get('validation_rules')

        if validation_rules and 'value' in data:
            value = data['value']
            # 创建临时实例进行验证
            temp_instance = SystemConfig(
                value=value,
                validation_rules=validation_rules
            )
            try:
                temp_instance.clean()
            except serializers.ValidationError as e:
                raise serializers.ValidationError({'value': e.detail})

        return data

    def to_representation(self, instance):
        """
        自定义数据展示
        """
        data = super().to_representation(instance)
        if not instance.is_public and not self.context['request'].user.is_staff:
            # 非公开配置只返回键名和描述
            data.pop('value', None)
            data.pop('validation_rules', None)
        return data


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class ConfigBatchUpdateSerializer(serializers.Serializer):
    """批量更新配置序列化器"""
    configs = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )

    def save(self):
        configs = []
        for config_data in self.validated_data['configs']:
            config, _ = SystemConfig.objects.update_or_create(
                key=config_data['key'],
                defaults=config_data
            )
            configs.append(config)
        return configs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'content', 'link', 'read', 'module', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'max_count', 'expiration_days', 'sound_enabled',
            'desktop_notification', 'group_by_module', 'auto_cleanup'
        ]

    def validate_max_count(self, value):
        if value < 10 or value > 100:
            raise serializers.ValidationError('通知数量限制必须在10-100之间')
        return value

    def validate_expiration_days(self, value):
        if value < 1 or value > 30:
            raise serializers.ValidationError('通知保留天数必须在1-30之间')
        return value


class TaskHistorySerializer(serializers.ModelSerializer):
    """任务历史记录序列化器"""
    class Meta:
        model = TaskResult
        fields = ['task_id', 'status', 'result', 'date_done', 'traceback']


class PerformanceStatsSerializer(serializers.Serializer):
    """性能统计数据序列化器"""
    cpu_percent = serializers.FloatField()
    memory_percent = serializers.FloatField()
    disk_percent = serializers.FloatField()
    process_count = serializers.IntegerField()
    thread_count = serializers.IntegerField()
    network_io = serializers.DictField()
    disk_io = serializers.DictField()


class MetricsSerializer(serializers.Serializer):
    """系统指标序列化器"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    cache_hit_rate = serializers.FloatField()


class HealthCheckSerializer(serializers.Serializer):
    """健康检查序列化器"""
    status = serializers.CharField()
    database = serializers.BooleanField()
    cache = serializers.BooleanField()
    celery = serializers.BooleanField()
    uptime = serializers.IntegerField()


class APIErrorSerializer(serializers.Serializer):
    """API错误序列化器"""
    error_code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField() 