"""
缓存管理服务
负责管理运费计算相关的缓存
"""

import logging
import threading
from typing import Dict, Any, Optional, List
from decimal import Decimal

from django.core.cache import cache
from django.conf import settings
from django_redis import get_redis_connection
from redis.exceptions import RedisError

from apps.core.constants import (
    CACHE_KEY_PREFIX,
    CACHE_TTL,
    LOCAL_CACHE_SIZE
)
from apps.core.exceptions import CacheException

logger = logging.getLogger(__name__)

class CacheService:
    """
    缓存服务类
    负责计算结果和相关数据的缓存管理
    """
    
    def __init__(self):
        """初始化缓存服务"""
        self.logger = logging.getLogger(__name__)
        
        # 初始化Redis缓存
        try:
            self.redis_cache = get_redis_connection("default")
        except Exception as e:
            self.logger.warning(f"Redis连接失败: {str(e)}，将使用Django缓存后端")
            self.redis_cache = None
        
        # 初始化本地缓存
        self._init_local_cache()
    
    def _init_local_cache(self):
        """初始化本地缓存"""
        self.local_cache = {}
        self.local_cache_size = getattr(settings, 'LOCAL_CACHE_SIZE', LOCAL_CACHE_SIZE)
        self.local_cache_lock = threading.Lock()
        self.logger.info(f"初始化本地缓存，大小: {self.local_cache_size}")
    
    def generate_cache_key(self, data: Dict[str, Any]) -> str:
        """
        生成缓存键
        
        Args:
            data: 请求数据，包含各种计算参数
            
        Returns:
            str: 生成的缓存键
        """
        # 提取关键字段
        key_fields = {
            'product_id': data.get('product_id'),
            'weight': data.get('weight'),
            'from_postal': data.get('from_postal'),
            'to_postal': data.get('to_postal'),
            'length': data.get('length'),
            'width': data.get('width'),
            'height': data.get('height'),
            'is_residential': data.get('is_residential', False)
        }

        # 生成缓存键
        cache_key = f"{CACHE_KEY_PREFIX}:calc:{':'.join([f'{k}={v}' for k, v in sorted(
            key_fields.items()) if v is not None])}"
        return cache_key
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        从缓存中获取数据
        
        Args:
            cache_key: 缓存键
            
        Returns:
            Optional[Dict]: 缓存的数据，如果不存在则返回None
        """
        # 首先检查本地缓存
        with self.local_cache_lock:
            if cache_key in self.local_cache:
                self.logger.debug(f"本地缓存命中: {cache_key}")
                return self.local_cache[cache_key]
        
        # 然后检查Redis缓存
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"Redis缓存命中: {cache_key}")
                # 更新本地缓存
                self._update_local_cache(cache_key, cached_data)
                return cached_data
        except Exception as e:
            self.logger.warning(f"从缓存获取数据失败: {str(e)}")
        
        return None
    
    def set_to_cache(self, cache_key: str, data: Dict, ttl: int = None) -> bool:
        """
        将数据存入缓存
        
        Args:
            cache_key: 缓存键
            data: 要缓存的数据
            ttl: 缓存过期时间（秒），默认为None，使用系统配置
            
        Returns:
            bool: 是否成功缓存
        """
        if not ttl:
            ttl = getattr(settings, 'CACHE_TIMEOUT', CACHE_TTL)
        
        # 更新本地缓存
        self._update_local_cache(cache_key, data)
        
        # 更新Redis缓存
        try:
            cache.set(cache_key, data, timeout=ttl)
            self.logger.debug(f"数据已缓存: {cache_key}, TTL: {ttl}秒")
            return True
        except Exception as e:
            self.logger.warning(f"缓存数据失败: {str(e)}")
            return False
    
    def _update_local_cache(self, key: str, value: Any):
        """
        更新本地缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self.local_cache_lock:
            # 如果缓存已满，删除最旧的条目
            if len(self.local_cache) >= self.local_cache_size:
                oldest_key = next(iter(self.local_cache))
                del self.local_cache[oldest_key]
                self.logger.debug(f"本地缓存已满，删除最旧的条目: {oldest_key}")
            
            # 添加新条目
            self.local_cache[key] = value
    
    def invalidate_cache(self, cache_key: str) -> bool:
        """
        使缓存失效
        
        Args:
            cache_key: 缓存键
            
        Returns:
            bool: 是否成功使缓存失效
        """
        # 从本地缓存中删除
        with self.local_cache_lock:
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
                self.logger.debug(f"从本地缓存中删除: {cache_key}")
        
        # 从Redis缓存中删除
        try:
            cache.delete(cache_key)
            self.logger.debug(f"从Redis缓存中删除: {cache_key}")
            return True
        except Exception as e:
            self.logger.warning(f"删除缓存失败: {str(e)}")
            return False
    
    def clear_product_cache(self, product_id: str) -> bool:
        """
        清除特定产品的所有缓存
        
        Args:
            product_id: 产品ID
            
        Returns:
            bool: 是否成功清除缓存
        """
        # 清除本地缓存
        with self.local_cache_lock:
            keys_to_delete = [k for k in self.local_cache if f'product_id={product_id}' in k]
            for key in keys_to_delete:
                del self.local_cache[key]
            self.logger.debug(f"从本地缓存中删除产品相关条目: {len(keys_to_delete)}个")
        
        # 清除Redis缓存
        try:
            # 获取包含该产品ID的所有缓存键
            pattern = f"{CACHE_KEY_PREFIX}:*product_id={product_id}*"
            if self.redis_cache:
                keys = self.redis_cache.keys(pattern)
                if keys:
                    self.redis_cache.delete(*keys)
                    self.logger.debug(f"从Redis缓存中删除产品相关条目: {len(keys)}个")
                return True
            else:
                self.logger.warning("Redis连接不可用，无法按模式删除缓存")
                return False
        except Exception as e:
            self.logger.warning(f"清除产品缓存失败: {str(e)}")
            return False
    
    def warm_cache(self, patterns: List[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        预热缓存
        
        Args:
            patterns: 请求模式列表，用于生成预热的请求
            
        Returns:
            Dict[str, int]: 预热结果统计
        """
        from apps.calculator.calculator import Calculator
        
        if not patterns:
            # 如果没有提供模式，使用默认模式
            patterns = [
                {
                    'product_id': 'DEFAULT',
                    'weight': '1.0',
                    'from_postal': '10001',
                    'to_postal': '90001'
                }
            ]
        
        calculator = Calculator()
        success_count = 0
        failed_count = 0
        
        self.logger.info(f"开始缓存预热，模式数量: {len(patterns)}")
        
        for pattern in patterns:
            try:
                # 生成缓存键
                cache_key = self.generate_cache_key(pattern)
                
                # 检查缓存是否已存在
                if self.get_from_cache(cache_key):
                    self.logger.debug(f"缓存已存在，跳过预热: {cache_key}")
                    continue
                
                # 计算并缓存结果
                result = calculator.calculate(pattern)
                self.set_to_cache(cache_key, result)
                success_count += 1
                
                self.logger.debug(f"缓存预热成功: {cache_key}")
            except Exception as e:
                self.logger.warning(f"缓存预热失败: {str(e)}")
                failed_count += 1
        
        self.logger.info(f"缓存预热完成，成功: {success_count}，失败: {failed_count}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(patterns)
        } 