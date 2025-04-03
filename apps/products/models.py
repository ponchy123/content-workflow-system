from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.utils.functional import cached_property
from simple_history.models import HistoricalRecords
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation
from apps.core.models import BaseModel, ServiceProvider
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.decorators import db_connection_retry
import re
import uuid
import time
import random
import string
import logging
import json
import datetime
import sys

logger = logging.getLogger(__name__)


class Product(BaseModel):
    """产品主表"""
    product_id = models.CharField('产品ID', max_length=12, primary_key=True)
    provider_name = models.CharField('服务商名称', max_length=100)
    product_name = models.CharField('产品名称', max_length=100)
    dim_factor = models.DecimalField('体积重系数', max_digits=10, decimal_places=2)
    dim_factor_unit = models.CharField('体积重系数单位', max_length=10)
    effective_date = models.DateField('生效日期')
    expiration_date = models.DateField('失效日期')
    country = models.CharField('国家', max_length=50)
    currency = models.CharField('货币单位', max_length=3)
    weight_unit = models.CharField('重量单位', max_length=5)
    dim_unit = models.CharField('尺寸单位', max_length=5)
    description = models.TextField('产品描述', null=True, blank=True)
    status = models.BooleanField('状态', default=True)
    enabled_start_date = models.DateField('启用开始日期', null=True, blank=True)
    enabled_end_date = models.DateField('启用结束日期', null=True, blank=True)
    history = HistoricalRecords()
    
    # 添加访问日志关联
    access_log_entries = models.ManyToManyField('core.AccessLog', related_name='log_accessed_products')

    class Meta:
        db_table = 'products'
        verbose_name = '产品'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['effective_date', 'expiration_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.product_name} ({self.product_id})"

    @property
    def provider(self) -> str:
        """获取服务商名称"""
        return self.provider_name
    
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_cached_price(self, weight: Decimal, zone: str, length: Decimal = None, width: Decimal = None, height: Decimal = None) -> Dict[str, Any]:
        """
        获取缓存中的价格，如果缓存中不存在则计算并缓存
        """
        dimensions_key = ""
        if length is not None and width is not None and height is not None:
            dimensions_key = f"_{length}_{width}_{height}"
        
        cache_key = f"product_price_{self.id}_{weight}_{zone}{dimensions_key}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        result = self.calculate_price(weight, zone, length, width, height)
        # 缓存12小时
        cache.set(cache_key, result, 60 * 60 * 12)
        return result
    
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def calculate_price(self, weight: Decimal, zone: str, length: Decimal = None, width: Decimal = None, height: Decimal = None) -> Dict[str, Any]:
        """
        计算指定重量和区域的价格
        """
        from apps.core.utils import find_weight_range_and_calculate
        
        # 参数验证
        if not isinstance(weight, Decimal):
            weight = Decimal(str(weight))
        
        # 查找适用的重量段和计算价格
        try:
            weight_range, base_price = find_weight_range_and_calculate(self, weight, zone)
            if not weight_range:
                return {
                    'success': False,
                    'error': f'No weight range found for weight {weight}',
                }
            
            # 计算附加费
            surcharges = self.calculate_surcharges(zone)
            surcharge_total = sum(item['amount'] for item in surcharges)
            
            total_price = base_price + surcharge_total
            
            return {
                'success': True,
                'product_id': self.id,
                'weight': weight,
                'zone': zone,
                'base_price': base_price,
                'surcharges': surcharges,
                'surcharge_total': surcharge_total,
                'total_price': total_price,
                'currency': self.currency,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def calculate_surcharges(self, zone: str) -> List[Dict[str, Any]]:
        """
        计算适用的附加费
        
        Args:
            zone: 区域
            
        Returns:
            List[Dict[str, Any]]: 附加费列表
        """
        result = []
        now = timezone.now().date()
        
        # 获取适用的附加费
        surcharges = Surcharge.objects.filter(
            product=self,
            is_deleted=False,
            effective_date__lte=now,
            expiration_date__gte=now
        ).order_by('display_order')
        
        for surcharge in surcharges:
            amount = surcharge.calculate_amount(zone)
            if amount > 0:
                result.append({
                    'id': surcharge.id,
                    'name': surcharge.surcharge_type,
                    'code': f"{surcharge.surcharge_type}",
                    'amount': amount,
                    'type': 'FIXED',
                })
        
        # 获取适用的旺季附加费
        peak_season_surcharges = PeakSeasonSurcharge.objects.filter(
            product=self,
            is_deleted=False,
            start_date__lte=now,
            end_date__gte=now
        )
        
        for peak_surcharge in peak_season_surcharges:
            if peak_surcharge.is_applicable():
                result.append({
                    'id': peak_surcharge.id,
                    'name': peak_surcharge.surcharge_type,
                    'code': f"PSS-{peak_surcharge.surcharge_type}",
                    'amount': peak_surcharge.fee_amount,
                    'type': 'FIXED',
                })
        
        return result

    @cached_property
    def current_version(self) -> Dict[str, Any]:
        """获取当前版本的完整信息"""
        return {
            'weight_points': self._get_weight_points_from_base_fees(),
            'surcharges': list(self.surcharge_set.values()),
            'peak_season_surcharges': list(self.peakseasonsurcharge_set.values())
        }

    def _get_weight_points_from_base_fees(self):
        """从基础费用表中获取重量点数据"""
        base_fees = BaseFee.objects.filter(product=self)
        result = []
        
        for fee in base_fees:
            # 创建基本字段
            weight_point = {
                'id': fee.fee_id,
                'product_id': fee.product_id,
                'weight': fee.weight,
                'weight_unit': fee.weight_unit,
                'pricing_type': fee.fee_type,
            }
            
            # 添加所有区域价格
            if fee.zone_prices:
                for zone_key, price in fee.zone_prices.items():
                    if zone_key.startswith('zone'):
                        weight_point[f'{zone_key}_price'] = Decimal(str(price))
                        
                        # 添加对应的单价
                        unit_price = fee.zone_unit_prices.get(zone_key, 0)
                        weight_point[f'{zone_key}_unit_price'] = Decimal(str(unit_price)) if unit_price else Decimal('0')
            
            result.append(weight_point)
            
        return result

    def clear_cache(self) -> None:
        """清除产品相关的所有缓存"""
        # 清除价格缓存
        for base_fee in BaseFee.objects.filter(product=self):
            # 获取所有区域键
            available_zones = []
            
            # 从JSONField获取区域
            if base_fee.zone_prices:
                for zone_key in base_fee.zone_prices:
                    if zone_key.startswith('zone'):
                        zone_num = zone_key.replace('zone', '')
                        zone = f"ZONE{zone_num}"
                        cache_key = f'price:{self.product_id}:{base_fee.weight}:{zone}'
                        cache.delete(cache_key)
                        available_zones.append(zone)
            
            # 如果没有JSONField数据，直接使用通配符尝试清除所有相关缓存
            if not available_zones:
                try:
                    # 检查是否可以直接访问Redis客户端
                    from django.core.cache import caches
                    redis_cache = caches['default']
                    if hasattr(redis_cache, '_client') and hasattr(redis_cache._client, 'keys'):
                        # 使用Redis的通配符搜索删除缓存键
                        pattern = f'price:{self.product_id}:{base_fee.weight}:*'
                        keys_to_delete = redis_cache._client.keys(pattern)
                        if keys_to_delete:
                            redis_cache._client.delete(*keys_to_delete)
                            logger.info(f"Cleared {len(keys_to_delete)} cache keys for pattern {pattern}")
                except Exception as e:
                    logger.warning(f"Error clearing cache with pattern: {str(e)}")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.clear_cache()

    def to_dict(self):
        """转换为字典格式"""
        # 获取基础费用
        base_fees = BaseFee.objects.filter(product=self)
        
        # 从基础费用构建重量点和区域费率
        weight_points = []
        zone_rates = []
        
        for fee in base_fees:
            # 添加重量点
            weight_point = {
                'id': fee.fee_id,
                'product_id': self.product_id,
                'weight': fee.weight,
                'unit': fee.weight_unit,
                'fee_type': fee.fee_type,
            }
            weight_points.append(weight_point)
            
            # 使用JSONField获取所有区域价格
            if fee.zone_prices:
                for zone_key, price in fee.zone_prices.items():
                    if zone_key.startswith('zone'):
                        zone_num = zone_key.replace('zone', '')
                        unit_price = fee.zone_unit_prices.get(zone_key, 0)
                        
                        # 创建区域费率
                        if price > 0 or unit_price > 0:
                            zone_rate = {
                                'id': f"{fee.fee_id}_{zone_num}",
                                'product_id': self.product_id,
                                'weight_point_id': fee.fee_id,
                                'zone': f"ZONE{zone_num}",
                                'base_rate': Decimal(str(price)),
                                'unit_rate': Decimal(str(unit_price)) if unit_price else Decimal('0'),
                            }
                            zone_rates.append(zone_rate)
        
        return {
            'id': self.pk,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'provider_name': self.provider_name,
            'dim_factor': float(self.dim_factor),
            'dim_factor_unit': self.dim_factor_unit,
            'effective_date': self.effective_date,
            'expiration_date': self.expiration_date,
            'country': self.country,
            'currency': self.currency,
            'weight_unit': self.weight_unit,
            'dim_unit': self.dim_unit,
            'description': self.description,
            'status': self.status,
            'enabled_start_date': self.enabled_start_date,
            'enabled_end_date': self.enabled_end_date,
            'weight_points': weight_points,
            'zone_rates': zone_rates,
            'surcharges': list(self.surcharge_set.values()),
            'peak_season_surcharges': list(self.peakseasonsurcharge_set.values()),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }


class Surcharge(BaseModel):
    """附加费表"""
    surcharge_id = models.AutoField('附加费ID', primary_key=True)
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        db_column='product_id',
        to_field='product_id',
        verbose_name='产品'
    )
    surcharge_type = models.CharField('附加费类型', max_length=50)
    sub_type = models.CharField('子类型', max_length=50, null=True, blank=True)
    condition_desc = models.TextField('条件描述', null=True, blank=True)
    # 使用JSONField存储区域附加费
    zone_fees = models.JSONField('区域附加费', default=dict, help_text='格式: {"zone1": 5.0, "zone2": 7.5}')
    display_order = models.IntegerField('显示顺序', default=0)

    class Meta:
        db_table = 'surcharges'
        verbose_name = '附加费'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['product', 'surcharge_type', 'sub_type']),
        ]
        ordering = ['display_order', 'surcharge_type']

    def __str__(self):
        return f"{self.product.product_name} - {self.surcharge_type}"
        
    def get_fee(self, zone_num):
        """获取指定区域的附加费"""
        zone_key = f"zone{zone_num}"
        if zone_key in self.zone_fees:
            return Decimal(str(self.zone_fees[zone_key]))
        return Decimal('0')
    
    def calculate_amount(self, zone: str) -> Decimal:
        """
        计算附加费金额
        
        Args:
            zone: 区域
            
        Returns:
            Decimal: 附加费金额
        """
        zone_num = zone.replace('ZONE', '')
        return self.get_fee(zone_num)
    
    def save(self, *args, **kwargs):
        """保存Surcharge对象"""
        super().save(*args, **kwargs)


class PeakSeasonSurcharge(BaseModel):
    """旺季附加费"""
    pss_id = models.AutoField('旺季附加费ID', primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='产品')
    surcharge_type = models.CharField('附加费类型', max_length=50)
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期')
    fee_amount = models.DecimalField('费用金额', max_digits=10, decimal_places=2, default=0)
    history = HistoricalRecords()

    class Meta:
        db_table = 'peak_season_surcharges'
        verbose_name = '旺季附加费'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['product', 'surcharge_type']),
        ]

    def __str__(self):
        return f"{self.product.product_name} - {self.surcharge_type} ({self.start_date} ~ {self.end_date})"
        
    def is_applicable(self) -> bool:
        """检查该旺季附加费是否应该应用
        
        检查条件:
        1. 当前日期在有效期内
        2. 费用金额大于0
        
        Returns:
            bool: 是否应用该旺季附加费
        """
        current_date = timezone.now().date()
        # 检查当前日期是否在有效期内，且金额大于0
        return (self.start_date <= current_date <= self.end_date) and self.fee_amount > 0


class BaseFee(BaseModel):
    """基础运费表"""
    fee_id = models.AutoField('费用ID', primary_key=True)
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        db_column='product_id',
        to_field='product_id',
        verbose_name='产品'
    )
    weight = models.DecimalField('重量值', max_digits=10, decimal_places=3)
    weight_unit = models.CharField('重量单位', max_length=5)
    fee_type = models.CharField('计费类型', max_length=20)
    # 使用JSONField存储区域价格，支持真正动态的分区
    zone_prices = models.JSONField('区域价格', default=dict, help_text='格式: {"zone1": 10.0, "zone2": 15.0}')
    zone_unit_prices = models.JSONField('区域单位价格', default=dict, help_text='格式: {"zone1": 0.5, "zone2": 0.75}')
    # 存储原始数据格式，以确保前端可以精确还原Excel的原始格式
    raw_data = models.JSONField('原始数据', default=dict, null=True, blank=True, 
                              help_text='存储原始数据行，保留完整格式')

    class Meta:
        db_table = 'base_fees'
        verbose_name = '基础运费'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['product', 'weight', 'fee_type']),
        ]

    def __str__(self):
        return f"{self.product.product_name} - {self.weight}{self.weight_unit}"
        
    def get_price(self, zone_num):
        """
        获取指定区域的价格
        
        Args:
            zone_num: 区域号
            
        Returns:
            Decimal: 价格
        """
        # 兼容两种格式：数字和字符串
        if isinstance(zone_num, str) and zone_num.startswith('ZONE'):
            zone_num = zone_num[4:]
        
        # 查找区域价格
        zone_key = f"zone{zone_num}"
        
        # 如果存在原始数据，优先使用原始数据
        if hasattr(self, 'raw_data') and self.raw_data:
            # 检查原始数据中是否包含价格列
            if self.raw_data and isinstance(self.raw_data, dict):
                # 尝试不同的可能键名
                possible_keys = [
                    f"ZONE{zone_num}",
                    f"Zone{zone_num}",
                    f"zone{zone_num}",
                    f"ZONE{zone_num}基础价格",
                    f"Zone{zone_num}基础价格",
                    f"zone{zone_num}基础价格",
                    f"ZONE{zone_num}_price",
                    f"zone{zone_num}_price",
                    f"Zone{zone_num}_price",
                    str(zone_num)  # 仅数字
                ]
                
                # 遍历所有可能的键名
                for key in possible_keys:
                    if key in self.raw_data:
                        try:
                            price_value = self.raw_data[key]
                            if price_value and (isinstance(price_value, (int, float, str))):
                                # 检查是否为有效价格
                                price = Decimal(str(price_value))
                                if price > 0:
                                    print(f"从raw_data中找到价格: {key}={price}", file=sys.stdout)
                                    return price
                        except (ValueError, TypeError, InvalidOperation):
                            continue
                
                # 如果没有找到匹配的键，打印raw_data的内容以便调试
                print(f"raw_data内容: {json.dumps(self.raw_data, indent=2)}", file=sys.stdout)
        
        # 从zone_prices中获取价格
        if zone_key in self.zone_prices:
            try:
                price_value = self.zone_prices[zone_key]
                price = Decimal(str(price_value))
                if price > 0:
                    print(f"从zone_prices中找到价格: {zone_key}={price}", file=sys.stdout)
                    return price
            except (ValueError, TypeError, InvalidOperation):
                logger.warning(f"产品[{self.product_id}]的区域[{zone_key}]价格格式无效")
                return Decimal('0')
        
        # 如果找不到区域价格，返回0
        print(f"未找到区域{zone_num}的价格，返回0", file=sys.stdout)
        return Decimal('0')
        
    def get_unit_price(self, zone_num):
        """获取指定区域的单位价格"""
        zone_key = f"zone{zone_num}"
        
        # 首先尝试从raw_data获取单价
        if self.raw_data:
            try:
                raw_data = self.raw_data if isinstance(self.raw_data, dict) else json.loads(self.raw_data)
                # 尝试不同的可能键名
                possible_keys = [
                    f"Zone{zone_num}单价",
                    f"zone{zone_num}单价",
                    f"Zone{zone_num}_unit_price",
                    f"zone{zone_num}_unit_price",
                    f"ZONE{zone_num}_unit_price"
                ]
                
                for key in possible_keys:
                    if key in raw_data and raw_data[key] is not None:
                        return Decimal(str(raw_data[key]))
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"从raw_data获取单价失败: {str(e)}")
        
        # 如果raw_data中没有找到，再从zone_unit_prices获取
        if zone_key in self.zone_unit_prices:
            return Decimal(str(self.zone_unit_prices[zone_key]))
            
        return Decimal('0')
    
    def save(self, *args, **kwargs):
        """保存BaseFee对象"""
        super().save(*args, **kwargs) 