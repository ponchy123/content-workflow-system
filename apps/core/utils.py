import uuid
import random
import string
import time
import signal
import threading
from functools import wraps
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING
from typing import Union, Dict, List, Any, Tuple, Callable, Optional
from datetime import datetime
import re
import logging
import pandas as pd
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.cache import cache
import json
from django.db import DatabaseError
from apps.core.exceptions import (
    InvalidParameterException,
    ProductNotFoundException,
    WeightRangeNotFoundException,
    ZonePriceNotFoundException,
    CalculationException,
    CalculationTimeoutError,
    WeightPointNotFoundException,
)
from apps.core.decorators import db_connection_retry
from .exceptions import CacheException
from rest_framework.response import Response
from rest_framework import status
from redis.exceptions import RedisError
from rest_framework.routers import DefaultRouter

logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """处理 Decimal 类型的 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

def json_dumps(obj: Any) -> str:
    """使用自定义编码器进行 JSON 序列化"""
    return json.dumps(obj, cls=DecimalEncoder)

def json_loads(s: str) -> Any:
    """JSON 反序列化，支持 Decimal 类型"""
    def decimal_hook(dct):
        for k, v in dct.items():
            if isinstance(v, str):
                try:
                    dct[k] = Decimal(v)
                except (InvalidOperation, ValueError):
                    pass
        return dct
    return json.loads(s, object_hook=decimal_hook)

def generate_request_id(prefix: str = '') -> str:
    """
    生成唯一的请求ID
    Args:
        prefix: ID前缀
    Returns:
        str: 请求ID
    """
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"

def get_client_ip(request) -> str:
    """
    获取客户端IP地址
    
    Args:
        request: HTTP请求对象
        
    Returns:
        str: 客户端IP地址
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def mask_sensitive_data(data: Union[Dict, List, Any], 
                       sensitive_fields: set = None) -> Union[Dict, List, Any]:
    """
    遮蔽敏感数据
    
    Args:
        data: 要处理的数据，可以是字典、列表或其他类型
        sensitive_fields: 敏感字段集合，默认包含常见敏感字段
        
    Returns:
        处理后的数据
    """
    if sensitive_fields is None:
        sensitive_fields = {'password', 'token', 'secret', 'credit_card', 'api_key'}
        
    if isinstance(data, dict):
        return {
            k: '******' if k in sensitive_fields else 
               mask_sensitive_data(v, sensitive_fields) if isinstance(v, (dict, list)) else v
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, sensitive_fields) if isinstance(item, (dict, list)) else item 
               for item in data]
    return data 

def validate_postal_code(postal_code: str) -> bool:
    """
    验证邮政编码格式
    Args:
        postal_code: 邮政编码
    Returns:
        bool: 是否有效
    """
    if not postal_code:
        return False
    postal_code = postal_code.strip()
    # 支持美国邮编格式：5位数字或9位数字（带连字符）
    return bool(re.match(r'^\d{5}(-\d{4})?$', postal_code))

def validate_weight(weight: Union[str, int, float, Decimal]) -> Decimal:
    """
    验证并转换重量值
    Args:
        weight: 重量值
    Returns:
        Decimal: 转换后的重量
    Raises:
        ValueError: 重量无效
    """
    try:
        weight = Decimal(str(weight))
        if weight <= 0:
            raise ValueError("重量必须大于0")
        return weight
    except (TypeError, ValueError):
        raise ValueError("重量格式无效")

def format_currency(amount: Decimal, currency: str = 'CNY', decimal_places: int = 2) -> str:
    """
    格式化货币金额
    Args:
        amount: 金额
        currency: 货币代码
        decimal_places: 小数位数
    Returns:
        str: 格式化后的金额
    """
    return f"{amount:.{decimal_places}f} {currency}"

def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串
    Args:
        date_str: 日期字符串
    Returns:
        datetime: 日期对象
    Raises:
        ValueError: 日期格式无效
    """
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y%m%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError("无效的日期格式")

def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    Args:
        phone: 手机号
    Returns:
        bool: 是否有效
    """
    return bool(re.match(r'^1[3-9]\d{9}$', phone.strip()))

