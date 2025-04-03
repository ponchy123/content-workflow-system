import logging
import time
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import DatabaseError
from redis.exceptions import RedisError
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.conf import settings
import traceback
from functools import wraps
from decimal import Decimal
from django.http import JsonResponse
import json
from typing import Optional, Any, Dict
from django.utils import timezone
from django.http import Http404
from rest_framework.exceptions import PermissionDenied, NotAuthenticated, AuthenticationFailed, MethodNotAllowed, NotAcceptable, UnsupportedMediaType, Throttled
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class BaseAPIException(APIException):
    """基础API异常类"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('发生未知错误')
    default_code = 'error'

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
            
        super().__init__(detail, code)

class InvalidParameterException(BaseAPIException):
    """参数验证错误"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('无效的参数')
    default_code = 'invalid_parameter'

class ResourceNotFoundException(BaseAPIException):
    """资源不存在错误"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('请求的资源不存在')
    default_code = 'not_found'

class PermissionDeniedException(BaseAPIException):
    """权限不足错误"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('没有足够的权限执行此操作')
    default_code = 'permission_denied'

class ConfigValidationException(BaseAPIException):
    """配置验证错误"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('配置验证失败')
    default_code = 'config_validation_error'

class CacheOperationException(BaseAPIException):
    """缓存操作错误"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _('缓存操作失败')
    default_code = 'cache_operation_error'

class DatabaseOperationException(BaseAPIException):
    """数据库操作错误"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _('数据库操作失败')
    default_code = 'database_operation_error'

class BusinessLogicException(BaseAPIException):
    """业务逻辑错误"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('业务逻辑错误')
    default_code = 'business_logic_error'

class ThirdPartyServiceException(BaseAPIException):
    """第三方服务错误"""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = _('第三方服务异常')
    default_code = 'third_party_service_error'

class RateLimitExceededException(BaseAPIException):
    """请求频率超限错误"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _('请求频率超出限制')
    default_code = 'rate_limit_exceeded'

class BaseCustomException(APIException):
    """基础自定义异常类"""
    def __init__(self, message, code=None, status_code=None):
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.status_code = status_code or status.HTTP_400_BAD_REQUEST
        self.detail = {'message': message, 'code': self.code}
        super().__init__(detail=self.detail)

class ValidationException(BaseCustomException):
    """验证异常"""
    def __init__(self, message):
        super().__init__(message, code='VALIDATION_ERROR', status_code=status.HTTP_400_BAD_REQUEST)

class ProductNotFoundException(BaseCustomException):
    """产品不存在异常"""
    def __init__(self, message):
        super().__init__(message, code='PRODUCT_NOT_FOUND', status_code=status.HTTP_404_NOT_FOUND)

class CacheException(BaseCustomException):
    """缓存异常"""
    def __init__(self, message):
        super().__init__(message, code='SERVICE_UNAVAILABLE', status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

class CalculationException(BaseCustomException):
    """计算异常"""
    def __init__(self, message):
        super().__init__(message, code='CALCULATION_ERROR', status_code=status.HTTP_400_BAD_REQUEST)

class DatabaseException(BaseCustomException):
    """数据库异常"""
    status_code = 500
    error_code = '500.03'
    default_detail = '数据库操作异常'
    default_code = 'database_error'

class BatchProcessingException(BaseCustomException):
    """批量处理异常"""
    status_code = 500
    default_code = 'BATCH_PROCESSING_ERROR'
    default_detail = '批量处理失败'

class CalculationTimeoutError(BaseCustomException):
    """计算超时异常"""
    status_code = 408
    default_code = 'CALCULATION_TIMEOUT'
    default_detail = '计算超时'

class ResourceLimitException(BaseCustomException):
    """资源限制异常"""
    status_code = 503
    default_code = 'RESOURCE_LIMIT_EXCEEDED'
    default_detail = '系统资源不足，请稍后再试'

class WeightRangeNotFoundException(ResourceNotFoundException):
    """重量范围未找到异常"""
    default_detail = _('请求的重量范围不存在')
    default_code = 'weight_range_not_found'

class WeightPointNotFoundException(CalculationException):
    """重量点不存在异常"""
    pass

class ZoneRateNotFoundException(ResourceNotFoundException):
    """区域费率未找到异常"""
    default_detail = _('请求的区域费率不存在')
    default_code = 'zone_rate_not_found'

class ZonePriceNotFoundException(ResourceNotFoundException):
    """区域价格未找到异常"""
    default_detail = _('请求的区域价格不存在')
    default_code = 'zone_price_not_found'

class DuplicateResourceException(BaseAPIException):
    """资源已存在异常"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('请求的资源已存在')
    default_code = 'resource_conflict'

def error_response(message, code='ERROR', http_status=status.HTTP_400_BAD_REQUEST, data=None):
    """返回统一格式的错误响应"""
    response_data = {
        'status': 'error',
        'code': code,
        'message': message,
        'data': data,
        'timestamp': timezone.now().isoformat()
    }
    return Response(response_data, status=http_status)

def get_error_response_data(message, code='ERROR', http_status=status.HTTP_400_BAD_REQUEST, data=None):
    """返回统一格式的错误响应数据和状态码，不返回Response对象"""
    response_data = {
        'status': 'error',
        'code': code,
        'message': message,
        'data': data,
        'timestamp': timezone.now().isoformat()
    }
    return response_data, http_status

