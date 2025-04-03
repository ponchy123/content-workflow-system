import logging
from django.core.cache import cache
from django.conf import settings
from django.db.models import Count, Q, Case, When, Max, Min
from datetime import datetime, timedelta
from apps.products.models import Product, Surcharge, BaseFee
from django.utils import timezone
from django_redis import get_redis_connection
from apps.core.models import AccessLog
from apps.calculator.models import CalculationRequest, FuelRate
import json
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Tuple, List, Optional, Callable, Union
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from apps.postal_codes.models import ZipZone
from apps.fuel_rates.models import FuelRate
import random
from apps.core.exceptions import ProductNotFoundException, CacheException, WeightPointNotFoundException, ZonePriceNotFoundException
from django.core.cache import cache
from apps.core.constants import (
    CACHE_KEY_PREFIX,
    CACHE_TTL,
    LOCAL_CACHE_SIZE,
    CACHE_WARM_SAMPLE_SIZE,
    MAX_WORKERS,
    BATCH_CHUNK_SIZE,
    MAX_BATCH_RECORDS,
    BULK_INSERT_SIZE,
    PROCESSING_TIMEOUT,
    OPTIMAL_CHUNK_SIZE
)
from apps.core.utils import chunk_list
import concurrent.futures
from django.contrib.contenttypes.models import ContentType
import itertools
from concurrent.futures import as_completed
import time
from redis.exceptions import RedisError
import pickle
import threading
from apps.core.decorators import db_connection_retry
import uuid

logger = logging.getLogger(__name__)

class SmartCacheWarmer:
    """智能缓存预热器"""
    
    def __init__(self):
        self.redis_client = get_redis_connection("default")
        self.logger = logging.getLogger(__name__)
        self.cache_manager = None  # 将在后面设置

    def set_cache_manager(self, cache_manager):
        """设置缓存管理器引用"""
        self.cache_manager = cache_manager

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _calculate_priority(self, product_id: int) -> int:
        """计算产品的缓存优先级"""
        try:
            # 获取最近24小时的访问次数
            recent_hits = AccessLog.objects.filter(
                product_id=product_id,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # 获取最近的计算请求
            recent_calcs = CalculationRequest.objects.filter(
                product_id=product_id,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # 计算优先级分数
            return recent_hits + (recent_calcs * 2)  # 计算请求权重更高
            
        except Exception as e:
            logger.error(f"Error calculating priority for product {product_id}: {e}")
            return 0

    def _get_cache_version(self, product_id: int) -> str:
        """获取产品的缓存版本号"""
        try:
            product = Product.objects.get(id=product_id)
            # 使用更新时间作为版本号
            version = product.updated_at.timestamp()
            return f"v{version}"
        except Exception as e:
            self.logger.error(f"获取缓存版本失败: {str(e)}")
            return "v1"

    def get_with_lock(self, cache_key: str, fetch_func: Callable, *args, **kwargs) -> Any:
        """带分布式锁的缓存获取"""
        with self.cache_manager._get_lock(cache_key):
            value = self.cache_manager.get(cache_key)
            if value is not None:
                return value
            
            value = fetch_func(*args, **kwargs)
            if value is not None:
                self.cache_manager.set(cache_key, value)
            return value

    def optimize_cache_eviction(self):
        """优化缓存淘汰策略"""
        try:
            # 获取所有缓存键
            all_keys = self.redis_client.keys(f"{CACHE_KEY_PREFIX}:*")
            
            # 按访问频率和最后访问时间排序
            key_stats = []
            for key in all_keys:
                hits = int(self.redis_client.object('idletime', key) or 0)
                last_access = float(self.redis_client.object('freq', key) or 0)
                key_stats.append((key, hits, last_access))
            
            # 按优先级排序
            key_stats.sort(key=lambda x: (x[1], x[2]), reverse=True)
            
            # 保留高优先级的键
            keep_count = int(len(key_stats) * 0.8)  # 保留80%的键
            for key, _, _ in key_stats[keep_count:]:
                self.redis_client.delete(key)
                
        except Exception as e:
            self.logger.error(f"优化缓存淘汰策略失败: {str(e)}")

    def get_detailed_metrics(self) -> Dict[str, Any]:
        """获取详细的监控指标"""
        try:
            metrics = {
                'cache_stats': self.cache_manager.get_stats(),
                'redis_info': self.redis_client.info(),
                'custom_metrics': {
                    'product_cache_hits': {},
                    'zone_cache_hits': {},
                    'weight_range_cache_hits': {},
                    'response_times': [],
                    'error_rates': {},
                    'cache_size_by_type': {}
                }
            }
            
            # 获取产品缓存命中统计
            for key in self.redis_client.scan_iter(f"{CACHE_KEY_PREFIX}:product:*"):
                product_id = key.split(':')[-1]
                hits = int(self.redis_client.object('freq', key) or 0)
                metrics['custom_metrics']['product_cache_hits'][product_id] = hits
            
            # 获取响应时间统计
            response_times = AccessLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).values_list('response_time', flat=True)
            metrics['custom_metrics']['response_times'] = list(response_times)
            
            # 获取错误率统计
            error_logs = AccessLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1),
                status_code__gte=400
            ).values('status_code').annotate(count=Count('id'))
            metrics['custom_metrics']['error_rates'] = {
                log['status_code']: log['count'] for log in error_logs
            }
            
            # 获取各类型缓存大小
            for key_type in ['product', 'weight_range', 'zone_price', 'surcharge']:
                pattern = f"{CACHE_KEY_PREFIX}:{key_type}:*"
                size = sum(self.redis_client.memory_usage(key) or 0 
                          for key in self.redis_client.scan_iter(pattern))
                metrics['custom_metrics']['cache_size_by_type'][key_type] = size
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"获取详细监控指标失败: {str(e)}")
            return {}

    def warm_cache_intelligently(self) -> dict:
        """智能预热缓存"""
        try:
            # 获取最近访问的产品
            recent_products = self._get_recent_products()
            
            # 按优先级排序产品
            product_priorities = [
                (product, self._calculate_priority(product.id))
                for product in recent_products
            ]
            product_priorities.sort(key=lambda x: x[1], reverse=True)
            
            warmed_keys = []
            for product, priority in product_priorities:
                # 获取缓存版本
                version = self._get_cache_version(product.id)
                
                # 预热产品基本信息
                product_key = f"{CACHE_KEY_PREFIX}:product:{product.id}:{version}"
                self.get_with_lock(product_key, lambda: product)
                warmed_keys.append(product_key)
                
                # 预热重量范围
                weight_ranges = BaseFee.objects.filter(product=product, status=True)
                for weight_range in weight_ranges:
                    key = f"{CACHE_KEY_PREFIX}:weight_range:{product.id}:{weight_range.weight}:{version}"
                    self.get_with_lock(key, lambda: weight_range)
                    warmed_keys.append(key)
                
                # 预热区域价格
                for base_fee in weight_ranges:
                    # 从base_fee中获取所有区域
                    if base_fee.zone_prices:
                        for zone_key, price in base_fee.zone_prices.items():
                            if zone_key.startswith('zone'):
                                zone_num = zone_key[4:]  # 去掉'zone'前缀
                                zone = f"ZONE{zone_num}"
                                
                                # 为每个区域创建缓存键
                                key = f"{CACHE_KEY_PREFIX}:zone_price:{product.id}:{base_fee.fee_id}:{zone}"
                                
                                # 缓存区域价格数据
                                zone_price_data = {
                                    'zone': zone,
                                    'base_rate': price,
                                    'unit_rate': base_fee.zone_unit_prices.get(zone_key, '0'),
                                    'weight_point_id': base_fee.fee_id
                                }
                                
                                self.get_with_lock(key, lambda: zone_price_data)
                                warmed_keys.append(key)
                
                # 预热附加费
                surcharges = Surcharge.objects.filter(product=product, status=True)
                if surcharges.exists():
                    key = f"{CACHE_KEY_PREFIX}:surcharge:{product.id}:{version}"
                    self.get_with_lock(key, lambda: list(surcharges))
                    warmed_keys.append(key)
            
            # 优化缓存淘汰
            self.optimize_cache_eviction()
            
            # 收集监控指标
            metrics = self.get_detailed_metrics()
            
            return {
                'status': 'success',
                'code': 'SUCCESS',
                'message': '缓存预热完成',
                'data': {
                    'warmed_keys': warmed_keys,
                    'metrics': metrics,
                    'timestamp': timezone.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"缓存预热失败: {str(e)}")
            return {
                'status': 'error',
                'code': 'WARM_ERROR',
                'message': str(e),
                'data': None
            }

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _get_recent_products(self) -> list:
        """获取最近使用的产品列表"""
        try:
            # 获取最近24小时内有计算请求的产品
            recent_products = CalculationRequest.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).values('product_id').annotate(
                request_count=Count('id')
            ).order_by('-request_count')[:CACHE_WARM_SAMPLE_SIZE]
            
            return [p['product_id'] for p in recent_products]
            
        except Exception as e:
            logger.error(f"Error getting recent products: {e}")
            return []

    def _warm_product_cache(self, product_id: int) -> list:
        """预热指定产品的缓存"""
        try:
            warmed_keys = []
            
            # 获取产品信息
            try:
                product = Product.objects.get(id=product_id)
                product_key = f'product:{product_id}'
                self.redis_client.set(product_key, pickle.dumps(product))
                warmed_keys.append(product_key)
            except Product.DoesNotExist:
                return warmed_keys
                
            # 预热重量范围
            weight_ranges = BaseFee.objects.filter(product=product)
            for weight_range in weight_ranges:
                key = f"weight_range:{product_id}:{weight_range.weight}"
                self.redis_client.set(key, pickle.dumps(weight_range))
                warmed_keys.append(key)
                
            # 预热区域价格
            for base_fee in weight_ranges:
                # 从base_fee中获取所有区域
                if base_fee.zone_prices:
                    for zone_key, price in base_fee.zone_prices.items():
                        if zone_key.startswith('zone'):
                            zone_num = zone_key[4:]  # 去掉'zone'前缀
                            zone = f"ZONE{zone_num}"
                            
                            # 构建区域价格数据
                            zone_price_data = {
                                'zone': zone,
                                'base_rate': price,
                                'unit_rate': base_fee.zone_unit_prices.get(zone_key, '0'),
                                'weight_point_id': base_fee.fee_id
                            }
                            
                            key = f'zone_price:{product_id}:{zone}'
                            self.redis_client.set(key, pickle.dumps(zone_price_data))
                            warmed_keys.append(key)
            
            return warmed_keys
            
        except Exception as e:
            logger.error(f"预热产品{product_id}的缓存失败: {str(e)}")
            return []

    def _calculate_and_cache(self, product_id: int, weight: Decimal, from_postal: str, to_postal: str) -> bool:
        """计算并缓存运费"""
        try:
            # 获取产品信息
            product = self.cache_manager.get(
                self.cache_manager.get_cache_key('product', product_id=product_id),
                lambda: Product.objects.get(id=product_id)
            )
            if not product:
                return False
                
            # 获取重量范围
            weight_range = self.cache_manager.get(
                self.cache_manager.get_cache_key('weight_range', product_id=product_id, weight=str(weight)),
                lambda: BaseFee.objects.filter(
                    product=product,
                    weight__gte=weight
                ).order_by('weight').first()
            )
            if not weight_range:
                return False
                
            # 获取区域价格
            # 根据邮编获取区域号
            zone = self._get_postal_zone(from_postal, to_postal)
            if not zone:
                return False
                
            # 从zone获取区域号 (ZONE1 -> 1)
            zone_num = zone.replace('ZONE', '')
            
            # 检查weight_range是否包含此区域的价格
            if not weight_range.zone_prices or f'zone{zone_num}' not in weight_range.zone_prices:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error calculating and caching: {str(e)}")
            return False

    def invalidate_cache(self, product_id: int) -> dict:
        """使指定产品的所有缓存失效"""
        try:
            # 获取产品信息
            product = Product.objects.get(id=product_id)
            
            # 删除产品相关的所有缓存
            patterns = [
                f"{CACHE_KEY_PREFIX}:product:{product_id}",
                f"{CACHE_KEY_PREFIX}:weight_range:{product_id}:*",
                f"{CACHE_KEY_PREFIX}:zone_price:{product_id}:*",
                f"{CACHE_KEY_PREFIX}:surcharge:{product_id}"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                deleted_count += self.cache_manager.delete_pattern(pattern)
            
            return {
                'status': 'success',
                'code': 'SUCCESS',
                'data': {
                    'product_id': product_id,
                    'invalidated_keys': deleted_count,
                    'message': f'Successfully invalidated {deleted_count} cache keys'
                }
            }
            
        except Product.DoesNotExist:
            return {
                'status': 'error',
                'code': 'PRODUCT_NOT_FOUND',
                'message': f'Product {product_id} not found'
            }
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return {
                'status': 'error',
                'code': 'INVALIDATION_ERROR',
                'message': str(e)
            }

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_cached_product(self, product_id: int) -> Product:
        """获取缓存的产品信息"""
        cache_key = self.cache_manager.get_cache_key('product', product_id=product_id)
        product = self.cache_manager.get(cache_key)
        
        if not product:
            try:
                product = Product.objects.get(id=product_id)
                if product:
                    self.cache_manager.set(cache_key, product)
            except Product.DoesNotExist:
                raise ProductNotFoundException(f"Product {product_id} not found")
                
        return product

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_cached_weight_range(self, product_id: int, weight: Decimal) -> Optional[BaseFee]:
        """获取缓存的重量范围"""
        cache_key = self.cache_manager.get_cache_key('weight_range', product_id=product_id, weight=str(weight))
        weight_range = self.cache_manager.get(cache_key)
        
        if not weight_range:
            try:
                # 使用BaseFee查询，条件为：最小重量小于等于给定重量，最大重量大于等于给定重量
                weight_range = BaseFee.objects.filter(
                    product_id=product_id,
                    min_weight__lte=weight,
                    weight__gte=weight
                ).first()
                
                if weight_range:
                    self.cache_manager.set(cache_key, weight_range)
            except Exception as e:
                logger.error(f"Error fetching weight range for product {product_id} and weight {weight}: {e}")
                return None
                
        return weight_range

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_cached_zone_price(self, product_id: int, from_zone: str, to_zone: str) -> Optional[Dict]:
        """获取缓存的区域价格"""
        cache_key = self.cache_manager.get_cache_key('zone_price', product_id=product_id, from_zone=from_zone, to_zone=to_zone)
        zone_price = self.cache_manager.get(cache_key)
        
        if not zone_price:
            try:
                # 从to_zone获取区域号码 (ZONE1 -> 1)
                zone_num = to_zone.replace('ZONE', '')
                
                # 获取产品的所有基础费用
                base_fees = BaseFee.objects.filter(
                    product_id=product_id,
                    status=True
                )
                
                # 查找包含该区域价格的基础费用
                for base_fee in base_fees:
                    # 检查base_fee是否有该区域的价格
                    zone_key = f'zone{zone_num}'
                    if base_fee.zone_prices and zone_key in base_fee.zone_prices:
                        # 构建区域价格数据
                        zone_price = {
                            'zone': to_zone,
                            'base_rate': base_fee.zone_prices[zone_key],
                            'unit_rate': base_fee.zone_unit_prices.get(zone_key, 0)
                        }
                        self.cache_manager.set(cache_key, zone_price)
                        return zone_price
                        
                return None
            except Exception as e:
                logger.error(f"获取区域价格失败: {str(e)}")
                return None
                
        return zone_price

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_cached_surcharges(self, product_id: int) -> List[Surcharge]:
        """获取缓存的附加费用"""
        cache_key = self.cache_manager.get_cache_key('surcharge', product_id=product_id)
        surcharges = self.cache_manager.get(cache_key)
        
        if not surcharges:
            try:
                surcharges = list(Surcharge.objects.filter(product_id=product_id))
                if surcharges:
                    self.cache_manager.set(cache_key, surcharges)
            except Exception as e:
                logger.error(f"Error getting surcharges for product {product_id}: {e}")
                return []
                
        return surcharges

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_cached_postal_zone(self, postal_code: str) -> Optional[str]:
        """获取缓存的邮编区域"""
        cache_key = self.cache_manager.get_cache_key('postal_zone', postal_code=postal_code)
        zone = self.cache_manager.get(cache_key)
        
        if not zone:
            try:
                # 查找匹配的zip区域
                zip_zone = ZipZone.objects.filter(
                    dest_zip_start__lte=postal_code,
                    dest_zip_end__gte=postal_code
                ).first()
                if zip_zone:
                    zone = f"ZONE{zip_zone.zone_number}"
                    self.cache_manager.set(cache_key, zone)
            except Exception:
                return None
                
        return zone

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_cached_fuel_rate(self, provider_id: int) -> Optional[FuelRate]:
        """获取缓存的燃油费率"""
        today = timezone.now().date()
        cache_key = self.cache_manager.get_cache_key('fuel_rate', provider_id=provider_id, date=today)
        fuel_rate = self.cache_manager.get(cache_key)
        
        if not fuel_rate:
            try:
                fuel_rate = FuelRate.objects.filter(
                    provider_id=provider_id,
                    effective_date__lte=today
                ).order_by('-effective_date').first()
                
                if fuel_rate:
                    self.cache_manager.set(cache_key, fuel_rate)
            except Exception as e:
                logger.error(f"Error getting fuel rate for provider {provider_id}: {e}")
                return None
                
        return fuel_rate

    def clear_local_cache(self):
        """清理本地缓存"""
        self.cache_manager.clear_local_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.cache_manager.get_stats()

    def optimize_cache_ttl(self, product_id: int) -> int:
        """优化缓存TTL"""
        try:
            # 分析产品访问频率
            access_stats = self.analyze_access_patterns()
            product_hits = access_stats.get('data', {}).get('products', {}).get(product_id, {}).get('hits', 0)
            
            # 根据访问频率调整TTL
            if product_hits > 1000:
                return CACHE_TTL * 2  # 高频访问，延长TTL
            elif product_hits < 100:
                return CACHE_TTL // 2  # 低频访问，缩短TTL
            
            return CACHE_TTL
        except Exception as e:
            logger.error(f"优化缓存TTL失败: {str(e)}")
            return CACHE_TTL

    def clean_expired_cache(self) -> dict:
        """清理过期缓存"""
        try:
            # 获取所有缓存键
            pattern = f"{CACHE_KEY_PREFIX}:*"
            keys = self.cache_manager.redis_client.keys(pattern)
            
            # 清理过期键
            expired_count = 0
            for key in keys:
                if not self.cache_manager.redis_client.ttl(key):
                    self.cache_manager.redis_client.delete(key)
                    expired_count += 1
            
            return {
                'status': 'success',
                'cleaned_keys': expired_count,
                'total_keys': len(keys)
            }
        except Exception as e:
            logger.error(f"清理过期缓存失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def reset_stats(self):
        """重置缓存统计"""
        self.cache_manager.reset_stats()

    @staticmethod
    def get_cache_key(key_type: str, **kwargs) -> str:
        """
        生成缓存键
        Args:
            key_type: 键类型
            **kwargs: 参数
        Returns:
            str: 缓存键
        Raises:
            ValueError: 未知的缓存键类型
        """
        if key_type not in CACHE_KEY_TYPES:
            raise ValueError(f'未知的缓存键类型: {key_type}')
            
        key_generator = CACHE_KEY_TYPES[key_type]
        return key_generator(**kwargs)

class CacheManager:
    """
    缓存管理器负责处理系统中的各种缓存操作
    提供缓存预热、清理和一致性维护等功能
    """
    
    def __init__(self):
        self.redis_client = get_redis_connection("default")
        self.local_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_ttl = CACHE_TTL
        self._locks = {}
        self.warmer = SmartCacheWarmer()
        self.warmer.set_cache_manager(self)  # 设置反向引用
        self.cache_timeout = getattr(settings, 'CACHE_TIMEOUT', 3600)  # 默认缓存过期时间（秒）
        self.sample_size = getattr(settings, 'CACHE_WARM_SAMPLE_SIZE', 100)  # 预热样本数量
        
    def _get_lock(self, key: str):
        """获取指定键的锁"""
        if key not in self._locks:
            self._locks[key] = threading.Lock()
        return self._locks[key]

    def get_cache_key(self, key_type: str, **kwargs) -> str:
        """
        获取缓存键
        
        Args:
            key_type: 缓存类型（product, weight_point, zone_price）
            **kwargs: 其他参数
            
        Returns:
            str: 缓存键
        """
        if key_type == 'product':
            return f"{CACHE_KEY_PREFIX}:product:{kwargs.get('product_id')}"
        elif key_type == 'weight_point':
            return f"{CACHE_KEY_PREFIX}:weight_point:{kwargs.get('product_id')}:{kwargs.get('weight')}"
        elif key_type == 'zone_price':
            return f"{CACHE_KEY_PREFIX}:zone_price:{kwargs.get('product_id')}:{kwargs.get('weight_point_id')}:{kwargs.get('zone')}"
        else:
            return f"{CACHE_KEY_PREFIX}:{key_type}:{uuid.uuid4().hex}"

    def get(self, key: str, fetch_func: Optional[Callable] = None, *args, **kwargs) -> Any:
        """
        获取缓存数据，如果不存在则使用fetch_func获取并缓存
        """
        try:
            # 先从本地缓存获取
            if key in self.local_cache:
                self.cache_hits += 1
                return self.local_cache[key]
            
            # 从Redis获取
            data = cache.get(key)
            if data is not None:
                self.cache_hits += 1
                self.local_cache[key] = data
                return data
            
            self.cache_misses += 1
            
            # 如果提供了获取函数，则获取数据并缓存
            if fetch_func:
                # 使用锁防止缓存击穿和缓存雪崩
                with self._get_lock(key):
                    # 双重检查，防止其他线程已经缓存了数据
                    data = cache.get(key)
                    if data is not None:
                        self.cache_hits += 1
                        self.local_cache[key] = data
                        return data
                        
                    data = fetch_func(*args, **kwargs)
                    if data is not None:
                        self.set(key, data)
                    return data
                
            return None
            
        except RedisError as e:
            logger.error(f"Redis error while getting key {key}: {str(e)}")
            if key in self.local_cache:
                return self.local_cache[key]
            return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        设置缓存数据
        """
        try:
            with self._get_lock(key):
                # 设置到本地缓存
                self.local_cache[key] = value
                
                # 如果本地缓存太大，清理最早的数据
                if len(self.local_cache) > LOCAL_CACHE_SIZE:
                    oldest_key = next(iter(self.local_cache))
                    del self.local_cache[oldest_key]
                
                # 设置到Redis
                return cache.set(key, value, timeout or self.cache_ttl)
            
        except RedisError as e:
            logger.error(f"Redis error while setting key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存数据
        """
        try:
            with self._get_lock(key):
                # 从本地缓存删除
                self.local_cache.pop(key, None)
                
                # 从Redis删除
                return cache.delete(key)
            
        except RedisError as e:
            logger.error(f"Redis error while deleting key {key}: {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存
        """
        try:
            # 获取所有匹配的键
            keys = self.redis_client.keys(pattern)
            deleted_count = 0
            
            # 逐个删除键，使用锁机制
            for key in keys:
                with self._get_lock(key):
                    # 从本地缓存删除
                    if key in self.local_cache:
                        del self.local_cache[key]
                    
                    # 从Redis删除
                    if self.redis_client.delete(key):
                        deleted_count += 1
            
            return deleted_count
            
        except RedisError as e:
            logger.error(f"Redis error while deleting pattern {pattern}: {str(e)}")
            return 0

    def clear_local_cache(self):
        """
        清空本地缓存
        """
        self.local_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        """
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total': total,
            'hit_rate': hit_rate,
            'local_cache_size': len(self.local_cache),
            'redis_keys': len(self.redis_client.keys(f"{CACHE_KEY_PREFIX}:*"))
        }

    def reset_stats(self):
        """
        重置统计信息
        """
        self.cache_hits = 0
        self.cache_misses = 0

    def warm_all_caches(self) -> dict:
        """预热所有缓存"""
        try:
            # 使用智能缓存预热器预热缓存
            result = self.warmer.warm_cache_intelligently()
            logger.info("Cache warming completed successfully")
            return result
        except Exception as e:
            logger.error(f"Cache warming failed: {str(e)}")
            raise

    def warm_weight_ranges_cache(self, product_id: int = None) -> bool:
        """
        预热重量范围缓存
        Args:
            product_id: 产品ID，如果为None则预热所有产品
        Returns:
            bool: 是否成功
        """
        try:
            # 获取需要预热的产品ID列表
            if product_id:
                product_ids = [product_id]
            else:
                product_ids = Product.objects.filter(status=True).values_list('id', flat=True)
            
            # 获取当前日期
            current_date = timezone.now().date()
            
            # 为每个产品预热重量范围
            for pid in product_ids:
                try:
                    # 获取产品的重量范围
                    weight_ranges = BaseFee.objects.filter(
                        product_id=pid,
                        status=True
                    ).order_by('weight')
                    
                    if not weight_ranges:
                        logger.warning(f"No weight ranges found for product {pid}")
                        continue
                    
                    # 获取最小和最大重量
                    min_max = weight_ranges.aggregate(
                        min_weight=Min('weight'), 
                        max_weight=Max('weight')
                    )
                    min_weight = min_max['min_weight'] or Decimal('0.5')
                    max_weight = min_max['max_weight'] or Decimal('70.0')
                    
                    # 生成样本重量
                    samples = self._generate_weight_samples(min_weight, max_weight)
                    
                    # 为每个样本重量预热缓存
                    for weight in samples:
                        # 查找适用的重量范围
                        weight_range = weight_ranges.filter(
                            weight__gte=weight
                        ).order_by('weight').first()
                        
                        if not weight_range:
                            continue
                        
                        # 构建缓存键
                        cache_key = self.get_cache_key('weight_range', product_id=pid, weight=weight)
                        
                        # 设置缓存
                        cache.set(cache_key, weight_range, self.cache_timeout)
                        
                    logger.info(f"Warmed weight ranges cache for product {pid}, {len(samples)} samples")
                except Exception as e:
                    logger.error(f"Error warming weight ranges cache for product {pid}: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error warming weight ranges cache: {str(e)}")
            raise CacheException(f"Failed to warm weight ranges cache: {str(e)}")
    
    def warm_zone_prices_cache(self, product_ids=None):
        """
        预热区域价格缓存
        
        Args:
            product_ids: 指定产品ID列表，如果为None则预热所有产品
            
        Returns:
            dict: 预热结果
        """
        try:
            logger = logging.getLogger(__name__)
            
            # 获取需要预热的产品ID
            if product_ids is None:
                # 获取所有活跃产品
                products = Product.objects.filter(
                    status=True,
                    effective_date__lte=timezone.now().date(),
                    expiration_date__gte=timezone.now().date()
                )
                product_ids = [p.id for p in products]
            else:
                # 如果传入的不是列表，转换为列表
                if not isinstance(product_ids, list):
                    product_ids = [product_ids]
            
            logger.info(f"Warming zone prices cache for products: {product_ids}")
            
            # 统计预热的缓存数量
            warmed_count = 0
            
            # 为每个产品预热区域价格
            for pid in product_ids:
                try:
                    # 获取产品的重量点
                    weight_points = BaseFee.objects.filter(
                        product_id=pid,
                        status=True
                    )
                    
                    if not weight_points:
                        logger.warning(f"No weight points found for product {pid}")
                        continue
                    
                    # 为每个重量点和区域预热价格
                    for weight_point in weight_points:
                        # 获取所有可用区域
                        available_zones = []
                        
                        # 从JSONField获取区域
                        if weight_point.zone_prices:
                            for zone_key in weight_point.zone_prices.keys():
                                if zone_key.startswith('zone'):
                                    zone_num = zone_key.replace('zone', '')
                                    available_zones.append(f"ZONE{zone_num}")
                        
                        logger.info(f"Available zones for product {pid}, weight {weight_point.weight}: {available_zones}")
                        
                        # 为每个区域预热价格
                        for zone in available_zones:
                            zone_num = zone.replace('ZONE', '')
                            price = weight_point.get_price(zone_num)
                            
                            # 如果价格为0，跳过
                            if price <= 0:
                                continue
                            
                            # 构建缓存键
                            cache_key = f"{CACHE_KEY_PREFIX}:zone_price:{pid}:{weight_point.fee_id}:{zone}"
                            
                            # 缓存区域价格
                            zone_price_data = {
                                'zone': zone,
                                'base_rate': float(price),
                                'unit_rate': float(weight_point.get_unit_price(zone_num))
                            }
                            
                            # 存入缓存
                            cache.set(cache_key, zone_price_data, 3600 * 24)  # 缓存24小时
                            warmed_count += 1
                    
                    logger.info(f"Warmed {warmed_count} zone prices for product {pid}")
                    
                except Exception as e:
                    logger.error(f"Error warming zone prices for product {pid}: {str(e)}")
                    continue
            
            return {
                'success': True,
                'warmed_count': warmed_count
            }
        
        except Exception as e:
            logger.error(f"Error warming zone prices: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def warm_postal_zones_cache(self, limit: int = 1000) -> bool:
        """
        预热邮编区域缓存
        Args:
            limit: 预热的数量限制
        Returns:
            bool: 是否成功
        """
        try:
            # 获取常用的邮编对
            # 这里可以根据实际情况优化，例如从历史记录中获取常用的邮编对
            postal_pairs = ZipZone.objects.all().order_by('?')[:limit]
            
            # 为每个邮编对预热区域
            for postal_pair in postal_pairs:
                try:
                    # 构建缓存键
                    cache_key = self.get_cache_key(
                        'postal_zone', 
                        from_postal=postal_pair.origin_zip, 
                        to_postal=postal_pair.dest_zip_start
                    )
                    
                    # 设置缓存
                    cache.set(cache_key, f"ZONE{postal_pair.zone_number}", self.cache_timeout)
                except Exception as e:
                    logger.error(f"Error warming postal zone cache for {postal_pair.origin_zip}-{postal_pair.dest_zip_start}: {str(e)}")
            
            logger.info(f"Warmed postal zones cache, {len(postal_pairs)} pairs")
            return True
        except Exception as e:
            logger.error(f"Error warming postal zones cache: {str(e)}")
            raise CacheException(f"Failed to warm postal zones cache: {str(e)}")
    
    def _generate_weight_samples(self, min_weight: Decimal, max_weight: Decimal) -> List[Decimal]:
        """
        生成重量样本
        Args:
            min_weight: 最小重量
            max_weight: 最大重量
        Returns:
            List[Decimal]: 重量样本列表
        """
        samples = []
        
        # 添加边界值
        samples.append(min_weight)
        samples.append(max_weight)
        
        # 添加常用重量
        common_weights = [
            Decimal('0.5'), Decimal('1.0'), Decimal('2.0'), Decimal('5.0'), 
            Decimal('10.0'), Decimal('15.0'), Decimal('20.0'), Decimal('30.0'), 
            Decimal('50.0'), Decimal('70.0')
        ]
        for weight in common_weights:
            if min_weight <= weight <= max_weight:
                samples.append(weight)
        
        # 添加随机样本
        range_size = max_weight - min_weight
        step = max(Decimal('0.1'), range_size / Decimal(str(self.sample_size)))
        
        for i in range(self.sample_size - len(samples)):
            # 生成随机重量
            random_weight = min_weight + Decimal(random.uniform(0, float(range_size)))
            # 四舍五入到0.1
            random_weight = random_weight.quantize(Decimal('0.1'))
            samples.append(random_weight)
        
        # 去重排序
        return sorted(set(samples))
    
    def clear_product_cache(self, product_id: int) -> bool:
        """
        清除产品相关的缓存
        Args:
            product_id: 产品ID
        Returns:
            bool: 是否成功
        """
        try:
            # 清除产品缓存
            product_key = self.get_cache_key('product', product_id=product_id)
            cache.delete(product_key)
            
            # 获取产品的重量点
            weight_points = BaseFee.objects.filter(
                product_id=product_id
            )
            
            # 清除重量点和区域价格缓存
            for weight_point in weight_points:
                # 清除可能的重量点缓存
                weight_point_key = self.get_cache_key('weight_point', product_id=product_id, weight=weight_point.weight)
                cache.delete(weight_point_key)
                
                # 获取所有可用区域
                available_zones = []
                
                # 从JSONField获取区域
                if weight_point.zone_prices:
                    for zone_key in weight_point.zone_prices.keys():
                        if zone_key.startswith('zone'):
                            zone_num = zone_key.replace('zone', '')
                            available_zones.append(f"ZONE{zone_num}")
                
                # 清除区域价格缓存
                for zone in available_zones:
                    zone_price_key = self.get_cache_key('zone_price', product_id=product_id, weight_point_id=weight_point.fee_id, zone=zone)
                    cache.delete(zone_price_key)
            
            logger.info(f"Cleared cache for product {product_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing product cache: {str(e)}")
            return False
    
    def get_weight_range(self, product_id: int, weight: Decimal) -> Optional[Dict]:
        """
        获取重量范围
        Args:
            product_id: 产品ID
            weight: 重量
        Returns:
            Optional[Dict]: 重量范围
        Raises:
            WeightPointNotFoundException: 重量点不存在异常
        """
        # 构建缓存键
        cache_key = self.get_cache_key('weight_range', product_id=product_id, weight=weight)
        
        # 从缓存获取
        weight_range = cache.get(cache_key)
        
        if not weight_range:
            # 缓存中不存在，从数据库获取
            try:
                weight_range = BaseFee.objects.filter(
                    product_id=product_id,
                    status=True,
                    weight__gte=weight
                ).order_by('weight').first()
                
                if not weight_range:
                    raise WeightPointNotFoundException(f"找不到产品 {product_id} 重量 {weight} 的重量点")
                
                # 设置缓存
                cache.set(cache_key, weight_range, self.cache_timeout)
            except WeightPointNotFoundException:
                raise
            except Exception as e:
                logger.error(f"获取重量点时出错: {str(e)}")
                raise WeightPointNotFoundException(f"获取重量点失败: {str(e)}")
        
        return weight_range
    
    def get_zone_price(self, product_id: int, weight_point_id: int, zone: str) -> Optional[Dict]:
        """
        获取区域价格
        Args:
            product_id: 产品ID
            weight_point_id: 重量点ID
            zone: 区域
        Returns:
            Optional[Dict]: 区域价格
        Raises:
            ZonePriceNotFoundException: 区域价格不存在异常
        """
        # 构建缓存键
        cache_key = self.get_cache_key('zone_price', product_id=product_id, weight_point_id=weight_point_id, zone=zone)
        
        # 从缓存获取
        zone_price = cache.get(cache_key)
        
        if not zone_price:
            # 缓存中不存在，从数据库获取
            try:
                # 获取对应的基础费用
                weight_point = BaseFee.objects.get(
                    fee_id=weight_point_id,
                    status=True
                )
                
                # 获取区域号码
                zone_num = zone.replace('ZONE', '')
                
                # 从JSONField获取价格数据
                price = weight_point.get_price(zone_num)
                unit_price = weight_point.get_unit_price(zone_num)
                
                # 如果该区域没有价格，抛出异常
                if price <= 0:
                    raise ZonePriceNotFoundException(f"找不到产品 {product_id} 重量点 {weight_point_id} 区域 {zone} 的价格")
                
                # 构建区域价格
                zone_price = {
                    'base_rate': price,
                    'unit_rate': unit_price,
                    'zone': zone,
                    'weight_point_id': weight_point_id
                }
                
                # 设置缓存
                cache.set(cache_key, zone_price, self.cache_timeout)
            except ZonePriceNotFoundException:
                raise
            except Exception as e:
                logger.error(f"获取区域价格时出错: {str(e)}")
                raise ZonePriceNotFoundException(f"获取区域价格失败: {str(e)}")
        
        return zone_price

# 创建全局缓存管理器实例
cache_manager = CacheManager()

# 缓存键类型定义
CACHE_KEY_TYPES = {
    'product': lambda product_id: f'{CACHE_KEY_PREFIX}:product:{product_id}',
    'weight_range': lambda product_id, weight: f'{CACHE_KEY_PREFIX}:weight_range:{product_id}:{weight}',
    'zone_price': lambda product_id, zone: f'{CACHE_KEY_PREFIX}:zone_price:{product_id}:{zone}',
    'surcharge': lambda product_id: f'{CACHE_KEY_PREFIX}:surcharge:{product_id}',
    'fuel_rate': lambda provider_id, date: f'{CACHE_KEY_PREFIX}:fuel_rate:{provider_id}:{date}',
    'postal_zones': lambda: f'{CACHE_KEY_PREFIX}:postal_zones',
} 