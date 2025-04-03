"""
配置值获取模块
避免硬编码的配置值，提供动态获取机制
"""
from decimal import Decimal
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

# 默认区域常量
DEFAULT_ZONE = '1'

def get_setting(key, default=None):
    """
    获取配置项，如果未找到则返回None或指定的默认值
    
    Args:
        key: 配置项名称
        default: 自定义默认值
        
    Returns:
        配置值
    """
    # 尝试从settings获取
    if hasattr(settings, key):
        return getattr(settings, key)
    
    # 尝试从环境变量获取
    env_key = f"FREIGHT_{key.upper()}"
    if env_key in os.environ:
        value = os.environ[env_key]
        
        # 尝试转换为适当类型
        try:
            # 整数
            if value.isdigit():
                return int(value)
            
            # 浮点数
            if '.' in value and value.replace('.', '', 1).isdigit():
                return float(value)
            
            # 布尔值
            if value.lower() in ('true', 'yes', '1'):
                return True
            if value.lower() in ('false', 'no', '0'):
                return False
            
            # Decimal
            try:
                return Decimal(value)
            except:
                pass
            
            # 其他情况保持字符串
            return value
        except Exception as e:
            logger.warning(f"无法将环境变量 {env_key}={value} 转换为适当类型: {str(e)}")
            return value
    
    # 默认值
    return default 