from rest_framework import serializers
from .models import (
    Product, 
    Surcharge, 
    PeakSeasonSurcharge,
    BaseFee,
)
from apps.core.models import ServiceProvider
from django.utils import timezone


class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = ['id', 'name', 'code', 'contact_person', 'contact_email', 'contact_phone']
        read_only_fields = ['id']


class BaseFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseFee
        fields = '__all__'
        
    def to_representation(self, instance):
        """自定义序列化表示，确保正确处理区域价格和原始数据"""
        ret = super().to_representation(instance)
        
        # 确保zone_prices字段存在且为字典
        if not ret.get('zone_prices'):
            ret['zone_prices'] = {}
            
        # 添加直接映射的区域费用字段，供前端表格直接使用
        zone_prices = ret.get('zone_prices', {})
        if zone_prices and isinstance(zone_prices, dict):
            for zone_key, price in zone_prices.items():
                if zone_key.startswith('zone'):
                    zone_num = zone_key.replace('zone', '')
                    try:
                        ret[f'Zone{zone_num}'] = float(price)
                    except (TypeError, ValueError):
                        ret[f'Zone{zone_num}'] = 0.0
        
        # 如果原始数据存在，优先使用原始数据中的单位信息
        raw_data = ret.get('raw_data', {})
        if raw_data and isinstance(raw_data, dict):
            # 使用原始数据中的单位
            if '单位' in raw_data:
                ret['unit_display'] = raw_data['单位']
            
        return ret


class SurchargeSerializer(serializers.ModelSerializer):
    zone_fees_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Surcharge
        fields = [
            'surcharge_id', 'product', 'surcharge_type', 'sub_type',
            'condition_desc', 'zone_fees', 'zone_fees_data',
            'display_order'
        ]
    
    def get_zone_fees_data(self, obj):
        """将zone_fees JSON字段转换为前端友好格式"""
        result = {}
        if obj.zone_fees:
            for zone_key, fee in obj.zone_fees.items():
                if zone_key.startswith('zone'):
                    # 转换为前端期望的格式，例如：zone1 -> Zone1
                    frontend_key = 'Zone' + zone_key[4:]
                    try:
                        result[frontend_key] = float(fee)
                    except (TypeError, ValueError):
                        result[frontend_key] = 0.0
        return result
    
    def to_representation(self, instance):
        """自定义序列化表示"""
        ret = super().to_representation(instance)
        
        # 确保zone_fees字段存在且为字典
        if not ret.get('zone_fees'):
            ret['zone_fees'] = {}
            
        # 添加直接映射的区域费用字段，供前端表格直接使用
        zone_fees = ret.get('zone_fees', {})
        if zone_fees and isinstance(zone_fees, dict):
            for zone_key, fee in zone_fees.items():
                if zone_key.startswith('zone'):
                    zone_num = zone_key.replace('zone', '')
                    try:
                        ret[f'Zone{zone_num}'] = float(fee)
                    except (TypeError, ValueError):
                        ret[f'Zone{zone_num}'] = 0.0
        
        return ret
    
    def validate(self, data):
        """验证并处理区域费用数据"""
        validated_data = super().validate(data)
        
        # 确保zone_fees是字典类型
        if 'zone_fees' not in validated_data:
            validated_data['zone_fees'] = {}
        elif not isinstance(validated_data['zone_fees'], dict):
            raise serializers.ValidationError({'zone_fees': '区域费用必须是字典格式'})
        
        # 处理区域费用数据
        zone_fees = validated_data['zone_fees']
        processed_zone_fees = {}
        
        # 处理现有的zone_fees数据
        for key, value in zone_fees.items():
            # 确保键的格式正确（zone1, zone2等）
            if key.startswith('zone') or key.startswith('Zone'):
                zone_key = f"zone{key.lower().replace('zone', '')}"
                try:
                    # 尝试转换为数值类型
                    processed_zone_fees[zone_key] = float(value)
                except (TypeError, ValueError):
                    processed_zone_fees[zone_key] = 0.0
        
        # 更新处理后的数据
        validated_data['zone_fees'] = processed_zone_fees
        
        return validated_data


class PeakSeasonSurchargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeakSeasonSurcharge
        fields = [
            'pss_id', 'product', 'surcharge_type',
            'start_date', 'end_date', 'fee_amount'
        ]

    def to_representation(self, instance):
        """自定义序列化表示"""
        ret = super().to_representation(instance)
        # 添加统一的区域费用
        for i in range(1, 9):
            ret[f'Zone{i}'] = float(instance.fee_amount)
        ret['Zone17'] = float(instance.fee_amount)
        return ret


class ProductSerializer(serializers.ModelSerializer):
    provider_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'product_id', 'product_name', 'provider_name', 'dim_factor', 
            'dim_factor_unit', 'effective_date', 'expiration_date', 'country',
            'currency', 'weight_unit', 'dim_unit', 'description', 'status',
            'enabled_start_date', 'enabled_end_date', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'is_deleted'
        ]
    
    def get_provider_name(self, obj):
        return obj.provider_name


class ProductDetailSerializer(serializers.ModelSerializer):
    surcharges = serializers.SerializerMethodField()
    peak_season_surcharges = serializers.SerializerMethodField()
    surcharges_count = serializers.SerializerMethodField()
    peak_season_surcharges_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'product_id', 'product_name', 'provider_name', 'dim_factor', 
            'dim_factor_unit', 'effective_date', 'expiration_date', 'country',
            'currency', 'weight_unit', 'dim_unit', 'description', 'status',
            'enabled_start_date', 'enabled_end_date', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'is_deleted', 'surcharges',
            'peak_season_surcharges', 'surcharges_count',
            'peak_season_surcharges_count'
        ]
    
    def get_surcharges(self, obj):
        surcharges = Surcharge.objects.filter(product=obj)
        serializer = SurchargeSerializer(surcharges, many=True)
        return serializer.data
    
    def get_peak_season_surcharges(self, obj):
        peak_season_surcharges = PeakSeasonSurcharge.objects.filter(product=obj)
        return PeakSeasonSurchargeSerializer(peak_season_surcharges, many=True).data
    
    def get_surcharges_count(self, obj):
        """获取产品下的附加费数量"""
        return Surcharge.objects.filter(product=obj).count()
    
    def get_peak_season_surcharges_count(self, obj):
        """获取产品下的旺季附加费数量"""
        return PeakSeasonSurcharge.objects.filter(product=obj).count()


class ProductZoneRateImportSerializer(serializers.Serializer):
    weight = serializers.DecimalField(max_digits=10, decimal_places=2)
    weight_unit = serializers.CharField(max_length=10)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 动态添加zone字段
        for i in range(1, 20):  # 支持到zone19
            self.fields[f'zone{i}'] = serializers.DecimalField(
                max_digits=10, decimal_places=2, required=False
            )
    
    def to_internal_value(self, data):
        """转换为内部模型需要的格式"""
        validated_data = super().to_internal_value(data)
        
        # 从扁平结构转换为JSON结构
        zone_prices = {}
        
        for key, value in validated_data.items():
            if key.startswith('zone') and value is not None:
                zone_prices[key] = str(value)
        
        # 更新数据结构
        validated_data['zone_prices'] = zone_prices
        
        # 移除已处理的字段
        for key in list(validated_data.keys()):
            if key.startswith('zone'):
                validated_data.pop(key)
        
        return validated_data


class SurchargeImportSerializer(serializers.Serializer):
    surcharge_type = serializers.CharField(max_length=50)
    sub_type = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    condition_desc = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 动态添加所有可能的zone字段
        for i in range(1, 20):  # 支持到zone19
            self.fields[f'zone{i}'] = serializers.DecimalField(
                max_digits=10, decimal_places=2, required=False
            )
    
    def to_internal_value(self, data):
        """转换为内部模型需要的格式"""
        validated_data = super().to_internal_value(data)
        
        # 从扁平结构转换为JSON结构
        zone_fees = {}
        
        for key, value in validated_data.items():
            if key.startswith('zone') and value is not None:
                zone_fees[key] = str(value)
        
        # 更新数据结构
        validated_data['zone_fees'] = zone_fees
        
        # 移除已处理的字段
        for key in list(validated_data.keys()):
            if key.startswith('zone'):
                validated_data.pop(key)
        
        return validated_data


class PeakSeasonSurchargeImportSerializer(serializers.Serializer):
    surcharge_type = serializers.CharField(max_length=50)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    fee_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class BaseFeeImportSerializer(serializers.Serializer):
    weight = serializers.DecimalField(max_digits=10, decimal_places=2)
    weight_unit = serializers.CharField(max_length=2, required=False, default='lb')
    fee_type = serializers.CharField(max_length=10)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 动态添加可能的zone字段
        for i in range(1, 20):  # 支持到zone19
            self.fields[f'zone{i}_price'] = serializers.DecimalField(
                max_digits=10, decimal_places=2, required=False
            )
            self.fields[f'zone{i}_unit_price'] = serializers.DecimalField(
                max_digits=10, decimal_places=2, required=False
            )
    
    def to_internal_value(self, data):
        """转换为内部模型需要的格式"""
        validated_data = super().to_internal_value(data)
        
        # 从扁平结构转换为JSON结构
        zone_prices = {}
        zone_unit_prices = {}
        
        for key, value in validated_data.items():
            if key.endswith('_price') and key.startswith('zone') and value is not None:
                zone_key = key.replace('_price', '')
                zone_prices[zone_key] = str(value)
            elif key.endswith('_unit_price') and key.startswith('zone') and value is not None:
                zone_key = key.replace('_unit_price', '')
                zone_unit_prices[zone_key] = str(value)
        
        # 更新数据结构
        validated_data['zone_prices'] = zone_prices
        validated_data['zone_unit_prices'] = zone_unit_prices
        
        # 移除已处理的字段
        for key in list(validated_data.keys()):
            if (key.endswith('_price') or key.endswith('_unit_price')) and key.startswith('zone'):
                validated_data.pop(key)
        
        return validated_data 