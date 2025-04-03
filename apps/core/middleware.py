from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.conf import settings
from django.db import connection, reset_queries, connections
from .models import AuditLog, RequestLog, ResponseLog
from .utils import get_client_ip, mask_sensitive_data
from .exceptions import (
    BaseCustomException, ValidationException, InvalidParameterException,
    DatabaseException, CacheException, ResourceLimitException, CalculationTimeoutError
)
from .decorators import db_connection_retry
import json
import time
import logging
from django.utils import timezone
import psutil
from django.http import JsonResponse, HttpResponseServerError, HttpResponse
from rest_framework import status
from django.db import DatabaseError
from redis.exceptions import RedisError
from rest_framework.exceptions import (
    ValidationError, NotAuthenticated, AuthenticationFailed,
    PermissionDenied, NotFound, MethodNotAllowed
)
from .responses import APIResponse
from django.core.cache import cache
from typing import Optional, Dict, Any, List
import random
import threading
from rest_framework.views import exception_handler
from .exceptions import BaseAPIException
import traceback
from rest_framework.exceptions import APIException
from datetime import datetime
import re
import uuid
import hashlib
from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.middleware import get_user
import os
from urllib.parse import urlparse
import asyncio

# 添加新的NoCacheMiddleware中间件
class NoCacheMiddleware:
    """
    中间件，用于确保响应不被浏览器缓存。
    对于登录页面和认证相关的接口特别有用。
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # 需要应用no-cache头的路径前缀列表
        self.no_cache_paths = [
            '/api/v1/users/token/',
            '/api/v1/users/login/',
            '/api/v1/users/logout/',
            '/api/v1/users/refresh/',
            '/api/v1/users/me/',
            '/api/auth/',
            '/login',
            '/logout'
        ]
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # 检查当前请求路径是否需要应用no-cache头
        path = request.path
        
        # 对API或认证相关的路径应用no-cache头
        if any(path.startswith(prefix) for prefix in self.no_cache_paths):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            print(f"已为路径 {path} 应用no-cache头")
            
        return response

# 延迟导入User模型，避免循环导入
# User = get_user_model()
logger = logging.getLogger(__name__)

# 配置日志记录器
request_logger = logging.getLogger('freight.request')

# 设置全局请求超时（秒）
REQUEST_TIMEOUT = getattr(settings, 'REQUEST_TIMEOUT', 5)
# 设置全局数据库查询限制
MAX_DB_QUERIES = getattr(settings, 'MAX_DB_QUERIES', 100)
# 设置内存使用限制（MB）
MAX_MEMORY_USAGE = getattr(settings, 'MAX_MEMORY_USAGE', 500)

# 当前进程ID
PROCESS_ID = os.getpid()
PROCESS = psutil.Process(PROCESS_ID)

# 安全检查工具函数
def check_user_authenticated(request):
    """安全检查request.user是否存在且已认证"""
    # 检查是否正在进行认证处理，避免递归
    if getattr(request, '_jwt_auth_in_progress', False):
        return False
        
    # 检查request是否有user属性
    if not hasattr(request, 'user'):
        return False
        
    # 检查user对象是否存在
    if request.user is None:
        return False
        
    # 检查user对象是否有is_authenticated属性
    if not hasattr(request.user, 'is_authenticated'):
        return False
        
    # 检查用户是否已认证    
    return request.user.is_authenticated

class ExceptionMiddleware:
    """异常处理中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)

    def handle_exception(self, request, exception):
        """处理异常并返回适当的响应"""
        # 添加超时控制
        if isinstance(exception, TimeoutError):
            logger.error(f"请求超时: {request.path}")
            return APIResponse.error(
                message="请求处理超时，请稍后重试",
                code="REQUEST_TIMEOUT",
                status_code=status.HTTP_408_REQUEST_TIMEOUT
            )
            
        if isinstance(exception, CalculationTimeoutError):
            logger.error(f"计算超时: {request.path}")
            return APIResponse.error(
                message=str(exception),
                code=exception.default_code,
                status_code=exception.status_code
            )
            
        if isinstance(exception, ResourceLimitException):
            logger.error(f"资源限制异常: {request.path} - {str(exception)}")
            return APIResponse.service_unavailable(
                message=str(exception)
            )

        if isinstance(exception, BaseCustomException):
            logger.warning(f"业务异常: {str(exception)}")
            return APIResponse.error(
                message=str(exception),
                code=exception.code,
                status_code=exception.status_code
            )

        if isinstance(exception, ValidationError):
            logger.warning(f"验证错误: {str(exception)}")
            return APIResponse.validation_error(errors=exception.detail)

        # 处理认证异常 - 监控接口特殊处理
        if isinstance(exception, NotAuthenticated):
            # 检查是否是监控接口，允许匿名访问
            path = request.path.lstrip('/')
            # 处理可能存在的代理请求
            requested_url = request.META.get('HTTP_HOST', '') + request.path
            print(f"代理请求: {request.path}")
            
            if ('monitoring' in path or 'monitoring' in request.path or 
                getattr(request, '_allow_anonymous_for_monitoring', False) or
                'monitoring' in requested_url):
                logger.info(f"监控接口允许匿名访问: {path}")
                return APIResponse.success(message="监控数据已记录")
            
            return APIResponse.unauthorized(message="请先登录")

        if isinstance(exception, DatabaseError):
            # 检查是否为数据库连接断开错误
            error_message = str(exception)
            if "Lost connection" in error_message:
                logger.error(f"数据库连接断开: {error_message}")
                # 尝试重新连接数据库
                try:
                    for conn in connections.all():
                        conn.close()
                    logger.info("已关闭所有数据库连接，等待重新连接")
                except Exception as e:
                    logger.error(f"关闭数据库连接时出错: {str(e)}")
                
                return APIResponse.error(
                    message="数据库连接暂时不可用，请稍后重试",
                    code="DB_CONNECTION_LOST",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            logger.error(f"数据库错误: {error_message}")
            return APIResponse.error(
                message="数据库操作失败，请稍后重试",
                code="DATABASE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if isinstance(exception, RedisError):
            logger.error(f"Redis错误: {str(exception)}")
            return APIResponse.error(
                message="服务暂时不可用，请稍后重试",
                code="CACHE_ERROR",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if isinstance(exception, PermissionDenied):
            return APIResponse.forbidden(message="没有权限执行此操作")

        if isinstance(exception, NotFound):
            return APIResponse.not_found(message="请求的资源不存在")

        if isinstance(exception, MethodNotAllowed):
            return APIResponse.error(
                message="不支持的请求方法",
                code="METHOD_NOT_ALLOWED",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        # 处理未预期的异常
        logger.error(f"未处理的异常: {str(exception)}", exc_info=True)
        return APIResponse.server_error(message="服务器内部错误")

class TimeoutMiddleware:
    """请求超时中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 设置请求开始时间
        request.start_time = time.time()
        
        # 使用线程实现超时控制
        result = {"response": None, "exception": None}
        
        def process_request():
            try:
                result["response"] = self.get_response(request)
            except Exception as e:
                result["exception"] = e
                
        # 创建处理线程
        thread = threading.Thread(target=process_request)
        thread.daemon = True
        thread.start()
        
        # 等待线程完成，最多等待REQUEST_TIMEOUT秒
        thread.join(REQUEST_TIMEOUT)
        
        # 如果线程仍在运行，说明请求超时
        if thread.is_alive():
            logger.error(f"请求超时: {request.path}")
            return APIResponse.error(
                message="请求处理超时，请稍后重试",
                code="REQUEST_TIMEOUT",
                status_code=status.HTTP_408_REQUEST_TIMEOUT
            )
            
        # 如果有异常，重新抛出
        if result["exception"]:
            raise result["exception"]
            
        return result["response"]

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """性能监控中间件"""

    def process_request(self, request):
        request.start_time = time.time()
        request._query_count_start = len(connection.queries)
        request._query_time_start = time.time()
        request._cache_hits = 0
        request._cache_misses = 0
        request._memory_start = psutil.Process().memory_info().rss
        request._thread_start = threading.active_count()
        request._fd_start = len(psutil.Process().open_files())
        
    def _get_system_metrics(self):
        """获取系统指标"""
        process = psutil.Process()
        metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'process_memory': process.memory_info().rss / 1024 / 1024,  # MB
            'process_cpu_percent': process.cpu_percent(),
            'thread_count': threading.active_count(),
            'open_files': len(process.open_files()),
            'connections': len(process.connections()),
        }
        
        # 添加磁盘使用情况，带错误处理
        try:
            disk = psutil.disk_usage('/')
            metrics.update({
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_free': disk.free,
                'disk_percent': float(disk.percent)
            })
        except Exception as e:
            logger.warning(f"Failed to get disk usage metrics: {str(e)}")
            metrics.update({
                'disk_total': 0,
                'disk_used': 0,
                'disk_free': 0,
                'disk_percent': 0.0
            })
            
        return metrics
        
    def process_response(self, request, response):
        # 递归保护
        if getattr(request, '_performance_monitoring_in_progress', False):
            return response
            
        if not hasattr(request, 'start_time'):
            return response
        
        try:
            # 设置标记防止递归
            request._performance_monitoring_in_progress = True
            
            # 计算请求处理时间
            duration = time.time() - request.start_time
            
            # 计算数据库查询统计
            query_count = len(connection.queries) - request._query_count_start
            query_time = sum(float(q.get('time', 0)) for q in connection.queries[request._query_count_start:])
            
            # 计算内存增长
            memory_growth = psutil.Process().memory_info().rss - request._memory_start
            
            # 计算线程增长
            thread_growth = threading.active_count() - request._thread_start
            
            # 计算文件描述符增长
            fd_growth = len(psutil.Process().open_files()) - request._fd_start
            
            # 安全获取用户信息
            user_info = 'anonymous'
            if check_user_authenticated(request):
                try:
                    user_info = str(request.user)
                except Exception as e:
                    logger.debug(f"获取用户信息失败: {str(e)}")
                    user_info = 'unknown'
            
            # 安全获取响应大小
            response_size = 0
            if hasattr(response, 'content'):
                # 检查内容是否已渲染
                if getattr(response, '_is_rendered', False) or not hasattr(response, 'render'):
                    try:
                        response_size = len(response.content)
                    except Exception:
                        pass
            
            # 收集性能指标
            metrics = {
                'duration': duration,
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'db_queries': query_count,
                'db_query_time': query_time,
                'response_size': response_size,
                'cache_hits': getattr(request, '_cache_hits', 0),
                'cache_misses': getattr(request, '_cache_misses', 0),
                'memory_growth': memory_growth,
                'thread_growth': thread_growth,
                'fd_growth': fd_growth,
                'user': user_info,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
            
            # 添加系统资源使用情况
            metrics.update(self._get_system_metrics())
            
            # 记录慢请求（超过1秒）
            if duration > 1.0:
                logger.warning(f'Slow request detected: {json.dumps(metrics)}')
                
            # 更新性能统计
            self._update_performance_stats(metrics)
            
            # 更新时间线数据
            self._update_timeline_stats(metrics)
            
            # 检查资源泄漏
            self._check_resource_leaks(metrics)
        
        except Exception as e:
            logger.error(f"性能监控处理失败: {str(e)}")
        finally:
            # 清除递归保护标记
            request._performance_monitoring_in_progress = False
            
        return response
        
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
        
    def _check_resource_leaks(self, metrics: Dict[str, Any]):
        """检查资源泄漏"""
        alerts = []
        
        # 检查内存泄漏
        if metrics['memory_growth'] > settings.MEMORY_GROWTH_THRESHOLD:
            alerts.append(f'Memory leak detected: {metrics["memory_growth"] / 1024 / 1024:.2f}MB growth')
            
        # 检查线程泄漏
        if metrics['thread_growth'] > settings.THREAD_GROWTH_THRESHOLD:
            alerts.append(f'Thread leak detected: {metrics["thread_growth"]} new threads')
            
        # 检查文件描述符泄漏
        if metrics['fd_growth'] > settings.FD_GROWTH_THRESHOLD:
            alerts.append(f'File descriptor leak detected: {metrics["fd_growth"]} new FDs')
            
        if alerts:
            logger.warning('Resource leak alerts: ' + '; '.join(alerts))
            
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _update_performance_stats(self, metrics: Dict[str, Any]):
        """更新性能统计数据"""
        cache_key = f'performance_stats_{time.strftime("%Y%m%d_%H")}'  # 按小时统计
        try:
            stats = cache.get(cache_key) or {
                'request_count': 0,
                'total_duration': 0,
                'slow_requests': 0,
                'error_requests': 0,
                'total_queries': 0,
                'total_query_time': 0,
                'total_response_size': 0,
                'total_cache_hits': 0,
                'total_cache_misses': 0,
                'total_memory_growth': 0,
                'total_thread_growth': 0,
                'total_fd_growth': 0,
                'status_codes': {},
                'paths': {},
                'user_stats': {},
                'ip_stats': {},
                'start_time': time.time()
            }
            
            # 如果统计时间超过1小时，重置统计数据
            if time.time() - stats['start_time'] > 3600:
                stats = {
                    'request_count': 0,
                    'total_duration': 0,
                    'slow_requests': 0,
                    'error_requests': 0,
                    'total_queries': 0,
                    'total_query_time': 0,
                    'total_response_size': 0,
                    'total_cache_hits': 0,
                    'total_cache_misses': 0,
                    'total_memory_growth': 0,
                    'total_thread_growth': 0,
                    'total_fd_growth': 0,
                    'status_codes': {},
                    'paths': {},
                    'user_stats': {},
                    'ip_stats': {},
                    'start_time': time.time()
                }
            
            # 更新基础统计数据
            stats['request_count'] += 1
            stats['total_duration'] += metrics['duration']
            stats['total_queries'] += metrics['db_queries']
            stats['total_query_time'] += metrics['db_query_time']
            stats['total_response_size'] += metrics['response_size']
            stats['total_cache_hits'] += metrics['cache_hits']
            stats['total_cache_misses'] += metrics['cache_misses']
            stats['total_memory_growth'] += metrics['memory_growth']
            stats['total_thread_growth'] += metrics['thread_growth']
            stats['total_fd_growth'] += metrics['fd_growth']
            
            if metrics['duration'] > 1.0:  # 超过1秒的请求视为慢请求
                stats['slow_requests'] += 1
                
            if metrics['status_code'] >= 400:
                stats['error_requests'] += 1
                
            # 保存统计数据
            cache.set(cache_key, stats, 3600)  # 保存1小时
            
            # 检查告警阈值（只在请求数超过30时进行）
            if stats['request_count'] > 30:
                self._check_alerts(metrics, stats)
            
        except Exception as e:
            logger.error(f'Failed to update performance stats: {e}')
            
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def _update_timeline_stats(self, metrics: Dict[str, Any]):
        """更新时间线统计数据"""
        timeline_key = f'performance_timeline_{time.strftime("%Y%m%d")}'
        try:
            timeline = cache.get(timeline_key) or []
            current_minute = datetime.now().replace(second=0, microsecond=0)
            
            # 如果时间线为空或最后一个时间点不是当前分钟，添加新的时间点
            if not timeline or timeline[-1]['time'] != current_minute.isoformat():
                timeline.append({
                    'time': current_minute.isoformat(),
                    'request_count': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'error_count': 0,
                    'slow_count': 0,
                    'cpu_percent': metrics['cpu_percent'],
                    'memory_percent': metrics['memory_percent'],
                    'disk_percent': metrics['disk_percent'],
                    'response_size': 0,
                    'cache_hits': 0,
                    'cache_misses': 0,
                    'active_requests': 1,
                })
            
            # 更新当前分钟的统计数据
            current_stats = timeline[-1]
            current_stats['request_count'] += 1
            current_stats['total_duration'] += metrics['duration']
            current_stats['avg_duration'] = current_stats['total_duration'] / current_stats['request_count']
            current_stats['response_size'] += metrics['response_size']
            current_stats['cache_hits'] += metrics['cache_hits']
            current_stats['cache_misses'] += metrics['cache_misses']
            
            if metrics['status_code'] >= 400:
                current_stats['error_count'] += 1
            if metrics['duration'] > settings.SLOW_REQUEST_THRESHOLD:
                current_stats['slow_count'] += 1
                
            # 更新系统资源使用情况（使用移动平均）
            alpha = 0.3  # 平滑因子
            current_stats['cpu_percent'] = (
                alpha * metrics['cpu_percent'] + 
                (1 - alpha) * current_stats['cpu_percent']
            )
            current_stats['memory_percent'] = (
                alpha * metrics['memory_percent'] + 
                (1 - alpha) * current_stats['memory_percent']
            )
            current_stats['disk_percent'] = (
                alpha * metrics['disk_percent'] + 
                (1 - alpha) * current_stats['disk_percent']
            )
            
            # 保留最近24小时的数据
            timeline = timeline[-1440:]  # 24小时 * 60分钟
            
            # 保存时间线数据
            cache.set(timeline_key, timeline, 86400)  # 保存24小时
            
        except Exception as e:
            logger.error(f'Failed to update timeline stats: {e}')
            
    def _check_alerts(self, metrics: Dict[str, Any], stats: Dict[str, Any]):
        """检查是否需要发送告警"""
        alerts = []
        
        # CPU使用率告警（超过80%）
        if metrics['cpu_percent'] > 80:
            alerts.append(f'High CPU usage: {metrics["cpu_percent"]}%')
            
        # 内存使用率告警（超过80%）
        if metrics['memory_percent'] > 80:
            alerts.append(f'High memory usage: {metrics["memory_percent"]}%')
            
        # 磁盘使用率告警（超过85%）
        if metrics['disk_percent'] > 85:
            alerts.append(f'High disk usage: {metrics["disk_percent"]}%')
            
        # 错误率告警（超过10%，且请求数大于30）
        error_rate = stats['error_requests'] / stats['request_count'] * 100
        if error_rate > 10:
            alerts.append(f'High error rate: {error_rate:.2f}%')
            
        # 慢请求比例告警（超过20%，且请求数大于30）
        slow_rate = stats['slow_requests'] / stats['request_count'] * 100
        if slow_rate > 20:
            alerts.append(f'High slow request rate: {slow_rate:.2f}%')
            
        # 数据库查询告警（平均查询时间超过1秒）
        if stats['total_queries'] > 0:
            avg_query_time = stats['total_query_time'] / stats['total_queries']
            if avg_query_time > 1.0:
                alerts.append(f'High average query time: {avg_query_time:.2f}s')
            
        # 缓存命中率告警（低于50%，且缓存请求数大于100）
        total_cache_requests = stats['total_cache_hits'] + stats['total_cache_misses']
        if total_cache_requests > 100:
            cache_hit_rate = stats['total_cache_hits'] / total_cache_requests * 100
            if cache_hit_rate < 50:
                alerts.append(f'Low cache hit rate: {cache_hit_rate:.2f}%')
        
        if alerts and not settings.DEBUG:  # 只在生产环境发送告警
            logger.warning('Performance alerts: ' + '; '.join(alerts))
            self._send_alerts(alerts)
            
    def _send_alerts(self, alerts: List[str]):
        """发送告警通知"""
        try:
            # 获取告警配置
            alert_config = cache.get('alert_config') or {
                'email': True,
                'dingtalk': True,
                'webhook': True,
            }
            
            # 发送邮件告警
            if alert_config.get('email'):
                self._send_email_alert(alerts)
                
            # 发送钉钉告警
            if alert_config.get('dingtalk'):
                self._send_dingtalk_alert(alerts)
                
            # 发送Webhook告警
            if alert_config.get('webhook'):
                self._send_webhook_alert(alerts)
                
        except Exception as e:
            logger.error(f'Failed to send alerts: {e}')
            
    def _send_email_alert(self, alerts: List[str]):
        """发送邮件告警"""
        try:
            from django.core.mail import send_mail
            subject = '性能监控告警'
            message = '\n'.join(alerts)
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = settings.ALERT_EMAIL_RECIPIENTS
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            logger.error(f'Failed to send email alert: {e}')
            
    def _send_dingtalk_alert(self, alerts: List[str]):
        """发送钉钉告警"""
        try:
            import requests
            webhook_url = settings.DINGTALK_WEBHOOK_URL
            headers = {'Content-Type': 'application/json'}
            data = {
                'msgtype': 'text',
                'text': {
                    'content': '性能监控告警:\n' + '\n'.join(alerts)
                }
            }
            requests.post(webhook_url, json=data, headers=headers)
        except Exception as e:
            logger.error(f'Failed to send dingtalk alert: {e}')
            
    def _send_webhook_alert(self, alerts: List[str]):
        """发送Webhook告警"""
        try:
            import requests
            webhook_url = settings.ALERT_WEBHOOK_URL
            data = {
                'type': 'performance_alert',
                'alerts': alerts,
                'timestamp': time.time()
            }
            requests.post(webhook_url, json=data)
        except Exception as e:
            logger.error(f'Failed to send webhook alert: {e}')

class QueryCountMiddleware(MiddlewareMixin):
    """查询计数中间件"""
    
    def process_request(self, request):
        request._query_count = len(connection.queries)
        request._query_time = time.time()

    def process_response(self, request, response):
        if not hasattr(request, '_query_count'):
            return response

        total_queries = len(connection.queries) - request._query_count
        query_time = time.time() - request._query_time

        if total_queries > 100:  # 设置一个合理的阈值
            logger.warning({
                'type': 'high_query_count',
                'path': request.path,
                'method': request.method,
                'query_count': total_queries,
                'query_time': query_time,
                'user': str(request.user) if check_user_authenticated(request) else 'anonymous'
            })

        return response


class AuditLogMiddleware(MiddlewareMixin):
    """审计日志中间件"""
    HIGH_RISK_PATHS = {'/api/admin/', '/api/users/', '/api/auth/'}
    
    def process_request(self, request):
        request.audit_data = {
            'ip_addr': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'start_time': time.time(),
        }

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def process_response(self, request, response):
        """处理响应，记录审计日志"""
        # 添加递归保护
        if getattr(request, '_audit_log_in_progress', False):
            return response
            
        if not hasattr(request, '_audit_log_start_time'):
            return response

        try:
            # 设置递归保护标记
            request._audit_log_in_progress = True
            
            # 计算执行时间
            duration = time.time() - request._audit_log_start_time

            # 获取请求体
            body = self.get_request_body(request)

            # 确定风险等级
            risk_level = self.determine_risk_level(request, body)

            # 确定模块
            module = self.determine_module(request.path)

            # 确定操作类型
            action = self.determine_action(request.method, request.path)

            # 获取变更信息
            change_message = self.get_change_message(request, response, body)

            # 获取错误信息
            error_message = self.get_error_message(response)

            # 安全获取用户信息
            user = None
            if check_user_authenticated(request):
                try:
                    user = request.user
                except Exception as e:
                    logger.debug(f"获取用户信息失败: {str(e)}")

            # 记录审计日志
            try:
                AuditLog.objects.create(
                    user=user,
                    action=action,
                    content_type=request.content_type if hasattr(request, 'content_type') else None,
                    object_id=request.object_id if hasattr(request, 'object_id') else None,
                    object_repr=str(request.object_repr) if hasattr(request, 'object_repr') else None,
                    change_message=change_message,
                    ip_addr=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    risk_level=risk_level,
                    module=module,
                    status='SUCCESS' if 200 <= response.status_code < 300 else 'ERROR',
                    error_message=error_message,
                    duration=duration * 1000  # 转换为毫秒
                )
            except Exception as e:
                logger.error(f"记录审计日志失败: {str(e)}")
        except Exception as e:
            logger.error(f"审计日志处理失败: {str(e)}")
        finally:
            # 清除递归保护标记
            request._audit_log_in_progress = False

        return response

    def should_log_get(self, request):
        """判断是否需要记录GET请求"""
        sensitive_paths = {'/api/export/', '/api/download/', '/api/report/'}
        return any(request.path.startswith(path) for path in sensitive_paths)

    def get_request_body(self, request):
        """获取请求体数据并处理敏感信息"""
        try:
            if request.body:
                body = json.loads(request.body)
                return mask_sensitive_data(body)
            return {}
        except:
            return {}

    def determine_risk_level(self, request, body):
        """确定风险等级"""
        if any(request.path.startswith(path) for path in self.HIGH_RISK_PATHS):
            return 'HIGH'
        if request.method in ['DELETE', 'PUT'] or len(body.get('ids', [])) > 10:
            return 'MEDIUM'
        return 'LOW'

    def determine_module(self, path):
        """确定功能模块"""
        path_parts = path.strip('/').split('/')
        return path_parts[1] if len(path_parts) > 1 else 'other'

    def determine_action(self, method, path):
        """确定操作类型"""
        if 'login' in path:
            return 'LOGIN'
        if 'logout' in path:
            return 'LOGOUT'
        if 'export' in path:
            return 'EXPORT'
        if 'import' in path:
            return 'IMPORT'
        
        method_action_map = {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE',
        }
        return method_action_map.get(method, 'OTHER')

    def get_safe_repr(self, data):
        """获取安全的对象描述"""
        return str(mask_sensitive_data(data))[:200]

    def get_change_message(self, request, response, body):
        """获取变更信息"""
        return {
            'method': request.method,
            'path': request.path,
            'query': request.GET.dict(),
            'body': mask_sensitive_data(body),
            'status_code': response.status_code,
            'timestamp': now().isoformat()
        }

    def get_error_message(self, response):
        """获取错误信息"""
        try:
            if hasattr(response, 'data'):
                return str(response.data)
            
            if hasattr(response, 'content'):
                # 检查内容是否已渲染
                if getattr(response, '_is_rendered', False) or not hasattr(response, 'render'):
                    return str(response.content)[:500]
                return "Content not rendered"
            
            return 'No error message available'
        except Exception:
            return 'Error message not available'


class RequestLoggingMiddleware(MiddlewareMixin):
    """请求日志中间件"""

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def get_request_body(self, request):
        """获取请求体"""
        try:
            if request.body:
                return json.loads(request.body)
            return {}
        except json.JSONDecodeError:
            return {'raw': request.body.decode('utf-8', errors='ignore')}
        except Exception as e:
            self.logger.error(f"获取请求体失败: {str(e)}")
            return {}

    def get_request_headers(self, request):
        """获取请求头"""
        headers = {}
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                headers[key[5:].lower()] = value
        return headers

    def process_request(self, request):
        """处理请求"""
        # 生成一个短的请求ID
        request_uuid = str(uuid.uuid4())
        request.id = hashlib.md5(request_uuid.encode()).hexdigest()[:16]
        request.start_time = time.time()
        
        try:
            # 记录请求日志，但暂时不设置用户信息
            RequestLog.objects.create(
                request_id=request.id,
                method=request.method,
                url=request.path,
                params=dict(request.GET),
                headers=self.get_request_headers(request),
                body=self.get_request_body(request),
                ip=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                user=None  # 先不设置用户，避免此时访问request.user导致递归
            )
        except Exception as e:
            self.logger.error(f"记录请求日志失败: {str(e)}")

    def process_response(self, request, response):
        """处理响应"""
        # 添加递归保护
        if getattr(request, '_response_logging_in_progress', False):
            return response

        try:
            # 设置标记以防止递归
            request._response_logging_in_progress = True
            
            # 计算响应时间
            duration = (time.time() - getattr(request, 'start_time', time.time())) * 1000
            
            # 获取响应体
            body = {}
            if hasattr(response, 'content'):
                # 检查是否为未渲染的内容
                if getattr(response, '_is_rendered', False) or not hasattr(response, 'render'):
                    try:
                        if isinstance(response.content, bytes):
                            body = response.content.decode('utf-8')
                        else:
                            body = response.content
                        try:
                            body = json.loads(body)
                        except json.JSONDecodeError:
                            body = {'raw': body}
                    except Exception:
                        body = {'error': 'Unable to decode response body'}
                else:
                    # 内容未渲染，不尝试获取
                    body = {'info': 'Response content not rendered'}

            # 记录响应日志
            request_log = RequestLog.objects.filter(request_id=getattr(request, 'id', None)).first()
            if request_log:
                # 在这里更新用户信息
                if request_log.user is None and check_user_authenticated(request):
                    try:
                        request_log.user = request.user
                        request_log.save(update_fields=['user'])
                    except Exception as e:
                        self.logger.error(f"更新请求日志用户信息失败: {str(e)}")
                
                # 安全地获取响应头
                try:
                    headers = dict(response.headers)
                except Exception:
                    headers = {}
                
                ResponseLog.objects.create(
                    request=request_log,
                    status_code=response.status_code,
                    headers=headers,
                    body=body,
                    duration=duration
                )
        except Exception as e:
            self.logger.error(f"记录响应日志失败: {str(e)}")
        finally:
            # 清除递归保护标记
            request._response_logging_in_progress = False
            
        return response


class CacheMiddleware:
    """缓存中间件"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def __call__(self, request):
        # 检查是否需要缓存
        if self._should_cache(request):
            # 尝试从缓存获取响应
            cached_response = self._get_cached_response(request)
            if cached_response:
                return cached_response
        
        response = self.get_response(request)
        
        # 如果需要，缓存响应
        if self._should_cache(request):
            self._cache_response(request, response)
        
        return response

    def _should_cache(self, request) -> bool:
        """判断是否应该缓存"""
        # 只缓存GET请求
        if request.method != 'GET':
            return False
            
        # 不缓存认证用户的请求
        if check_user_authenticated(request):
            return False
            
        # 检查请求路径是否在缓存白名单中
        return any(path in request.path for path in settings.CACHE_PATHS)

    def _get_cache_key(self, request) -> str:
        """生成缓存键"""
        return f"cache:{request.path}:{request.GET.urlencode()}"

    def _get_cached_response(self, request) -> Optional[Any]:
        """获取缓存的响应"""
        cache_key = self._get_cache_key(request)
        return cache.get(cache_key)

    def _cache_response(self, request, response):
        """缓存响应"""
        if response.status_code == 200:
            cache_key = self._get_cache_key(request)
            cache.set(cache_key, response, timeout=settings.CACHE_TIMEOUT)

def custom_exception_handler(exc, context):
    """
    自定义异常处理
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # 处理DRF的标准异常
        error_msg = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
        error_code = exc.get_codes() if hasattr(exc, 'get_codes') else 'error'
        
        response.data = {
            'status': 'error',
            'code': error_code,
            'message': error_msg,
            'data': None
        }
    
    return response


class GlobalExceptionMiddleware(MiddlewareMixin):
    """
    全局异常处理中间件
    """
    def process_exception(self, request, exception):
        """
        处理所有未被捕获的异常
        """
        # 获取异常信息
        exc_traceback = traceback.format_exc()
        logger.error(f"Uncaught exception: {exc_traceback}")

        # 构建错误响应
        error_response = {
            'status': 'error',
            'code': 'SYSTEM_ERROR',
            'message': '系统发生错误',
            'data': None
        }

        # 在开发环境下返回详细错误信息
        if settings.DEBUG:
            error_response['detail'] = {
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception),
                'traceback': exc_traceback
            }

        # 根据异常类型设置不同的状态码和错误信息
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        if isinstance(exception, BaseAPIException):
            status_code = exception.status_code
            error_response['code'] = exception.default_code
            error_response['message'] = str(exception.detail)

        elif isinstance(exception, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
            error_response['code'] = 'VALIDATION_ERROR'
            error_response['message'] = str(exception)

        elif isinstance(exception, DatabaseError):
            error_response['code'] = 'DATABASE_ERROR'
            error_response['message'] = '数据库操作失败'

        elif isinstance(exception, RedisError):
            error_response['code'] = 'CACHE_ERROR'
            error_response['message'] = '缓存操作失败'

        elif isinstance(exception, APIException):
            status_code = exception.status_code
            error_response['code'] = exception.default_code
            error_response['message'] = str(exception.detail)

        return JsonResponse(error_response, status=status_code)


class APIMetricsMiddleware(MiddlewareMixin):
    """
    API指标统计中间件
    """
    def process_request(self, request):
        request.start_time = time.time()

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def process_response(self, request, response):
        """处理响应，记录API指标"""
        if not hasattr(request, '_start_time'):
            return response

        # 计算响应时间
        duration = time.time() - request._start_time

        # 记录API调用指标
        try:
            from .models import APIMetrics
            
            # 尝试获取用户，避免递归
            user = None
            if check_user_authenticated(request):
                try:
                    user = request.user
                except Exception as e:
                    logger.debug(f"获取用户信息失败: {str(e)}")
            
            APIMetrics.objects.create(
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time=duration * 1000,  # 转换为毫秒
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                query_count=len(connection.queries) if settings.DEBUG else 0,
                error_message=str(response.data) if hasattr(response, 'data') and response.status_code >= 400 else None
            )
        except Exception as e:
            logger.error(f"记录API指标失败: {str(e)}")

        return response

class URLCleanupMiddleware:
    """
    处理URL路径重复问题的中间件
    例如：将 '/api/v1/api/v1/path' 修正为 '/api/v1/path'
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # 编译重复API路径的正则表达式
        self.double_api_pattern = re.compile(r'/api/v1/api/v1/')

    def __call__(self, request):
        # 检查并修复路径重复问题
        if self.double_api_pattern.search(request.path):
            # 修正路径
            fixed_path = request.path.replace('/api/v1/api/v1/', '/api/v1/')
            logger.warning(f"检测到重复API路径: {request.path} -> 修正为: {fixed_path}")
            request.path = fixed_path
            request.path_info = fixed_path
        
        # 继续处理请求
        response = self.get_response(request)
        return response 

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """JWT认证中间件"""
    def process_request(self, request):
        # 检查是否是认证豁免的URL
        path = request.path.lstrip('/')
        
        # 处理OPTIONS请求
        if request.method == 'OPTIONS':
            request._skip_jwt_auth = True
            return None
        
        # 特别处理admin页面，直接跳过JWT认证
        if path.startswith('admin/'):
            request._skip_jwt_auth = True
            return None
        
        # 从Django REST框架设置中获取不需要认证的URL列表
        exempt_urls = getattr(settings, 'REST_FRAMEWORK', {}).get('UNAUTHENTICATED_URLS', [])
        
        # 特别处理"monitoring"路径下的请求 - 完全放开不做认证要求
        if 'monitoring' in path or path.startswith('api/v1/core/monitoring/') or 'monitoring' in request.path:
            # 监控请求不需要认证，但保留可能存在的用户信息
            request._skip_jwt_auth = True  # 跳过JWT认证
            # 确保不会返回401状态码
            request._allow_anonymous_for_monitoring = True
            print(f"监控接口允许匿名访问: {path}")
            return None
            
        # 检查当前路径是否在豁免列表中
        for exempt_url in exempt_urls:
            if exempt_url.endswith('/'):
                exempt_url = exempt_url[:-1]
            if path.startswith(exempt_url) or path == exempt_url.lstrip('/'):
                # 豁免URL，跳过认证
                request._skip_jwt_auth = True
                print(f"跳过JWT认证: {path} 在豁免列表中")
                return None
        
        # 非豁免URL，获取用户
        request._skip_jwt_auth = False
        # 防止递归，检查是否已经在处理认证
        if not hasattr(request, '_jwt_auth_in_progress') and (not hasattr(request, 'user') or request.user.is_anonymous):
            request._jwt_auth_in_progress = True
            request.user = SimpleLazyObject(lambda: self.get_jwt_user(request))
            if hasattr(request, '_jwt_auth_in_progress'):
                del request._jwt_auth_in_progress

    @staticmethod
    def get_jwt_user(request):
        # 如果正在进行认证处理，返回None避免递归
        if getattr(request, '_jwt_auth_in_progress', False):
            return None
            
        # 如果标记为跳过认证，直接返回None
        if getattr(request, '_skip_jwt_auth', False):
            return None
        
        # 标记正在处理中    
        request._jwt_auth_in_progress = True
            
        try:
            # 从request获取user
            user = get_user(request)
            if user.is_authenticated:
                return user
                
            # 获取请求头中的JWT token
            jwt_auth = JWTAuthentication()
            user_auth_tuple = jwt_auth.authenticate(request)
            if user_auth_tuple is not None:
                user, token = user_auth_tuple
                return user
                
            # 认证失败，返回None而不是request.user以避免递归
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
        except Exception as e:
            # 认证失败，记录错误
            logger.debug(f"JWT认证失败: {str(e)}")
            # 返回AnonymousUser而不是None
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
        finally:
            # 清除处理标记
            if hasattr(request, '_jwt_auth_in_progress'):
                del request._jwt_auth_in_progress

class APIMonitorMiddleware(MiddlewareMixin):
    """API监控中间件，记录请求和响应信息，帮助调试"""
    
    def process_request(self, request):
        """处理请求"""
        request.api_monitor_start_time = time.time()
        
        # 仅监控API请求
        if request.path.startswith('/api/'):
            # 记录请求信息
            request_method = request.method
            request_path = request.path
            request_query = request.GET.dict()
            
            # 获取请求体
            try:
                if request.body:
                    request_body = request.body.decode('utf-8')
                    # 尝试解析JSON请求体
                    try:
                        request_body = json.loads(request_body)
                    except:
                        pass
                else:
                    request_body = {}
            except:
                request_body = "<cannot decode>"
                
            # 记录请求头
            headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
            
            # 打印请求信息
            print(f"\n{'='*80}")
            print(f"API请求: {request_method} {request_path}")
            print(f"查询参数: {request_query}")
            print(f"请求体: {request_body}")
            print(f"请求头: {headers}")
            print(f"{'='*80}\n")
    
    def process_response(self, request, response):
        """处理响应"""
        # 仅监控API请求
        if hasattr(request, 'api_monitor_start_time') and request.path.startswith('/api/'):
            # 计算处理时间
            process_time = time.time() - request.api_monitor_start_time
            
            # 记录响应信息
            status_code = response.status_code
            
            # 尝试获取响应内容
            response_content = "<no content>"
            try:
                if hasattr(response, 'content'):
                    # 检查内容是否已渲染
                    if getattr(response, '_is_rendered', False) or not hasattr(response, 'render'):
                        response_content = response.content.decode('utf-8')
                        # 尝试解析JSON响应
                        try:
                            response_content = json.loads(response_content)
                        except:
                            pass
                    else:
                        response_content = "<content not rendered>"
            except:
                response_content = "<cannot decode>"
                
            # 打印响应信息
            print(f"\n{'='*80}")
            print(f"API响应: {request.method} {request.path} - 状态码: {status_code}")
            print(f"处理时间: {process_time:.4f}秒")
            print(f"响应内容: {response_content}")
            print(f"{'='*80}\n")
            
        return response 

# 添加自定义CORS中间件
class CustomCORSMiddleware:
    """自定义CORS中间件，用于解决跨域问题"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = [
            'http://localhost:5173',
            'http://localhost:5174',
            'http://localhost:5175',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:5174',
            'http://127.0.0.1:5175',
        ]
        self.allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
        self.allowed_headers = [
            'accept',
            'accept-encoding',
            'authorization',
            'content-type',
            'dnt',
            'origin',
            'user-agent',
            'x-csrftoken',
            'x-requested-with',
            'x-frontend-origin',
            'x-frontend-debug',
            'x-request-id',
            'access-control-request-method',
            'access-control-request-headers',
        ]
    
    def __call__(self, request):
        # 检查请求头中的源是否在允许列表中或是否允许所有源
        origin = request.META.get('HTTP_ORIGIN', '')
        allow_all = getattr(settings, 'CORS_ORIGIN_ALLOW_ALL', False)
        
        # 记录CORS请求信息
        logger.debug(f"CORS请求: {request.method} {request.path} 来源: {origin}, 允许所有源: {allow_all}")
        
        # 处理预检请求
        if request.method == 'OPTIONS':
            logger.debug(f"处理OPTIONS预检请求: {request.path}, 来源: {origin}")
            
            response = HttpResponse()
            response['Content-Type'] = 'text/plain'
            
            # 设置CORS头
            if allow_all or origin in self.allowed_origins:
                response['Access-Control-Allow-Origin'] = origin or '*'
            else:
                response['Access-Control-Allow-Origin'] = self.allowed_origins[0] if self.allowed_origins else '*'
                
            response['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
            response['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'  # 24小时
            
            logger.debug(f"OPTIONS响应头: {dict(response.headers)}")
            return response
        
        # 处理正常请求
        response = self.get_response(request)
        
        # 设置CORS头
        if allow_all or origin in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = origin or '*'
        elif self.allowed_origins:
            response['Access-Control-Allow-Origin'] = self.allowed_origins[0]
            
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
        
        # 添加其他可能需要的头
        if hasattr(response, 'headers'):
            response.headers['Vary'] = 'Origin'
            
        logger.debug(f"正常请求CORS响应头: {request.method} {request.path}, 添加的CORS头: Origin={response.get('Access-Control-Allow-Origin')}")
            
        return response

class AllowAllCORSMiddleware:
    """
    中间件，允许所有跨域请求，不做任何检查
    仅用于开发环境调试
    """
    def __init__(self, get_response):
        self.get_response = get_response
        logger.info("AllowAllCORSMiddleware 已启用 - 允许所有跨域请求")

    def __call__(self, request):
        # 记录请求信息
        origin = request.headers.get('Origin', '')
        method = request.method
        path = request.path
        
        logger.info(f"CORS中间件处理请求: {method} {path}, Origin: {origin}")
        
        # 对于OPTIONS请求，直接返回成功，带上CORS头
        if request.method == 'OPTIONS':
            logger.info(f"处理OPTIONS预检请求: {path}")
            
            # 允许的HTTP方法
            allowed_methods = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
            
            # 允许的HTTP头
            allowed_headers = request.headers.get('Access-Control-Request-Headers') or '*'
            
            response = HttpResponse('')
            response.status_code = 204  # 204 No Content 更适用于OPTIONS
            response['Content-Length'] = '0'
            
            # 设置CORS头
            response['Access-Control-Allow-Origin'] = origin or '*'
            response['Access-Control-Allow-Methods'] = allowed_methods
            response['Access-Control-Allow-Headers'] = allowed_headers
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'  # 24小时
            
            # 记录响应头
            logger.info(f"OPTIONS预检响应头: {dict(response.headers)}")
            return response
        
        # 对于其他请求，处理后添加CORS头
        response = self.get_response(request)
        
        # 添加CORS头到响应
        if origin:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
        else:
            response['Access-Control-Allow-Origin'] = '*'
            
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response['Access-Control-Allow-Headers'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Type'
        
        # 记录正常请求的响应头
        logger.info(f"正常请求响应头: {method} {path}, 状态码: {response.status_code}, 头: {dict(response.headers)}")
        
        return response 