def success_response(data=None, message="Success"):
    """
    标准成功响应格式
    """
    response_data = {
        'status': 'success',
        'code': 'SUCCESS',
        'message': message,
        'data': data if data is not None else {},
        'timestamp': timezone.now().isoformat()
    }
    return Response(response_data, status=status.HTTP_200_OK)

def custom_exception_handler(exc, context):
    """自定义异常处理器"""
    
    # 处理自定义异常
    if isinstance(exc, BaseCustomException):
        return Response({
            'status': 'error',
            'code': exc.code,
            'message': str(exc.message),
            'data': None,
            'timestamp': timezone.now().isoformat()
        }, status=exc.status_code)
    
    # 处理Django验证异常
    if isinstance(exc, ValidationError):
        if hasattr(exc, 'detail'):
            errors = exc.detail
        else:
            errors = exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
        
        return Response({
            'status': 'error',
            'code': 'VALIDATION_ERROR',
            'message': "验证错误",
            'errors': errors,
            'data': None,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 处理数据库异常
    if isinstance(exc, DatabaseError):
        logger.error(f"数据库错误: {str(exc)}")
        return Response({
            'status': 'error',
            'code': 'SERVICE_UNAVAILABLE',
            'message': "服务暂时不可用，请稍后重试",
            'data': None,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # 处理Redis异常
    if isinstance(exc, RedisError):
        logger.error(f"Redis错误: {str(exc)}")
        return Response({
            'status': 'error',
            'code': 'SERVICE_UNAVAILABLE',
            'message': "服务暂时不可用，请稍后重试",
            'data': None,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # 处理权限异常
    if isinstance(exc, PermissionDenied):
        return Response({
            'status': 'error',
            'code': 'FORBIDDEN',
            'message': "没有权限执行此操作",
            'data': None,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 处理认证异常
    if isinstance(exc, NotAuthenticated):
        return Response({
            'status': 'error',
            'code': 'UNAUTHORIZED',
            'message': "请先登录",
            'data': None,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # 处理方法不允许异常
    if isinstance(exc, MethodNotAllowed):
        return Response({
            'status': 'error',
            'code': 'METHOD_NOT_ALLOWED',
            'message': "不支持的请求方法",
            'data': None,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    # 处理其他DRF异常
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'status': 'error',
            'code': 'API_ERROR',
            'message': str(exc),
            'data': None,
            'timestamp': timezone.now().isoformat()
        }
        return response
    
    # 处理未预期的异常
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return Response({
        'status': 'error',
        'code': 'INTERNAL_SERVER_ERROR',
        'message': "服务器内部错误",
        'data': None,
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def handle_calculation_error(func):
    """计算异常处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            response_data, status_code = error_response(
                message=str(e),
                code='VALIDATION_ERROR',
                http_status=status.HTTP_400_BAD_REQUEST
            )
            response = Response(response_data, status=status_code)
            response.render()
            return response
        except InvalidParameterException as e:
            response_data, status_code = error_response(
                message=str(e),
                code='INVALID_PARAMETER',
                http_status=status.HTTP_400_BAD_REQUEST,
                data=getattr(e, 'data', None)
            )
            response = Response(response_data, status=status_code)
            response.render()
            return response
        except (ProductNotFoundException, WeightRangeNotFoundException, ZonePriceNotFoundException) as e:
            response_data, status_code = error_response(
                message=str(e),
                code='NOT_FOUND',
                http_status=status.HTTP_404_NOT_FOUND,
                data=getattr(e, 'data', None)
            )
            response = Response(response_data, status=status_code)
            response.render()
            return response
        except RedisError as e:
            logger.error(f"Redis error: {str(e)}")
            response_data, status_code = error_response(
                message='Cache service is temporarily unavailable',
                code='SERVICE_UNAVAILABLE',
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            response = Response(response_data, status=status_code)
            response.render()
            return response
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}")
            response_data, status_code = error_response(
                message='Database service is temporarily unavailable',
                code='SERVICE_UNAVAILABLE',
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            response = Response(response_data, status=status_code)
            response.render()
            return response
        except BaseCustomException as e:
            response_data, status_code = error_response(
                message=str(e),
                code=getattr(e, 'default_code', 'ERROR').upper(),
                http_status=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                data=getattr(e, 'data', None)
            )
            response = Response(response_data, status=status_code)
            response.render()
            return response
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}")
            response_data, status_code = error_response(
                message='An unexpected error occurred',
                code='INTERNAL_SERVER_ERROR',
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            response = Response(response_data, status=status_code)
            response.render()
            return response
    return wrapper

def mask_sensitive_data(data):
    """敏感信息屏蔽"""
    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            if key.lower() in ['password', 'token', 'secret']:
                masked_data[key] = '******'
            else:
                masked_data[key] = mask_sensitive_data(value)
        return masked_data
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data 

# 从 decorators.py 导入 db_connection_retry 装饰器
# 修改为延迟导入以避免循环导入问题
# from .decorators import db_connection_retry

# 上面的导入被注释掉了，需要在使用到db_connection_retry的地方进行延迟导入
# 比如可以在函数或类内部使用时再导入