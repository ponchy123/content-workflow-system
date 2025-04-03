from rest_framework import viewsets, permissions, status, exceptions
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from .models import ServiceProvider, SystemConfig, Notification, NotificationSettings
from .serializers import (
    ServiceProviderSerializer, 
    SystemConfigSerializer,
    UserLoginSerializer,
    ConfigBatchUpdateSerializer,
    NotificationSerializer,
    NotificationSettingsSerializer,
    TaskHistorySerializer,
    PerformanceStatsSerializer,
    MetricsSerializer,
    HealthCheckSerializer,
    APIErrorSerializer
)
from django.http import JsonResponse, HttpResponse, Http404
from django.db import connection, models
from rest_framework.permissions import AllowAny, IsAdminUser
from redis.exceptions import RedisError
import psutil
import os
from django.utils import timezone
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from .exceptions import InvalidParameterException
from rest_framework_simplejwt.tokens import RefreshToken
from django_celery_results.models import TaskResult
from datetime import timedelta
import time
import pandas as pd
import io
from io import BytesIO
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.serializers import AuthTokenSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, extend_schema_field
from drf_spectacular.types import OpenApiTypes
from typing import Dict, Any, List, Optional
from rest_framework.generics import GenericAPIView
import json
from django.views.decorators.csrf import csrf_exempt
import logging
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token


logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    服务商视图集
    """
    queryset = ServiceProvider.objects.all().order_by('id')
    serializer_class = ServiceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'code']
    search_fields = ['name', 'code', 'contact_person']
    ordering_fields = ['created_at', 'name', 'id']
    ordering = ['id']
    pagination_class = StandardResultsSetPagination

    @method_decorator(cache_page(60 * 15))  # 缓存15分钟
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        """
        获取服务商列表（已缓存15分钟）
        """
        return super().list(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """
        删除服务商
        """
        instance.delete()
        # 删除相关缓存
        cache.delete_pattern(f'*{self.__class__.__name__}*')

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """
        切换服务商状态
        """
        provider = self.get_object()
        provider.status = not provider.status
        provider.save()
        # 删除相关缓存
        cache.delete_pattern(f'*{self.__class__.__name__}*')
        return Response({'status': provider.status})

    @action(detail=True, methods=['post'])
    def refresh_api_key(self, request, pk=None):
        """
        刷新API密钥
        """
        provider = self.get_object()
        # TODO: 实现API密钥刷新逻辑
        return Response({'message': 'API密钥已刷新'})


@extend_schema_view(
    list=extend_schema(
        summary="获取系统配置列表",
        description="获取系统配置列表，支持分页、过滤和搜索",
        parameters=[
            OpenApiParameter(
                name="page",
                type={"type": "integer"},
                location=OpenApiParameter.QUERY,
                description="页码"
            ),
            OpenApiParameter(
                name="page_size",
                type={"type": "integer"},
                location=OpenApiParameter.QUERY,
                description="每页数量"
            ),
            OpenApiParameter(
                name="config_type",
                type={"type": "string", "enum": ["basic", "calculation", "notification", "api"]},
                location=OpenApiParameter.QUERY,
                description="配置类型",
            ),
            OpenApiParameter(
                name="search",
                type={"type": "string"},
                location=OpenApiParameter.QUERY,
                description="搜索关键词"
            )
        ]
    ),
    create=extend_schema(
        summary="创建系统配置",
        description="创建新的系统配置项"
    ),
    retrieve=extend_schema(
        summary="获取系统配置详情",
        description="根据ID获取系统配置详情"
    ),
    update=extend_schema(
        summary="更新系统配置",
        description="更新指定的系统配置项"
    ),
    destroy=extend_schema(
        summary="删除系统配置",
        description="删除指定的系统配置项"
    )
)
class SystemConfigViewSet(viewsets.ModelViewSet):
    """
    系统配置视图集
    
    提供系统配置的CRUD操作，支持：
    1. 获取配置列表（分页、过滤、搜索）
    2. 获取单个配置详情
    3. 创建新配置
    4. 更新配置
    5. 删除配置
    6. 批量更新配置
    7. 导入导出配置
    8. 重置配置到默认值
    """
    queryset = SystemConfig.objects.all().order_by('config_type', 'key')
    serializer_class = SystemConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_public', 'config_type']
    search_fields = ['key', 'description']
    ordering_fields = ['created_at', 'key', 'id', 'config_type']
    ordering = ['config_type', 'key']
    pagination_class = StandardResultsSetPagination

    @method_decorator(cache_page(60 * 15))  # 缓存15分钟
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        """
        获取配置列表（已缓存15分钟）
        """
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        根据用户权限过滤配置项
        """
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)
        return queryset

    def perform_destroy(self, instance):
        """
        删除配置
        """
        instance.delete()
        # 删除缓存
        cache.delete(f'system_config_{instance.key}')
        cache.delete_pattern('system_config_list_*')

    @extend_schema(
        summary="批量更新配置",
        description="""
        批量更新系统配置
        
        请求体格式：
        ```json
        {
            "configs": [
                {
                    "key": "site_name",
                    "value": "新站点名称",
                    "description": "站点名称"
                },
                {
                    "key": "logo_url",
                    "value": "http://example.com/logo.png"
                }
            ]
        }
        ```
        """,
        request=ConfigBatchUpdateSerializer,
        responses={200: SystemConfigSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """
        批量更新配置
        
        请求体格式：
        {
            "configs": [
                {
                    "key": "site_name",
                    "value": "新站点名称",
                    "description": "站点名称"
                },
                {
                    "key": "logo_url",
                    "value": "http://example.com/logo.png"
                }
            ]
        }
        """
        serializer = ConfigBatchUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        configs = serializer.save()
        
        return Response(
            SystemConfigSerializer(configs, many=True).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="导入配置",
        description="导入JSON格式的配置文件",
        request={'multipart/form-data': {'file': {"type": "string", "format": "binary"}}},
        responses={200: SystemConfigSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def import_configs(self, request):
        """
        导入配置
        
        支持JSON格式的配置文件导入
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': '请上传配置文件'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        config_file = request.FILES['file']
        try:
            configs = json.loads(config_file.read())
            serializer = ConfigBatchUpdateSerializer(
                data={'configs': configs},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            updated_configs = serializer.save()
            
            return Response({
                'message': f'成功导入 {len(updated_configs)} 个配置项',
                'configs': SystemConfigSerializer(updated_configs, many=True).data
            })
        except json.JSONDecodeError:
            return Response(
                {'error': '无效的JSON文件格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="导出配置",
        description="导出所有系统配置为JSON文件",
        responses={(200, 'application/json'): {"type": "string", "format": "binary"}}
    )
    @action(detail=False, methods=['get'])
    def export_configs(self, request):
        """
        导出配置
        
        将当前所有配置导出为JSON文件
        """
        configs = self.get_queryset()
        serializer = SystemConfigSerializer(configs, many=True)
        response = HttpResponse(
            json.dumps(serializer.data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="system_configs.json"'
        return response

    @extend_schema(
        summary="重置默认配置",
        description="将所有配置重置为系统默认值",
        responses={200: SystemConfigSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def reset_defaults(self, request):
        """
        重置配置到默认值
        """
        # 默认配置定义
        default_configs = [
            # 基础设置
            {
                'key': 'site_name',
                'value': '运费计算系统',
                'description': '站点名称',
                'is_public': True,
                'config_type': 'basic',
                'validation_rules': {
                    'type': 'string',
                    'max_length': 100
                }
            },
            {
                'key': 'company_name',
                'value': '示例公司',
                'description': '公司名称',
                'is_public': True,
                'config_type': 'basic',
                'validation_rules': {
                    'type': 'string',
                    'max_length': 100
                }
            },
            {
                'key': 'contact_email',
                'value': 'support@example.com',
                'description': '联系邮箱',
                'is_public': True,
                'config_type': 'basic',
                'validation_rules': {
                    'type': 'email'
                }
            },
            {
                'key': 'language',
                'value': 'zh_CN',
                'description': '系统语言',
                'is_public': True,
                'config_type': 'basic',
                'validation_rules': {
                    'type': 'string',
                    'pattern': '^[a-z]{2}_[A-Z]{2}$'
                }
            },
            {
                'key': 'available_languages',
                'value': [
                    {'code': 'zh_CN', 'name': '简体中文'},
                    {'code': 'en_US', 'name': 'English (US)'}
                ],
                'description': '可用语言列表',
                'is_public': True,
                'config_type': 'basic',
                'validation_rules': {
                    'type': 'json'
                }
            },
            {
                'key': 'theme',
                'value': {
                    'mode': 'light',
                    'primary_color': '#409EFF',
                    'success_color': '#67C23A',
                    'warning_color': '#E6A23C',
                    'danger_color': '#F56C6C',
                    'info_color': '#909399',
                    'font_family': 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial',
                    'border_radius': '4px'
                },
                'description': '主题设置',
                'is_public': True,
                'config_type': 'basic',
                'validation_rules': {
                    'type': 'json'
                }
            },
            {
                'key': 'available_themes',
                'value': [
                    {
                        'name': '默认亮色',
                        'mode': 'light',
                        'primary_color': '#409EFF'
                    },
                    {
                        'name': '默认暗色',
                        'mode': 'dark',
                        'primary_color': '#409EFF'
                    },
                    {
                        'name': '商务蓝',
                        'mode': 'light',
                        'primary_color': '#2B5DE0'
                    },
                    {
                        'name': '科技绿',
                        'mode': 'light',
                        'primary_color': '#18A058'
                    }
                ],
                'description': '可用主题列表',
                'is_public': True,
                'config_type': 'basic',
                'validation_rules': {
                    'type': 'json'
                }
            },

            # 计算设置
            {
                'key': 'volume_weight_factor',
                'value': 6000,
                'description': '体积重系数(cm³/kg)',
                'is_public': True,
                'config_type': 'calculation',
                'validation_rules': {
                    'type': 'number',
                    'min': 1,
                    'max': 10000
                }
            },

            # 通知设置
            {
                'key': 'enable_email_notification',
                'value': False,
                'description': '启用邮件通知',
                'is_public': True,
                'config_type': 'notification',
                'validation_rules': {
                    'type': 'boolean'
                }
            },
            {
                'key': 'smtp_settings',
                'value': {
                    'host': 'smtp.example.com',
                    'port': 587,
                    'username': '',
                    'password': '',
                    'use_tls': True
                },
                'description': 'SMTP服务器设置',
                'is_public': False,
                'config_type': 'notification'
            },

            # API设置
            {
                'key': 'api_rate_limit',
                'value': 1000,
                'description': 'API请求限制(次/小时)',
                'is_public': False,
                'config_type': 'api',
                'validation_rules': {
                    'type': 'number',
                    'min': 1,
                    'max': 10000
                }
            }
        ]
        
        serializer = ConfigBatchUpdateSerializer(
            data={'configs': default_configs},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        configs = serializer.save()
        
        # 清除所有配置缓存
        cache.delete_pattern('system_config_*')
        
        return Response({
            'message': '配置已重置为默认值',
            'configs': SystemConfigSerializer(configs, many=True).data
        })

    @extend_schema(
        summary="清除配置缓存",
        description="清除所有系统配置的缓存",
        responses={200: {"type": "object"}}
    )
    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """
        清除配置缓存
        """
        cache.delete_pattern('system_config_*')
        return Response({'message': '配置缓存已清除'})

    @extend_schema(
        summary="获取配置类型列表",
        description="获取所有可用的配置类型",
        responses={200: {"type": "object"}}
    )
    @action(detail=False, methods=['get'])
    def types(self, request):
        """
        获取配置类型列表
        """
        return Response(dict(SystemConfig.CONFIG_TYPES))


@extend_schema(
    tags=['系统监控'],
    responses={200: HealthCheckSerializer},
    description='健康检查接口'
)
class HealthCheckView(GenericAPIView):
    """健康检查视图"""
    permission_classes = [AllowAny]
    serializer_class = HealthCheckSerializer

    def get(self, request) -> Response:
        """获取系统健康状态"""
        try:
            # 检查数据库连接
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # 检查Redis连接
            cache.set('health_check', 'ok', 10)
            cache.get('health_check')
            
            # 检查系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            data = {
                'status': 'healthy',
                'database': True,
                'cache': True,
                'celery': True,
                'uptime': int(time.time() - psutil.boot_time()),
                'system': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'disk_usage': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': disk.percent
                    }
                },
                'timestamp': timezone.now()
            }
            
            serializer = self.get_serializer(data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {
                    'status': 'unhealthy',
                    'error': str(e)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


@extend_schema(
    tags=['系统监控'],
    responses={200: MetricsSerializer},
    description='获取系统指标数据'
)
class MetricsView(GenericAPIView):
    """系统指标视图"""
    permission_classes = [AllowAny]
    serializer_class = MetricsSerializer

    def get(self, request) -> Response:
        """获取系统指标数据"""
        try:
            # 获取系统资源使用情况
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取数据库指标
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                migration_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                user_count = cursor.fetchone()[0]
            
            # 获取缓存指标
            cache_info = {
                'keys': 0,
                'hits': 0,
                'misses': 0,
                'hit_rate': 0
            }
            try:
                redis_client = cache.client.get_client()
                cache_info = redis_client.info()
            except RedisError:
                pass
            
            data = {
                'total_users': user_count,
                'active_users': user_count,  # 这里可以根据实际需求修改活跃用户的计算方式
                'total_requests': 0,  # 需要实现请求计数
                'average_response_time': 0.0,  # 需要实现响应时间统计
                'error_rate': 0.0,  # 需要实现错误率统计
                'cache_hit_rate': cache_info.get('hit_rate', 0),
                'system': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'disk_usage': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': disk.percent
                    },
                    'boot_time': psutil.boot_time()
                },
                'database': {
                    'migration_count': migration_count,
                    'user_count': user_count,
                    'connections': len(connection.connection_pool._connections)
                },
                'cache': {
                    'keys': cache_info.get('keys', 0),
                    'hits': cache_info.get('hits', 0),
                    'misses': cache_info.get('misses', 0),
                    'hit_rate': cache_info.get('hit_rate', 0)
                },
                'timestamp': timezone.now()
            }
            
            serializer = self.get_serializer(data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
@extend_schema(tags=['系统管理'])
class LoginView(APIView):
    """
    用户登录视图
    """
    authentication_classes = []  # 禁用认证
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(
        request=UserLoginSerializer,
        responses={200: UserLoginSerializer},
        description='用户登录'
    )
    def post(self, request):
        """处理登录请求"""
        # 禁用CSRF检查
        request._dont_enforce_csrf_checks = True
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': '用户名或密码错误'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': '用户已被禁用'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 执行登录
        login(request, user)
        
        # 生成Token
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff
            }
        })


@extend_schema(tags=['系统管理'],
    responses={200: {"type": "object"}},
    description='获取API错误信息'
)
class APIErrorView(APIView):
    """
    API错误视图
    """
    permission_classes = [AllowAny]
    serializer_class = APIErrorSerializer

    @extend_schema(
        responses={200: {"type": "object"}},
        description='获取API错误信息'
    )
    def get(self, request):
        """
        获取错误信息
        """
        error_code = request.GET.get('code', 'UNKNOWN_ERROR')
        language = request.GET.get('lang', 'zh-hans')
        
        # 从缓存获取错误信息
        cache_key = f'error_message_{error_code}_{language}'
        error_message = cache.get(cache_key)
        
        if not error_message:
            # 如果缓存中没有，从数据库获取
            try:
                error_config = SystemConfig.objects.get(
                    key=f'error_message_{error_code}',
                    is_deleted=False
                )
                error_message = error_config.value.get(language, '未知错误')
                # 设置缓存
                cache.set(cache_key, error_message, 3600)
            except SystemConfig.DoesNotExist:
                error_message = '未知错误'
        
        return Response({
            'code': error_code,
            'message': error_message
        })
    
    @extend_schema(
        request=APIErrorSerializer,
        responses={200: APIErrorSerializer},
        description='报告API错误'
    )
    def post(self, request):
        """
        报告错误
        """
        error_data = request.data
        
        try:
            # 验证错误数据
            if not isinstance(error_data, dict):
                raise InvalidParameterException('错误数据格式不正确')
            
            required_fields = ['code', 'message', 'url']
            for field in required_fields:
                if field not in error_data:
                    raise InvalidParameterException(f'缺少必要字段: {field}')
            
            # 记录错误信息
            # TODO: 实现错误记录逻辑
            
            return Response({
                'message': '错误信息已记录'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(
        summary="获取通知列表",
        description="获取当前用户的所有通知"
    ),
    create=extend_schema(
        summary="创建通知",
        description="创建新的通知"
    ),
    retrieve=extend_schema(
        summary="获取通知详情",
        description="获取指定通知的详细信息",
        parameters=[
            OpenApiParameter(
                name="pk",
                type={"type": "integer"},
                location=OpenApiParameter.PATH,
                description="通知ID"
            )
        ]
    ),
    update=extend_schema(
        summary="更新通知",
        description="更新指定的通知",
        parameters=[
            OpenApiParameter(
                name="pk",
                type={"type": "integer"},
                location=OpenApiParameter.PATH,
                description="通知ID"
            )
        ]
    ),
    destroy=extend_schema(
        summary="删除通知",
        description="删除指定的通知",
        parameters=[
            OpenApiParameter(
                name="pk",
                type={"type": "integer"},
                location=OpenApiParameter.PATH,
                description="通知ID"
            )
        ]
    )
)
@extend_schema(tags=['通知管理'])
class NotificationViewSet(viewsets.ModelViewSet):
    """
    通知视图集
    
    提供通知的增删改查操作：
    - 获取通知列表
    - 创建新通知
    - 获取通知详情
    - 更新通知
    - 删除通知
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="获取通知设置列表",
        description="获取当前用户的所有通知设置"
    ),
    create=extend_schema(
        summary="创建通知设置",
        description="创建新的通知设置"
    ),
    retrieve=extend_schema(
        summary="获取通知设置详情",
        description="获取指定通知设置的详细信息",
        parameters=[
            OpenApiParameter(
                name="pk",
                type={"type": "integer"},
                location=OpenApiParameter.PATH,
                description="通知设置ID"
            )
        ]
    ),
    update=extend_schema(
        summary="更新通知设置",
        description="更新指定的通知设置",
        parameters=[
            OpenApiParameter(
                name="pk",
                type={"type": "integer"},
                location=OpenApiParameter.PATH,
                description="通知设置ID"
            )
        ]
    ),
    destroy=extend_schema(
        summary="删除通知设置",
        description="删除指定的通知设置",
        parameters=[
            OpenApiParameter(
                name="pk",
                type={"type": "integer"},
                location=OpenApiParameter.PATH,
                description="通知设置ID"
            )
        ]
    )
)
@extend_schema(tags=['通知管理'])
class NotificationSettingsViewSet(viewsets.ModelViewSet):
    """
    通知设置视图集
    
    提供通知设置的增删改查操作：
    - 获取通知设置列表
    - 创建新通知设置
    - 获取通知设置详情
    - 更新通知设置
    - 删除通知设置
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSettingsSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return NotificationSettings.objects.none()
        return NotificationSettings.objects.filter(user=self.request.user)


@extend_schema(
    tags=['系统监控'],
    description='获取任务历史记录',
    responses={200: {"type": "object"}}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def task_history(request):
    """
    获取任务历史记录
    """
    try:
        days = int(request.GET.get('days', 7))
        limit = int(request.GET.get('limit', 100))
        task_type = request.GET.get('type')
        
        # 构建查询条件
        cutoff_date = timezone.now() - timedelta(days=days)
        query = TaskResult.objects.filter(date_done__gte=cutoff_date)
        
        if task_type:
            query = query.filter(task_name__contains=task_type)
        
        # 获取任务记录
        tasks = query.order_by('-date_done')[:limit]
        
        # 统计任务状态
        status_counts = query.values('status').annotate(count=models.Count('id'))
        
        data = {
            'tasks': [{
                'task_id': task.task_id,
                'task_name': task.task_name,
                'status': task.status,
                'result': task.result,
                'date_done': task.date_done,
                'traceback': task.traceback if task.status == 'FAILURE' else None
            } for task in tasks],
            'summary': {
                'total': query.count(),
                'status_counts': {
                    item['status']: item['count']
                    for item in status_counts
                }
            }
        }
        
        return Response(data)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BaseAPIView(APIView):
    """
    基础API视图类
    提供统一的响应格式和常用方法
    所有API视图都应继承自此类
    """
    
    def success_response(self, data=None, message='操作成功', extra_fields=None):
        """成功响应"""
        from apps.core.responses import APIResponse
        return APIResponse.success(data=data, message=message, extra_fields=extra_fields)

    def error_response(self, message, code='ERROR', status_code=status.HTTP_400_BAD_REQUEST, data=None):
        """错误响应"""
        from apps.core.responses import APIResponse
        return APIResponse.error(message=message, code=code, status_code=status_code, data=data)
        
    def validation_error(self, errors, message='数据验证失败'):
        """验证错误响应"""
        from apps.core.responses import APIResponse
        return APIResponse.validation_error(errors=errors, message=message)
    
    def not_found(self, message='资源不存在', code='NOT_FOUND'):
        """资源不存在响应"""
        from apps.core.responses import APIResponse
        return APIResponse.not_found(message=message, code=code)
    
    def handle_exception(self, exc):
        """统一异常处理"""
        if isinstance(exc, APIException):
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, (list, dict)):
                    return self.validation_error(exc.detail)
                return self.error_response(
                    message=str(exc.detail),
                    code=getattr(exc, 'default_code', 'ERROR'),
                    status_code=exc.status_code
                )
            
        if isinstance(exc, Http404):
            return self.not_found()
            
        if isinstance(exc, (ValidationError, InvalidParameterException)):
            return self.validation_error(str(exc))
            
        if isinstance(exc, PermissionDenied):
            return self.error_response(
                message='没有权限执行此操作',
                code='PERMISSION_DENIED',
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        # 未处理的异常记录日志
        logger.exception(f"未处理的异常: {str(exc)}")
        return self.error_response(
            message='服务器内部错误',
            code='INTERNAL_SERVER_ERROR',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['系统监控'],
    description='获取性能统计数据',
    responses={200: {"type": "object"}}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def performance_stats(request):
    """
    获取系统性能统计数据
    """
    try:
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 获取数据库连接信息
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
        
        # 获取Celery任务统计
        total_tasks = TaskResult.objects.count()
        success_tasks = TaskResult.objects.filter(status='SUCCESS').count()
        failed_tasks = TaskResult.objects.filter(status='FAILURE').count()
        
        data = {
            'system': {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': float(disk.percent)
                }
            },
            'database': {
                'version': db_version,
                'migration_count': migration_count,
                'connections': len(connection.connection_pool._connections)
            },
            'tasks': {
                'total': total_tasks,
                'success': success_tasks,
                'failed': failed_tasks,
                'success_rate': (success_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'timestamp': timezone.now()
        }
        
        return Response(data)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BaseViewSet(viewsets.ModelViewSet):
    """
    基础视图集类
    提供统一的响应格式和异常处理
    所有视图集都应继承自此类
    """
    # 统一使用标准分页类
    pagination_class = StandardResultsSetPagination
    
    def get_model_name(self):
        """获取模型名称"""
        if hasattr(self, 'queryset'):
            return self.queryset.model._meta.verbose_name
        return '资源'
    
    def success_response(self, data=None, message='操作成功', extra_fields=None):
        """成功响应"""
        from apps.core.responses import APIResponse
        return APIResponse.success(data=data, message=message, extra_fields=extra_fields)

    def error_response(self, message, code='ERROR', status_code=status.HTTP_400_BAD_REQUEST, data=None):
        """错误响应"""
        from apps.core.responses import APIResponse
        return APIResponse.error(message=message, code=code, status_code=status_code, data=data)
        
    def validation_error(self, errors, message='数据验证失败'):
        """验证错误响应"""
        from apps.core.responses import APIResponse
        return APIResponse.validation_error(errors=errors, message=message)
    
    def not_found(self, message='资源不存在', code='NOT_FOUND'):
        """资源不存在响应"""
        from apps.core.responses import APIResponse
        return APIResponse.not_found(message=message, code=code)
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个资源（覆盖以实现统一响应格式）"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(
                data=serializer.data,
                message=f'获取{self.get_model_name()}成功'
            )
        except Http404:
            return self.not_found()
        except Exception as e:
            logger.exception(f"获取资源失败: {str(e)}")
            return self.error_response(message=str(e))
    
    def create(self, request, *args, **kwargs):
        """创建资源（覆盖以实现统一响应格式）"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.validation_error(serializer.errors)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return self.success_response(
                data=serializer.data,
                message=f'{self.get_model_name()}创建成功'
            )
        except Exception as e:
            logger.exception(f"创建资源失败: {str(e)}")
            return self.error_response(message=str(e))
    
    def update(self, request, *args, **kwargs):
        """更新资源（覆盖以实现统一响应格式）"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return self.validation_error(serializer.errors)
        
        try:
            self.perform_update(serializer)
            
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
                
            return self.success_response(
                data=serializer.data,
                message=f'{self.get_model_name()}更新成功'
            )
        except Exception as e:
            logger.exception(f"更新资源失败: {str(e)}")
            return self.error_response(message=str(e))
    
    def destroy(self, request, *args, **kwargs):
        """删除资源（覆盖以实现统一响应格式）"""
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return self.success_response(
                message=f'{self.get_model_name()}删除成功'
            )
        except Exception as e:
            logger.exception(f"删除资源失败: {str(e)}")
            return self.error_response(message=str(e))
            
    def list(self, request, *args, **kwargs):
        """获取资源列表（覆盖以实现统一响应格式）"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # 处理分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)
        
    def get_paginated_response(self, data):
        """获取分页响应（覆盖以实现统一响应格式）"""
        assert self.paginator is not None
        return self.success_response(
            data=data,
            extra_fields={
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
                'page_size': self.paginator.page_size,
                'current_page': self.paginator.page.number,
                'total_pages': self.paginator.page.paginator.num_pages
            }
        )


@extend_schema(
    tags=['系统配置'],
    description='获取应用配置',
    responses={200: {"type": "array"}}
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def configs_view(request):
    """
    返回系统配置信息的视图。
    特别处理OPTIONS请求以解决CORS问题。
    """
    # 首先处理OPTIONS请求
    if request.method == 'OPTIONS':
        response = HttpResponse()
        origin = request.headers.get('Origin')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Requested-With'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'  # 24小时
        return response
    
    # 正常处理GET请求
    configs = SystemConfig.objects.filter(is_active=True).order_by('key')
    config_data = {
        "apiVersion": "1.0",
        "apiBaseUrl": settings.API_BASE_URL if hasattr(settings, 'API_BASE_URL') else "/api/v1/",
        "debug": settings.DEBUG,
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "platformName": "物流运费计算系统",
        "configs": {config.key: config.value for config in configs}
    }
    
    response = JsonResponse(config_data)
    
    # 添加CORS头
    origin = request.headers.get('Origin')
    if origin:
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
    
    return response


# CSRF Token 视图
@ensure_csrf_cookie
def csrf_token_view(request):
    """
    获取CSRF Token的视图。
    使用 @ensure_csrf_cookie 装饰器确保响应中设置了CSRF cookie。
    """
    token = get_token(request)
    return JsonResponse({
        'status': 'success',
        'csrf_token': token
    })


@api_view(['POST', 'GET', 'OPTIONS'])
@authentication_classes([])  # 完全禁用认证
@permission_classes([AllowAny])
def slow_request_monitor(request):
    """记录前端上报的慢请求数据"""
    # 预检请求处理
    if request.method == 'OPTIONS':
        response = HttpResponse()
        origin = request.headers.get('Origin', '')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, X-CSRFTOKEN, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'  # 缓存预检结果24小时
        return response
        
    try:
        # 记录请求相关信息，便于调试
        logger.info(f"慢请求监控接收请求 - 方法: {request.method}")
        logger.debug(f"慢请求监控headers: {request.headers}")
        logger.debug(f"Content-Type: {request.content_type}")
        
        # 记录数据
        data = {}
        if request.method == 'POST':
            if request.body:
                try:
                    # 尝试直接从请求体解析JSON
                    if isinstance(request.body, bytes):
                        data = json.loads(request.body.decode('utf-8'))
                    else:
                        data = json.loads(request.body)
                except json.JSONDecodeError:
                    # 尝试使用request.data (已经解析的数据)
                    data = request.data if hasattr(request, 'data') and request.data else {}
                    logger.warning(f"无法直接解析JSON请求体，使用request.data: {data}")
                
            logger.info(f"慢请求监控数据: {data}")
            
            # 处理数据
            if data:
                try:
                    # 存储到缓存中，避免频繁写入数据库
                    slow_requests = cache.get('slow_requests', [])
                    slow_requests.append({
                        'url': data.get('url', '未知'),
                        'duration': data.get('duration', 0),
                        'timestamp': data.get('timestamp', int(time.time() * 1000)),
                        'success': data.get('success', False),
                        'resource_type': data.get('resourceType', '未知'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', '未知'),
                        'ip': request.META.get('REMOTE_ADDR', '未知')
                    })
                    # 只保留最近100条记录
                    if len(slow_requests) > 100:
                        slow_requests = slow_requests[-100:]
                    cache.set('slow_requests', slow_requests, 86400)  # 保存24小时
                    
                    # 记录到日志
                    logger.warning(f"前端慢请求: {data.get('url')} - 耗时: {data.get('duration')}ms - 资源类型: {data.get('resourceType')}")
                except Exception as e:
                    logger.error(f"处理慢请求数据失败: {str(e)}")
        
        # 返回成功响应
        response_data = {
            'status': 'success',
            'message': '慢请求数据已记录',
            'timestamp': int(time.time() * 1000)
        }
        
        # 创建响应并添加CORS头
        response = JsonResponse(response_data)
        origin = request.headers.get('Origin', '')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, X-CSRFTOKEN, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    except Exception as e:
        logger.exception(f"慢请求监控异常: {str(e)}")
        
        # 创建错误响应并添加CORS头
        response = JsonResponse({
            'status': 'error',
            'message': f"处理请求失败: {str(e)}"
        }, status=500)
        
        # 确保错误响应也有CORS头
        origin = request.headers.get('Origin', '')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, X-CSRFTOKEN, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
            
        return response


@api_view(['POST', 'GET', 'OPTIONS'])
@authentication_classes([])  # 完全禁用认证
@permission_classes([AllowAny])
def performance_monitor(request):
    """记录前端上报的性能数据"""
    # 预检请求处理
    if request.method == 'OPTIONS':
        response = HttpResponse()
        origin = request.headers.get('Origin', '')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, X-CSRFTOKEN, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'  # 缓存预检结果24小时
        return response
    
    try:
        # 获取性能数据
        data = {}
        if request.method == 'POST':
            if request.body:
                try:
                    # 尝试直接从请求体解析JSON
                    if isinstance(request.body, bytes):
                        data = json.loads(request.body.decode('utf-8'))
                    else:
                        data = json.loads(request.body)
                except json.JSONDecodeError:
                    # 尝试使用request.data (已经解析的数据)
                    data = request.data if hasattr(request, 'data') and request.data else {}
                    logger.warning(f"无法直接解析JSON请求体，使用request.data: {data}")
            
        # 记录性能数据
        logger.info(f"性能监控数据: {data}")
        
        # TODO: 处理性能数据，后续可添加存储到缓存或数据库的逻辑
        
        # 返回成功响应
        response_data = {
            'status': 'success',
            'message': '性能数据已记录',
            'timestamp': int(time.time() * 1000)
        }
        
        # 创建响应并添加CORS头
        response = JsonResponse(response_data)
        origin = request.headers.get('Origin', '')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, X-CSRFTOKEN, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    except Exception as e:
        logger.exception(f"性能监控异常: {str(e)}")
        
        # 创建错误响应并添加CORS头
        response = JsonResponse({
            'status': 'error',
            'message': f"处理请求失败: {str(e)}"
        }, status=500)
        
        # 确保错误响应也有CORS头
        origin = request.headers.get('Origin', '')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, X-CSRFTOKEN, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
            
        return response


# 添加配置API视图
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def configs(request):
    """
    获取系统配置API
    """
    try:
        # 获取所有公开的系统配置
        configs = SystemConfig.objects.filter(is_public=True)
        
        # 序列化配置数据
        serializer = SystemConfigSerializer(configs, many=True)
        
        return JsonResponse({
            'status': 'success',
            'message': '配置加载成功',
            'data': serializer.data
        })
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'配置加载失败: {str(e)}',
            'data': []
        }, status=500) 