def validate_email_address(email: str) -> bool:
    """
    验证邮箱地址
    Args:
        email: 邮箱地址
    Returns:
        bool: 是否有效
    """
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    将列表分块
    Args:
        lst: 原始列表
        chunk_size: 块大小
    Returns:
        List[List]: 分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def safe_divide(a: Union[int, float, Decimal], b: Union[int, float, Decimal], default: Union[int, float, Decimal] = 0) -> Union[int, float, Decimal]:
    """
    安全除法
    Args:
        a: 被除数
        b: 除数
        default: 默认值
    Returns:
        Union[int, float, Decimal]: 计算结果
    """
    try:
        return a / b if b != 0 else default
    except (TypeError, ValueError):
        return default

def format_file_size(size_in_bytes: int) -> str:
    """
    格式化文件大小
    Args:
        size_in_bytes: 文件大小（字节）
    Returns:
        str: 格式化后的大小
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"

def is_valid_id_card(id_card: str) -> bool:
    """
    验证身份证号
    Args:
        id_card: 身份证号
    Returns:
        bool: 是否有效
    """
    if not id_card:
        return False
        
    id_card = id_card.strip()
    
    # 18位身份证
    if len(id_card) == 18:
        return True
    return False

def get_age_from_id_card(id_card: str) -> int:
    """
    从身份证号获取年龄
    Args:
        id_card: 身份证号
    Returns:
        int: 年龄
    Raises:
        ValueError: 身份证号无效
    """
    if not is_valid_id_card(id_card):
        raise ValueError("无效的身份证号")
        
    if len(id_card) == 18:
        birth_year = int(id_card[6:10])
        birth_month = int(id_card[10:12])
        birth_day = int(id_card[12:14])
    else:  # 15位
        birth_year = int('19' + id_card[6:8])
        birth_month = int(id_card[8:10])
        birth_day = int(id_card[10:12])
        
    birth_date = datetime(birth_year, birth_month, birth_day)
    today = datetime.now()
    
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
        
    return age

def mask_sensitive_info(text: str, mask_char: str = '*') -> str:
    """
    掩码敏感信息
    Args:
        text: 原始文本
        mask_char: 掩码字符
    Returns:
        str: 掩码后的文本
    """
    if not text:
        return text
        
    text = str(text).strip()
    length = len(text)
    
    if length <= 4:
        return mask_char * length
    elif length <= 8:
        return text[:2] + mask_char * (length - 4) + text[-2:]
    else:
        return text[:3] + mask_char * (length - 6) + text[-3:]

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    错误重试装饰器
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise e
                    logger.warning(f"函数 {func.__name__} 执行失败，正在进行第 {retries} 次重试")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator 

def preprocess_calculation_data(data):
    """
    预处理计算数据，进行数据验证和清洗
    
    Args:
        data: 字典或DataFrame类型的输入数据
        
    Returns:
        处理后的数据和错误信息列表
    
    Raises:
        InvalidParameterException: 当输入数据无效时抛出
    """
    errors = []
    
    if isinstance(data, dict):
        # 验证必填字段
        required_fields = ['length', 'width', 'height', 'weight', 'from_postal']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise InvalidParameterException(f'缺少必填字段: {", ".join(missing_fields)}')
            
        # 验证数值字段
        numeric_fields = ['length', 'width', 'height', 'weight']
        for field in numeric_fields:
            try:
                value = Decimal(str(data[field]))
                if value <= 0:
                    raise InvalidParameterException(f'{field}必须大于0')
                data[field] = value
            except (TypeError, ValueError):
                raise InvalidParameterException(f'{field}必须是有效的数值')
                
        # 验证邮政编码
        if not validate_postal_code(data['from_postal']):
            raise InvalidParameterException('无效的始发地邮编')
        if 'to_postal' in data and not validate_postal_code(data['to_postal']):
            raise InvalidParameterException('无效的目的地邮编')
            
        # 处理可选字段
        data['declared_value'] = Decimal(str(data.get('declared_value', '0')))
        
        return data, errors
        
    elif isinstance(data, pd.DataFrame):
        if data.empty:
            raise InvalidParameterException('输入数据不能为空')
            
        # 验证必填字段
        required_columns = ['length', 'width', 'height', 'weight', 'from_postal']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise InvalidParameterException(f'缺少必填列: {", ".join(missing_columns)}')
            
        # 验证数值列
        numeric_columns = ['length', 'width', 'height', 'weight']
        for col in numeric_columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            invalid_rows = data[data[col].isna() | (data[col] <= 0)].index
            if not invalid_rows.empty:
                errors.extend([f'第{i+1}行: {col}必须大于0' for i in invalid_rows])
                data = data.drop(invalid_rows)
                
        # 验证邮政编码
        invalid_from_postal = ~data['from_postal'].apply(validate_postal_code)
        if invalid_from_postal.any():
            errors.extend([f'第{i+1}行: 无效的始发地邮编' for i in data[invalid_from_postal].index])
            data = data[~invalid_from_postal]
            
        if 'to_postal' in data.columns:
            invalid_to_postal = ~data['to_postal'].apply(validate_postal_code)
            if invalid_to_postal.any():
                errors.extend([f'第{i+1}行: 无效的目的地邮编' for i in data[invalid_to_postal].index])
                data = data[~invalid_to_postal]
                
        # 处理可选字段
        if 'declared_value' not in data.columns:
            data['declared_value'] = 0
        data['declared_value'] = pd.to_numeric(data['declared_value'], errors='coerce').fillna(0)
        
        # 删除重复行
        duplicates = data.duplicated(subset=['length', 'width', 'height', 'weight', 'from_postal', 'to_postal'], keep='first')
        if duplicates.any():
            errors.extend([f'第{i+1}行: 重复记录' for i in data[duplicates].index])
            data = data[~duplicates]
            
        if data.empty:
            raise InvalidParameterException('所有记录都无效')
            
        return data, errors
        
    else:
        raise InvalidParameterException('不支持的数据类型')

def validate_decimal(value: Union[str, float, Decimal, None], field_name: str) -> Decimal:
    """
    验证并转换为 Decimal 类型
    Args:
        value: 要验证的值
        field_name: 字段名称
    Returns:
        Decimal: 转换后的值
    Raises:
        InvalidParameterException: 当值无效时
    """
    try:
        if value is None:
            raise InvalidParameterException(f'{field_name} is required')
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise InvalidParameterException(f'{field_name} cannot be empty')
        
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise InvalidParameterException(f'{field_name} must be greater than 0')
        
        return decimal_value
    except (TypeError, ValueError, InvalidOperation) as e:
        raise InvalidParameterException(f'{field_name}格式无效')

@db_connection_retry(max_retries=3, retry_delay=0.5)
def log_audit(user, action: str, content_type: str, object_id: str, object_repr: str,
              change_message: dict, ip_addr: str = None, user_agent: str = None,
              risk_level: str = 'LOW', module: str = None, status: str = 'SUCCESS',
              error_message: str = None, duration: float = 0.0) -> None:
    """
    记录审计日志
    
    Args:
        user: 操作用户
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
    from .models import AuditLog
    try:
        # 确保 change_message 是 JSON 可序列化的
        if isinstance(change_message, dict):
            change_message = json_dumps(change_message)
        
        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            change_message=change_message,
            ip_addr=ip_addr or '0.0.0.0',
            user_agent=user_agent or '',
            risk_level=risk_level,
            module=module,
            status=status,
            error_message=error_message,
            duration=duration
        )
    except Exception as e:
        logger.error(f"审计日志记录失败: {str(e)}") 

def validate_calculation_input(data: dict) -> None:
    """
    验证计算输入数据
    Args:
        data: 输入数据字典
    Raises:
        InvalidParameterException: 当输入数据无效时抛出
    """
    required_fields = ['product_id', 'weight', 'from_postal']
    for field in required_fields:
        if field not in data:
            raise InvalidParameterException(f"缺少必填字段: {field}")
    
    # 验证重量
    try:
        weight = Decimal(str(data['weight']))
        if weight <= 0:
            raise InvalidParameterException("重量必须大于0")
    except (InvalidOperation, TypeError):
        raise InvalidParameterException("重量格式无效")
    
    # 验证尺寸（如果提供）
    dimensions = ['length', 'width', 'height']
    for dim in dimensions:
        if dim in data:
            try:
                value = Decimal(str(data[dim]))
                if value <= 0:
                    raise InvalidParameterException(f"{dim}必须大于0")
            except (InvalidOperation, TypeError):
                raise InvalidParameterException(f"{dim}格式无效")

def calculate_volume_weight(
    length: Union[Decimal, float, int, str],
    width: Union[Decimal, float, int, str],
    height: Union[Decimal, float, int, str],
    factor: Union[Decimal, float, int, str],
    dimension_unit: str = 'CM',
    weight_unit: str = 'KG'
) -> Decimal:
    """
    计算体积重量
    
    Args:
        length: 长度
        width: 宽度
        height: 高度
        factor: 体积重系数
        dimension_unit: 尺寸单位(CM/IN)
        weight_unit: 重量单位(KG/LB)
    
    Returns:
        Decimal: 体积重量
    """
    try:
        # 转换为Decimal
        length = Decimal(str(length))
        width = Decimal(str(width))
        height = Decimal(str(height))
        factor = Decimal(str(factor))
        
        # 确保所有输入值都大于0
        if any(x <= 0 for x in [length, width, height, factor]):
            raise ValueError("长度、宽度、高度和系数必须大于0")
            
        # 如果输入是厘米，需要转换为英寸
        if dimension_unit.upper() == 'CM':
            # 1 inch = 2.54 cm
            cm_to_in = Decimal('2.54')
            length = (length / cm_to_in).quantize(Decimal('1'), rounding=ROUND_CEILING)
            width = (width / cm_to_in).quantize(Decimal('1'), rounding=ROUND_CEILING)
            height = (height / cm_to_in).quantize(Decimal('1'), rounding=ROUND_CEILING)
            
        # 计算体积重量 (L*W*H/factor)
        volume_weight = (length * width * height / factor).quantize(Decimal('1'), rounding=ROUND_CEILING)
        
        # 如果需要输出KG但factor是按LB计算的，需要转换
        if weight_unit.upper() == 'KG' and factor == Decimal('250'):
            # 1 kg = 2.20462262 lb
            volume_weight = (volume_weight / Decimal('2.20462262')).quantize(Decimal('1'), rounding=ROUND_CEILING)
            
        return volume_weight
        
    except (TypeError, ValueError, InvalidOperation) as e:
        logger.error(f"计算体积重量时出错: {str(e)}")
        raise ValueError(f"计算体积重量失败: {str(e)}")

def calculate_chargeable_weight(actual_weight: Decimal, volume_weight: Decimal = None) -> Decimal:
    """
    计算计费重量
    Args:
        actual_weight: 实际重量
        volume_weight: 体积重
    Returns:
        Decimal: 计费重量
    """
    if volume_weight:
        return max(actual_weight, volume_weight).quantize(Decimal('0.01'))
    return actual_weight.quantize(Decimal('0.01'))

def calculate_surcharge(base_fee: Decimal, rate: Decimal) -> Decimal:
    """
    计算附加费
    Args:
        base_fee: 基础费用
        rate: 费率（百分比）
    Returns:
        Decimal: 附加费金额
    """
    return (base_fee * rate / Decimal('100')).quantize(Decimal('0.01'))

def round_fee(amount: Decimal, precision: int = 2) -> Decimal:
    """
    对金额进行四舍五入
    Args:
        amount: 金额
        precision: 精度，默认2位小数
    Returns:
        Decimal: 四舍五入后的金额
    """
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def timeout_decorator(timeout_seconds):
    """
    超时装饰器，用于限制函数执行时间
    
    Args:
        timeout_seconds: 超时时间（秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 定义超时处理函数
            def handle_timeout(signum, frame):
                raise CalculationTimeoutError(f"函数执行超时（{timeout_seconds}秒）")
            
            # 检查平台是否支持信号
            use_signal = hasattr(signal, 'SIGALRM')
            timeout_thread = None
            
            if use_signal:
                # 使用信号实现超时
                old_handler = signal.signal(signal.SIGALRM, handle_timeout)
                signal.alarm(timeout_seconds)
                try:
                    return func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # 使用线程实现超时（Windows平台）
                result = {"value": None, "exception": None}
                
                def target():
                    try:
                        result["value"] = func(*args, **kwargs)
                    except Exception as e:
                        result["exception"] = e
                
                timeout_thread = threading.Thread(target=target)
                timeout_thread.daemon = True
                timeout_thread.start()
                timeout_thread.join(timeout_seconds)
                
                if timeout_thread.is_alive():
                    # 超时
                    raise CalculationTimeoutError(f"函数执行超时（{timeout_seconds}秒）")
                
                if result["exception"]:
                    raise result["exception"]
                    
                return result["value"]
                
        return wrapper
    return decorator

class CacheService:
    """统一的缓存服务类"""
    
    def __init__(self, prefix: str = '', timeout: int = 3600):
        self.prefix = prefix
        self.default_timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.cache_hits = 0
        self.cache_misses = 0
        self._local_cache = {}
        self._local_cache_hits = 0
        self._local_cache_misses = 0

    def get_cache_key(self, key_type: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [self.prefix, key_type]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ':'.join(key_parts)

    def get_cached_data(self, cache_key: str, fetch_func: Callable, *args, **kwargs) -> Any:
        """获取缓存数据，如果不存在则调用fetch_func获取并缓存"""
        data = self._get_from_cache(cache_key)
        if data is not None:
            self._update_cache_stats(hit=True)
            return data

        self._update_cache_stats(hit=False)
        data = fetch_func(*args, **kwargs)
        if data is not None:
            self._set_to_cache(cache_key, data)
        return data

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存中获取数据"""
        try:
            # 先从本地缓存获取
            if key in self._local_cache:
                self._local_cache_hits += 1
                return self._local_cache[key]
            
            self._local_cache_misses += 1
            # 从Redis缓存获取
            data = cache.get(key)
            if data is not None:
                # 更新本地缓存
                self._local_cache[key] = data
            return data
        except Exception as e:
            self.logger.error(f"从缓存获取数据失败: {str(e)}")
            return None

    def _set_to_cache(self, key: str, value: Any, timeout: int = None) -> bool:
        """设置缓存数据"""
        try:
            timeout = timeout or self.default_timeout
            # 更新Redis缓存
            cache.set(key, value, timeout)
            # 更新本地缓存
            self._local_cache[key] = value
            self._check_local_cache_size()
            return True
        except Exception as e:
            self.logger.error(f"设置缓存数据失败: {str(e)}")
            return False

    def invalidate_cache(self, key: str) -> bool:
        """清除缓存"""
        try:
            # 清除Redis缓存
            cache.delete(key)
            # 清除本地缓存
            self._local_cache.pop(key, None)
            return True
        except Exception as e:
            self.logger.error(f"清除缓存失败: {str(e)}")
            return False

    def _check_local_cache_size(self, max_size: int = 1000):
        """检查并清理本地缓存大小"""
        if len(self._local_cache) > max_size:
            # 清除20%的缓存
            remove_count = int(max_size * 0.2)
            for _ in range(remove_count):
                self._local_cache.pop(next(iter(self._local_cache)))

    def _update_cache_stats(self, hit: bool):
        """更新缓存统计信息"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'local_hits': self._local_cache_hits,
            'local_misses': self._local_cache_misses,
            'local_cache_size': len(self._local_cache)
        } 

class BaseCalculationService:
    """基础计算服务类，提供通用的计算功能"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_service = CacheService(prefix='calc')
        self.cache_hits = 0
        self.cache_misses = 0

    def validate_input(self, data: Dict[str, Any]) -> None:
        """验证输入数据"""
        validate_calculation_input(data)

    def calculate_volume_weight(self, length: Decimal, width: Decimal, height: Decimal, factor: Decimal, 
                              dimension_unit: str = 'CM', weight_unit: str = 'KG') -> Decimal:
        """计算体积重"""
        return calculate_volume_weight(length, width, height, factor, dimension_unit, weight_unit)

    def calculate_chargeable_weight(self, actual_weight: Decimal, volume_weight: Decimal = None) -> Decimal:
        """计算计费重量"""
        return calculate_chargeable_weight(actual_weight, volume_weight)

    def calculate_surcharge(self, base_amount: Decimal, rate: Decimal) -> Decimal:
        """计算附加费"""
        return calculate_surcharge(base_amount, rate)

    def preprocess_calculation_data(self, data: Union[Dict, pd.DataFrame]) -> Tuple[Union[Dict, pd.DataFrame], List[str]]:
        """预处理计算数据"""
        return preprocess_calculation_data(data)

    def format_calculation_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化计算结果"""
        formatted = {}
        for key, value in result.items():
            if isinstance(value, Decimal):
                formatted[key] = str(value.quantize(Decimal('0.01')))
            elif isinstance(value, (list, dict)):
                formatted[key] = value
            else:
                formatted[key] = str(value)
        return formatted

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def log_calculation(self, request_data: Dict[str, Any], result: Dict[str, Any], 
                       user=None, ip_addr=None, user_agent=None) -> None:
        """
        记录计算日志
        """
        from .models import CalculationLog
        try:
            CalculationLog.objects.create(
                user=user,
                request_data=request_data,
                result=result,
                ip_addr=ip_addr,
                user_agent=user_agent,
                status='SUCCESS' if result.get('success') else 'ERROR',
                error_message=result.get('error'),
                duration=result.get('duration', 0.0)
            )
        except Exception as e:
            self.logger.error(f"记录计算日志失败: {str(e)}")

    def handle_calculation_error(self, e: Exception, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理计算错误"""
        error_message = str(e)
        self.logger.error(f"计算失败: {error_message}", exc_info=True)
        
        result = {
            'status': 'FAILED',
            'error_message': error_message,
            'request_id': generate_request_id('ERR'),
            'request_data': request_data,
            'calculation_time': 0
        }
        
        # 记录错误日志
        self.log_calculation(request_data, result)
        
        return result

    def validate_weight(self, weight: Union[str, Decimal, float]) -> Decimal:
        """验证并转换重量"""
        try:
            weight = Decimal(str(weight))
            if weight <= 0:
                raise InvalidParameterException("重量必须大于0")
            return weight
        except (InvalidOperation, TypeError):
            raise InvalidParameterException("重量格式无效")

    def validate_dimensions(self, data: Dict[str, Any]) -> Dict[str, Decimal]:
        """验证并转换尺寸数据"""
        dimensions = {}
        for dim in ['length', 'width', 'height']:
            if dim in data:
                try:
                    value = Decimal(str(data[dim]))
                    if value <= 0:
                        raise InvalidParameterException(f"{dim}必须大于0")
                    dimensions[dim] = value
                except (InvalidOperation, TypeError):
                    raise InvalidParameterException(f"{dim}格式无效")
        return dimensions

    def validate_postal_codes(self, from_postal: str, to_postal: str = None) -> None:
        """验证邮政编码"""
        if not from_postal:
            raise InvalidParameterException("始发地邮编不能为空")
        if not validate_postal_code(from_postal):
            raise InvalidParameterException(f"始发地邮编无效: {from_postal}")
        if to_postal and not validate_postal_code(to_postal):
            raise InvalidParameterException(f"目的地邮编无效: {to_postal}")

    def validate_declared_value(self, value: Union[str, Decimal, float, None]) -> Optional[Decimal]:
        """验证并转换申报价值"""
        if value is None:
            return None
        try:
            value = Decimal(str(value))
            if value < 0:
                raise InvalidParameterException("申报价值不能为负数")
            return value
        except (InvalidOperation, TypeError):
            raise InvalidParameterException("申报价值格式无效")

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'cache_size': len(self.cache_service._local_cache)
        }

    def clear_cache(self) -> None:
        """清除缓存"""
        self.cache_service._local_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

    def update_cache_stats(self, hit: bool) -> None:
        """更新缓存统计信息"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

def success_response(data=None, message=None, http_status=200):
    """
    生成统一的成功响应格式
    
    Args:
        data: 响应数据
        message: 响应消息
        http_status: HTTP状态码
        
    Returns:
        tuple: (response_dict, http_status)
    """
    response = {
        'status': 'success',
        'code': 'SUCCESS',
        'message': message or 'Success',
        'data': data if data is not None else {},
        'timestamp': timezone.now().isoformat()
    }
    return response, http_status

def error_response(message, code='ERROR', http_status=status.HTTP_400_BAD_REQUEST):
    """
    生成统一的错误响应格式
    
    Args:
        message: 错误消息
        code: 错误代码
        http_status: HTTP状态码
        
    Returns:
        tuple: (response_dict, http_status)
    """
    response_data = {
        'status': 'error',
        'code': code,
        'message': message,
        'data': {},
        'timestamp': timezone.now().isoformat()
    }
    return response_data, http_status

def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    
    Args:
        exc: 异常对象
        context: 上下文信息
        
    Returns:
        Response: 处理后的响应对象
    """
    if isinstance(exc, ValidationError):
        response_data = {
            'status': 'error',
            'code': 'VALIDATION_ERROR',
            'message': str(exc.detail),
            'error': str(exc.detail),
            'data': {},
            'timestamp': timezone.now().isoformat()
        }
        return response_data, status.HTTP_400_BAD_REQUEST
    
    if isinstance(exc, InvalidParameterException):
        response_data = {
            'status': 'error',
            'code': 'INVALID_PARAMETER',
            'message': str(exc),
            'error': str(exc),
            'data': {},
            'timestamp': timezone.now().isoformat()
        }
        return response_data, status.HTTP_400_BAD_REQUEST
    
    if isinstance(exc, ProductNotFoundException):
        response_data = {
            'status': 'error',
            'code': 'NOT_FOUND',
            'message': str(exc),
            'error': str(exc),
            'data': {},
            'timestamp': timezone.now().isoformat()
        }
        return response_data, status.HTTP_404_NOT_FOUND
    
    if isinstance(exc, WeightRangeNotFoundException) or isinstance(exc, WeightPointNotFoundException):
        return error_response('未找到适用的重量段，请检查重量输入是否合法。', 'WEIGHT_RANGE_NOT_FOUND', status.HTTP_404_NOT_FOUND)
    
    if isinstance(exc, ZonePriceNotFoundException):
        response_data = {
            'status': 'error',
            'code': 'NOT_FOUND',
            'message': str(exc),
            'error': str(exc),
            'data': {},
            'timestamp': timezone.now().isoformat()
        }
        return response_data, status.HTTP_404_NOT_FOUND
    
    if isinstance(exc, (DatabaseError, RedisError)):
        response_data = {
            'status': 'error',
            'code': 'SERVICE_UNAVAILABLE',
            'message': "Service temporarily unavailable",
            'error': str(exc),
            'data': {},
            'timestamp': timezone.now().isoformat()
        }
        return response_data, status.HTTP_503_SERVICE_UNAVAILABLE
    
    # Default error handling
    response_data = {
        'status': 'error',
        'code': 'INTERNAL_ERROR',
        'message': "Internal server error",
        'error': str(exc),
        'data': {},
        'timestamp': timezone.now().isoformat()
    }
    return response_data, status.HTTP_500_INTERNAL_SERVER_ERROR

def get_router():
    """
    返回统一配置的DefaultRouter实例
    
    由于项目设置了APPEND_SLASH=False，所以路由器也要设置trailing_slash=False
    以确保API URL格式一致性
    """
    return DefaultRouter(trailing_slash=False) 