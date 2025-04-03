from rest_framework import serializers
from .models import CalculationRequest, CalculationDetail, BatchCalculationTask
from django.utils import timezone
from decimal import Decimal
from apps.core.exceptions import InvalidParameterException
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CalculationDetailSerializer(serializers.ModelSerializer):
    """
    计算明细序列化器
    """
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, required=False)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, required=False)
    zone_info = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = CalculationDetail
        fields = [
            'fee_type', 'fee_type_display', 'fee_name', 'amount',
            'rate', 'weight_used', 'unit_price', 'calculation_formula',
            'zone_info'
        ]
        read_only_fields = ['amount', 'calculation_formula']


class CalculationRequestSerializer(serializers.Serializer):
    product_id = serializers.CharField(required=True)
    weight = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    length = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    width = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    height = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    from_postal = serializers.CharField(max_length=10, required=True)
    to_postal = serializers.CharField(max_length=10, required=True)
    quantity = serializers.IntegerField(required=False, default=1)
    declared_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal('0.00'))

    def validate_weight(self, value):
        if value <= 0:
            raise InvalidParameterException('重量必须大于0')
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise InvalidParameterException('数量必须大于0')
        return value

    def validate_declared_value(self, value):
        if value < 0:
            raise InvalidParameterException('申报价值不能为负数')
        return value


class SingleCalculationRequestSerializer(serializers.Serializer):
    """单次运费计算请求序列化器"""
    product_id = serializers.CharField(required=True, help_text='产品ID')
    from_postal = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text='起始邮编')
    to_postal = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text='目的邮编')
    weight = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, help_text='重量(kg)')
    quantity = serializers.IntegerField(default=1, min_value=1, help_text='数量')
    declared_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, help_text='申报价值')
    length = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, help_text='长度(cm)')
    width = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, help_text='宽度(cm)')
    height = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, help_text='高度(cm)')
    is_residential = serializers.BooleanField(default=False, required=False, help_text='是否住宅地址')
    
    def validate_weight(self, value):
        """验证重量"""
        try:
            # 检查重量是否为负数或零
            if value <= 0:
                raise InvalidParameterException('重量必须大于0')
            
            # 检查重量是否超过最大限制
            if value > settings.MAX_WEIGHT_LIMIT:
                raise InvalidParameterException(f'重量不能超过 {settings.MAX_WEIGHT_LIMIT}')
            
            # 检查小数位数
            decimal_places = abs(value.as_tuple().exponent)
            if decimal_places > 2:
                raise InvalidParameterException('重量最多支持2位小数')
            
            return value
            
        except InvalidParameterException:
            raise
        except Exception as e:
            logger.error(f'重量验证失败: {str(e)}')
            raise InvalidParameterException('重量格式错误')


class BatchCalculationRequestSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=CalculationRequestSerializer(),
        min_length=1,
        max_length=settings.MAX_BATCH_RECORDS,
        allow_empty=False,
        error_messages={
            'empty': '没有要计算的记录',
            'min_length': '至少需要一条记录',
            'max_length': f'记录数不能超过{settings.MAX_BATCH_RECORDS}条'
        }
    )

    def validate(self, attrs):
        """验证数据"""
        items = attrs.get('items', [])
        
        # 检查是否为空
        if not items:
            raise serializers.ValidationError({
                'items': '没有要计算的记录'
            })
            
        # 检查记录数量
        if len(items) > settings.MAX_BATCH_RECORDS:
            raise serializers.ValidationError({
                'items': f'记录数不能超过{settings.MAX_BATCH_RECORDS}条'
            })
            
        # 验证每条记录
        for i, item in enumerate(items):
            try:
                serializer = CalculationRequestSerializer(data=item)
                serializer.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    f'items[{i}]': e.detail
                })
                
        return attrs


class BatchCalculationTaskSerializer(serializers.ModelSerializer):
    """
    批量计算任务序列化器
    """
    provider_name = serializers.CharField(source='product.provider.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BatchCalculationTask
        fields = [
            'id', 'task_id', 'status', 'status_display',
            'provider_name', 'product_name',
            'total_records', 'processed_records',
            'success_records', 'error_records',
            'progress', 'result_file', 'error_file',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'task_id', 'status', 'status_display',
            'provider_name', 'product_name',
            'total_records', 'processed_records',
            'success_records', 'error_records',
            'progress', 'result_file', 'error_file',
            'created_at', 'updated_at'
        ]


class BatchCalculationResultSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='product.provider.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BatchCalculationTask
        fields = [
            'task_id', 'status', 'status_display',
            'provider_name', 'product_name',
            'total_records', 'processed_records',
            'success_records', 'error_records',
            'progress'
        ]


class SingleCalculationSerializer(serializers.Serializer):
    """单个运费计算序列化器"""
    product_id = serializers.CharField(required=True)
    weight = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    from_postal = serializers.CharField(max_length=10, required=True)
    to_postal = serializers.CharField(max_length=10, required=True)
    length = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    width = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    height = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_weight(self, value):
        """验证重量"""
        if value <= 0:
            raise InvalidParameterException("重量必须大于0")
        return value


class BatchCalculationSerializer(serializers.Serializer):
    """批量运费计算序列化器"""
    items = serializers.ListField(
        child=SingleCalculationSerializer(),
        min_length=1,
        required=True
    )

    def validate_items(self, value):
        """验证批量计算项目"""
        if not value:
            raise InvalidParameterException("请提供至少一个计算项目")
        if len(value) > 100:
            raise InvalidParameterException("批量计算项目不能超过100个")
        return value


class ProductComparisonSerializer(serializers.Serializer):
    """产品比较序列化器"""
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        required=True
    )
    weight = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    from_postal = serializers.CharField(max_length=10, required=True)
    to_postal = serializers.CharField(max_length=10, required=True)
    length = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    width = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    height = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_product_ids(self, value):
        """验证产品ID列表"""
        if not value:
            raise InvalidParameterException("请提供至少一个产品ID")
        if len(value) > 10:
            raise InvalidParameterException("产品比较数量不能超过10个")
        return value

    def validate_weight(self, value):
        """验证重量"""
        if value <= 0:
            raise InvalidParameterException("重量必须大于0")
        return value


class ProductComparisonRequestSerializer(serializers.Serializer):
    """产品比较请求序列化器"""
    products = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=10,
        required=True,
        error_messages={
            'min_length': '至少需要一个产品',
            'max_length': '最多支持10个产品比较'
        }
    )
    weight = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    from_postal = serializers.CharField(required=True)
    to_postal = serializers.CharField(required=True)
    length = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    width = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    height = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    quantity = serializers.IntegerField(default=1, min_value=1)
    declared_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_weight(self, value):
        """验证重量"""
        if value <= 0:
            raise InvalidParameterException('重量必须大于0')
        if value > settings.MAX_WEIGHT_LIMIT:
            raise InvalidParameterException(f'重量不能超过 {settings.MAX_WEIGHT_LIMIT}kg')
        return value

    def validate_products(self, value):
        """验证产品列表"""
        if not value:
            raise InvalidParameterException('请提供至少一个产品')
        if len(value) > 10:
            raise InvalidParameterException('最多支持10个产品比较')
        if len(set(value)) != len(value):
            raise InvalidParameterException('产品不能重复')
        return value


class CalculationRequestModelSerializer(serializers.ModelSerializer):
    """计算请求模型序列化器"""
    class Meta:
        model = CalculationRequest
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at') 