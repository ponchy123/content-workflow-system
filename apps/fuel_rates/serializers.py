from rest_framework import serializers
from .models import FuelRate, FuelRateHistory
from django.core.exceptions import ValidationError
from typing import Dict, Optional, Any
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


class FuelRateSerializer(serializers.ModelSerializer):
    """
    燃油费率序列化器
    """
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    last_history = serializers.SerializerMethodField()

    class Meta:
        model = FuelRate
        fields = [
            'rate_id', 'provider', 'provider_name', 'rate_value', 'effective_date',
            'expiration_date', 'status', 'last_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['rate_id', 'created_at', 'updated_at']

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'old_rate': {'type': 'number', 'format': 'decimal'},
            'new_rate': {'type': 'number', 'format': 'decimal'},
            'change_type': {'type': 'string'},
            'change_time': {'type': 'string', 'format': 'date-time'}
        }
    })
    def get_last_history(self, obj) -> Optional[Dict[str, Any]]:
        """
        获取最后一条历史记录
        """
        # 使用正确的related_name
        history = obj.histories.order_by('-created_at').first()
        if history:
            return {
                'old_rate': history.old_rate,
                'new_rate': history.new_rate,
                'change_type': history.get_change_type_display(),
                'change_time': history.created_at
            }
        return None

    def validate(self, attrs):
        """
        验证数据
        """
        # 检查日期
        if attrs.get('effective_date') and attrs.get('expiration_date'):
            if attrs['effective_date'] >= attrs['expiration_date']:
                raise serializers.ValidationError({'expiration_date': '失效日期必须大于生效日期'})
        
        # 如果是更新操作，合并现有实例的数据
        if self.instance:
            instance_data = {
                'provider': self.instance.provider,
                'rate_value': self.instance.rate_value,
                'effective_date': self.instance.effective_date,
                'expiration_date': self.instance.expiration_date,
                'status': self.instance.status
            }
            instance_data.update(attrs)
            attrs = instance_data
        
        # 调用模型的 clean 方法进行重叠时间段验证
        instance = FuelRate(**attrs)
        if self.instance:
            instance.rate_id = self.instance.rate_id
        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return attrs


class FuelRateHistorySerializer(serializers.ModelSerializer):
    """
    燃油费率历史记录序列化器
    """
    fuel_rate_info = serializers.SerializerMethodField()
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)

    class Meta:
        model = FuelRateHistory
        fields = [
            'id', 'fuel_rate_id', 'fuel_rate_info', 'old_rate', 'new_rate',
            'change_type', 'change_type_display', 'change_reason',
            'operator_id', 'operator_name', 'created_at'
        ]
        read_only_fields = ['created_at']

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'provider': {'type': 'string'},
            'rate_value': {'type': 'string'},
            'effective_date': {'type': 'string', 'format': 'date'}
        }
    })
    def get_fuel_rate_info(self, obj) -> Optional[Dict[str, Any]]:
        """
        获取燃油费率信息
        """
        fuel_rate = FuelRate.objects.filter(rate_id=obj.fuel_rate_id).first()
        if fuel_rate:
            return {
                'provider': fuel_rate.provider.name,
                'rate_value': str(fuel_rate.rate_value),
                'effective_date': fuel_rate.effective_date
            }
        return None
