from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from typing import Dict, Any, Optional, List, Union

class APIResponse:
    """API响应工具类"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", extra_fields: Dict = None) -> Response:
        """成功响应"""
        response_data = {
            'status': 'success',
            'code': 'SUCCESS',
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
        if extra_fields:
            response_data.update(extra_fields)
        return Response(response_data, status=status.HTTP_200_OK)
    
    @staticmethod
    def error(message: str, code: str = "ERROR", status_code: int = status.HTTP_400_BAD_REQUEST, data: Any = None) -> Response:
        """错误响应"""
        response_data = {
            'status': 'error',
            'code': code,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
        return Response(response_data, status=status_code)
    
    @staticmethod
    def validation_error(errors: Union[Dict, List, str], message: str = "验证错误") -> Response:
        """验证错误响应"""
        response_data = {
            'status': 'error',
            'code': 'VALIDATION_ERROR',
            'message': message,
            'errors': errors,
            'data': None,
            'timestamp': timezone.now().isoformat()
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    @staticmethod
    def not_found(message: str = "资源不存在", code: str = "NOT_FOUND") -> Response:
        """资源不存在响应"""
        return APIResponse.error(
            message=message, 
            code=code, 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def server_error(message: str = "服务器内部错误") -> Response:
        """服务器错误响应"""
        return APIResponse.error(
            message=message,
            code='INTERNAL_SERVER_ERROR',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def unauthorized(message: str = "未授权访问") -> Response:
        """未授权响应"""
        return APIResponse.error(
            message=message,
            code='UNAUTHORIZED',
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(message: str = "禁止访问") -> Response:
        """禁止访问响应"""
        return APIResponse.error(
            message=message,
            code='FORBIDDEN',
            status_code=status.HTTP_403_FORBIDDEN
        )

    @staticmethod
    def service_unavailable(message: str = "服务暂时不可用") -> Response:
        """服务不可用响应"""
        return APIResponse.error(
            message=message,
            code='SERVICE_UNAVAILABLE',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    @staticmethod
    def create_response(status_value: str, code: str, message: str, data: Any = None, 
                        status_code: int = status.HTTP_200_OK) -> Response:
        """创建自定义格式响应"""
        response_data = {
            'status': status_value,
            'code': code,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
        return Response(response_data, status=status_code)

# 为了兼容旧代码，保留这些函数
def success_response(data=None, message="Success"):
    return APIResponse.success(data, message)

def error_response(message, code='ERROR', status_code=status.HTTP_400_BAD_REQUEST, data=None):
    return APIResponse.error(message, code, status_code, data) 