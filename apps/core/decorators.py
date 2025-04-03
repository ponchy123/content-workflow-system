import time
import logging
import functools
import psutil
from django.conf import settings
from django.utils import timezone
from .exceptions import ResourceLimitException
from django.db import DatabaseError

logger = logging.getLogger(__name__)

def performance_monitor(func):
    """
    性能监控装饰器，记录函数执行时间和资源使用情况
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # 获取函数名称
            func_name = func.__qualname__
            
            # 记录性能指标
            logger.info(
                f"性能监控 - 函数: {func_name}, "
                f"执行时间: {execution_time:.4f}秒, "
                f"内存使用: {memory_delta:.2f}MB"
            )
            
            # 如果执行时间超过阈值，记录警告
            slow_threshold = getattr(settings, 'SLOW_FUNCTION_THRESHOLD', 1.0)
            if execution_time > slow_threshold:
                logger.warning(
                    f"性能警告 - 函数: {func_name}, "
                    f"执行时间: {execution_time:.4f}秒, "
                    f"超过阈值: {slow_threshold}秒"
                )
    
    return wrapper

def resource_check(func):
    """
    资源检查装饰器，检查系统资源使用情况，如果超过阈值则拒绝执行
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        
        # 获取阈值设置
        cpu_threshold = getattr(settings, 'CPU_THRESHOLD', 90)
        memory_threshold = getattr(settings, 'MEMORY_THRESHOLD', 90)
        enforce_limits = getattr(settings, 'ENFORCE_RESOURCE_LIMITS', True)
        
        # 检查CPU使用率
        if cpu_percent > cpu_threshold:
            message = f"CPU使用率过高: {cpu_percent}% > {cpu_threshold}%"
            logger.warning(f"资源限制 - {message}")
            if enforce_limits:
                raise ResourceLimitException(message)
        
        # 检查内存使用率
        if memory_percent > memory_threshold:
            message = f"内存使用率过高: {memory_percent}% > {memory_threshold}%"
            logger.warning(f"资源限制 - {message}")
            if enforce_limits:
                raise ResourceLimitException(message)
        
        # 资源检查通过，执行函数
        return func(*args, **kwargs)
    
    return wrapper

def monitor_performance(name=None):
    """
    性能监控装饰器，兼容旧版本的monitor_performance
    
    Args:
        name: 操作名称，用于日志记录
        
    Returns:
        装饰器函数
    """
    # 处理不带参数的调用
    if callable(name):
        return performance_monitor(name)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                logger.info(f"操作: {operation}, 执行时间: {execution_time:.4f}秒")
        
        return wrapper
    
    return decorator

def db_connection_retry(max_retries=3, retry_delay=0.5):
    """
    数据库连接重试装饰器
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟时间（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except DatabaseError as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"数据库操作失败，已达到最大重试次数: {str(e)}")
                        raise
                    logger.warning(f"数据库操作失败，正在进行第{retries}次重试: {str(e)}")
                    time.sleep(retry_delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator 