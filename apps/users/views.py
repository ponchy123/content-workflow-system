from django.urls import path, include
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.http import JsonResponse
from .models import UserProfile, Role, UserLoginLog
from .serializers import (
    UserSerializer, UserProfileSerializer,
    RoleSerializer, UserLoginLogSerializer
)
from apps.core.views import BaseViewSet, BaseAPIView
from apps.core.responses import APIResponse
from apps.core.decorators import db_connection_retry
from rest_framework import serializers
from django.middleware.csrf import get_token
from rest_framework.permissions import AllowAny
import logging
from drf_spectacular.utils import extend_schema
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import UserRateThrottle

User = get_user_model()
logger = logging.getLogger(__name__)


class CSRFTokenSerializer(serializers.Serializer):
    csrf_token = serializers.CharField(read_only=True)


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
@csrf_exempt
def get_csrf_token(request):
    """
    获取CSRF Token的视图
    """
    try:
        if request.method == 'OPTIONS':
            response = JsonResponse({})
        else:
            response = JsonResponse({'csrf_token': get_token(request)})
        
        # 添加CORS头
        origin = request.headers.get('Origin', '')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS, POST'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization'
            response['Access-Control-Allow-Credentials'] = 'true'
            if request.method == 'OPTIONS':
                response['Access-Control-Max-Age'] = '86400'  # 24小时
        
        return response
    except Exception as e:
        logger.error(f"获取CSRF token失败: {str(e)}")
        return JsonResponse({'error': '获取CSRF token失败'}, status=500)


@extend_schema(
    tags=['用户管理'],
    description='获取当前登录用户信息',
    responses={200: UserSerializer}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    """
    获取当前登录用户信息的独立视图函数
    """
    try:
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            # 如果用户未认证，尝试从JWT令牌恢复
            auth_header = request.META.get('HTTP_AUTHORIZATION', None)
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    token = auth_header.split(' ')[1]
                    jwt_auth = JWTAuthentication()
                    validated_token = jwt_auth.get_validated_token(token)
                    user = jwt_auth.get_user(validated_token)
                    
                    if user:
                        # 找到用户，恢复会话
                        if hasattr(request, 'session'):
                            request.session['_auth_user_id'] = str(user.pk)
                            request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
                            request.session.modified = True
                        
                        # 使用恢复的用户继续
                        request.user = user
                        logger.info(f"从JWT令牌恢复用户身份: {user.username}")
                    else:
                        return Response({
                            'status': 'error',
                            'message': '用户未认证',
                            'code': 'NOT_AUTHENTICATED'
                        }, status=status.HTTP_401_UNAUTHORIZED)
                except Exception as e:
                    logger.error(f"JWT身份恢复失败: {str(e)}")
                    return Response({
                        'status': 'error',
                        'message': '用户未认证',
                        'code': 'NOT_AUTHENTICATED'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'status': 'error',
                    'message': '用户未认证',
                    'code': 'NOT_AUTHENTICATED'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 记录用户信息访问
        logger.info(f"获取用户信息: {request.user.pk}, {request.user.username}")
        
        # 更新会话活动时间
        if hasattr(request, 'session'):
            request.session['last_activity'] = timezone.now().isoformat()
            request.session.modified = True
        
        # 序列化并返回用户信息
        serializer = UserSerializer(request.user)
        
        # 符合前端期望的格式
        return Response({
            'status': 'success',
            'message': '获取用户信息成功',
            'data': serializer.data
        })
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': '获取用户信息失败',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='login')
class UserViewSet(BaseViewSet):
    """
    用户视图集
    """
    queryset = User.objects.filter(is_active=True).order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active', 'department']
    search_fields = ['username', 'email', 'mobile']
    ordering_fields = ['date_joined', 'username']
    model_name = '用户'

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        用户登录
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return self.validation_error(
                errors={'non_field_errors': ['用户名和密码不能为空']},
                message='用户名和密码不能为空'
            )
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return self.error_response(
                message='用户名或密码错误',
                code='INVALID_CREDENTIALS',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
        if not user.is_active:
            return self.error_response(
                message='账号已被禁用',
                code='ACCOUNT_DISABLED',
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        # 生成token
        refresh = RefreshToken.for_user(user)
        
        # 记录登录日志
        UserLoginLog.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_time=timezone.now()
        )
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return self.success_response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': self.get_serializer(user).data
        }, message='登录成功')
        
    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def me(self, request):
        """
        获取当前登录用户信息
        """
        logger.info(f"用户ME接口被调用，用户验证状态：{request.user.is_authenticated}")
        
        if not request.user.is_authenticated:
            logger.warning("用户未登录，返回401错误")
            return self.error_response(
                message='未登录',
                code='NOT_AUTHENTICATED',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        logger.info(f"用户已登录，ID: {request.user.pk}, 用户名: {request.user.username}")
        serializer = self.get_serializer(request.user)
        return self.success_response(data=serializer.data)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        获取当前用户信息
        """
        if not request.user.is_authenticated:
            return self.error_response(
                message='未登录',
                code='NOT_AUTHENTICATED',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
        serializer = self.get_serializer(request.user)
        return self.success_response(data=serializer.data)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_update(self, serializer):
        return super().perform_update(serializer)


class RoleViewSet(BaseViewSet):
    """
    角色视图集
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']
    search_fields = ['role_name', 'description']
    ordering_fields = ['created_at', 'role_name']
    model_name = '角色'

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_update(self, serializer):
        return super().perform_update(serializer)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_destroy(self, instance):
        """
        删除角色
        """
        instance.delete()


class UserLoginLogViewSet(BaseViewSet):
    """
    用户登录日志视图集
    """
    serializer_class = UserLoginLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'login_time']
    search_fields = ['ip_address', 'user_agent']
    ordering_fields = ['login_time']
    model_name = '登录日志'
    
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def get_queryset(self):
        """
        获取查询集，普通用户只能查看自己的登录日志
        """
        if getattr(self, 'swagger_fake_view', False):
            return UserLoginLog.objects.none()
            
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return UserLoginLog.objects.all().order_by('-login_time')
        else:
            return UserLoginLog.objects.filter(user=user).order_by('-login_time')

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_update(self, serializer):
        return super().perform_update(serializer)

    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_destroy(self, instance):
        """
        删除登录日志
        """
        instance.delete()


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
@csrf_exempt
def login_view(request):
    """
    通用登录视图
    """
    if request.method == 'OPTIONS':
        response = Response()
        response["Allow"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response
    
    # 限流检查
    class LoginRateThrottle(UserRateThrottle):
        scope = 'login'
    
    throttle = LoginRateThrottle()
    if not throttle.allow_request(request, None):
        wait_time = throttle.wait()
        return Response({
            'status': 'error',
            'message': f'登录请求过于频繁，请在{wait_time}秒后重试',
            'code': 'throttled',
            'wait': wait_time
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # 处理登录请求
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'status': 'error',
                'message': '用户名和密码不能为空',
                'code': 'INVALID_CREDENTIALS'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user = authenticate(username=username, password=password)
        
        if user is None:
            # 增加登录失败日志
            logger.warning(f"用户登录失败: {username}, IP: {get_client_ip(request)}")
            return Response({
                'status': 'error',
                'message': '用户名或密码错误',
                'code': 'INVALID_CREDENTIALS'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        if not user.is_active:
            logger.warning(f"禁用用户尝试登录: {username}, IP: {get_client_ip(request)}")
            return Response({
                'status': 'error',
                'message': '账号已被禁用',
                'code': 'ACCOUNT_DISABLED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 记录登录日志
        try:
            UserLoginLog.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                login_status=True
            )
        except Exception as e:
            logger.error(f"记录登录日志失败: {str(e)}")
        
        # 生成token
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        # 设置刷新Token过期时间
        try:
            exp_timestamp = timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
            refresh_token_expires = int(exp_timestamp.timestamp())
        except (TypeError, ValueError, AttributeError, KeyError) as e:
            logger.error(f"计算Token过期时间失败: {str(e)}")
            refresh_token_expires = None
        
        # 获取用户信息
        user_serializer = UserSerializer(user)
        
        # 构建响应
        response_data = {
            'status': 'success',
            'message': '登录成功',
            'data': {
                'tokens': tokens,
                'user': user_serializer.data
            }
        }
        
        # 创建HTTP响应
        response = Response(response_data)
        
        # 设置Cookie
        if settings.SIMPLE_JWT.get('AUTH_COOKIE'):
            # 设置刷新Token的Cookie
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                str(refresh),
                expires=refresh_token_expires,
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
                httponly=settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
                samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
            )
        
        # 记录用户登录成功
        logger.info(f"用户 {user.username} 登录成功, IP: {get_client_ip(request)}")
        
        return response
    except Exception as e:
        # 捕获所有异常，确保返回友好的错误信息
        logger.exception(f"登录过程发生异常: {str(e)}")
        return Response({
            'status': 'error',
            'message': '登录过程发生错误',
            'detail': str(e) if settings.DEBUG else '系统错误'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetSerializer(serializers.Serializer):
    """密码重置请求序列化器"""
    email = serializers.EmailField(required=True)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    请求密码重置，发送重置邮件
    """
    serializer = PasswordResetSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    # 查找用户
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # 出于安全考虑，即使用户不存在也返回成功
        return Response(
            {"detail": "如果该邮箱已注册，我们已向其发送了密码重置链接。"},
            status=status.HTTP_200_OK
        )
    
    # 生成密码重置令牌
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # 构建重置链接
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password/{uid}/{token}/"
    
    # 构建邮件内容
    subject = "重置您的密码 - 物流运费订单系统"
    email_template_name = "email/password_reset_email.html"
    context = {
        "user": user,
        "reset_url": reset_url,
        "site_name": "物流运费订单系统",
        "uid": uid,
        "token": token,
    }
    email_html_message = render_to_string(email_template_name, context)
    
    # 发送邮件
    try:
        send_mail(
            subject=subject,
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=email_html_message,
            fail_silently=False,
        )
        logger.info(f"密码重置邮件已发送至 {user.email}")
        
        return Response(
            {"detail": "密码重置链接已发送到您的邮箱。"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"发送密码重置邮件失败: {str(e)}")
        return Response(
            {"detail": "发送邮件时出错，请稍后重试。"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """确认密码重置序列化器"""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不匹配"})
        return attrs


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    确认密码重置请求，设置新密码
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    uid = validated_data['uid']
    token = validated_data['token']
    new_password = validated_data['new_password']
    
    # 解码用户ID
    try:
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {"detail": "无效的用户ID或链接已过期"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证令牌
    if not default_token_generator.check_token(user, token):
        return Response(
            {"detail": "令牌无效或已过期"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 设置新密码
    user.set_password(new_password)
    user.save()
    
    # 记录密码更改日志
    logger.info(f"用户 {user.username} 成功重置密码")
    
    return Response(
        {"detail": "密码重置成功，请使用新密码登录"},
        status=status.HTTP_200_OK
    )


@method_decorator(csrf_exempt, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    自定义JWT令牌视图，兼容前端
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # 增加日志记录
        logger.info(f"Token视图收到请求: Method={request.method}, Path={request.path}, ContentType={request.content_type}")
        
        try:
            # 使用原始视图处理请求
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                # 获取用户信息
                username = request.data.get('username')
                user = None
                
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    logger.warning(f"用户名不存在: {username}")
                    return response
                    
                # 获取令牌数据
                token_data = response.data
                
                # 构建响应格式
                if user is not None:
                    user_serializer = UserSerializer(user)
                    # 将用户信息和令牌信息组合
                    response.data = {
                        'status': 'success',
                        'message': '登录成功',
                        'data': {
                            'tokens': {
                                'access': token_data.get('access'),
                                'refresh': token_data.get('refresh')
                            },
                            'user': user_serializer.data
                        }
                    }
                    
                    # 设置会话，确保用户登录状态持久化
                    if hasattr(request, 'session'):
                        request.session['_auth_user_id'] = str(user.pk)
                        request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
                        request.session['username'] = user.username
                        request.session.set_expiry(60 * 60 * 24 * 7)  # 7天
                        request.session.modified = True
                
                # 添加CORS头
                origin = request.headers.get('Origin', '')
                if origin:
                    response['Access-Control-Allow-Origin'] = origin
                    response['Access-Control-Allow-Credentials'] = 'true'
                    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
                    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
            
            return response
            
        except Exception as e:
            logger.error(f"Token视图处理异常: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"服务器内部错误: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def options(self, request, *args, **kwargs):
        """处理OPTIONS请求，支持CORS预检请求"""
        response = Response(status=status.HTTP_200_OK)
        origin = request.headers.get('Origin', '')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
            response['Access-Control-Max-Age'] = '86400'  # 24小时
        return response

@method_decorator(csrf_exempt, name='post')
class CustomTokenRefreshView(TokenRefreshView):
    """
    自定义的TokenRefreshView，添加自定义限流控制，并符合前端期望的格式
    """
    permission_classes = [AllowAny]
    throttle_scope = 'token_refresh'  # 使用token_refresh限流类别
    
    def post(self, request, *args, **kwargs):
        # 使用原始视图处理请求
        try:
            # 添加日志记录请求信息
            logger.info(f"收到token刷新请求，来源IP: {get_client_ip(request)}")
            
            # 检查请求频率是否合理，对于过快的刷新进行警告
            refresh_threshold_seconds = 5  # 刷新间隔阈值
            client_ip = get_client_ip(request)
            refresh_key = f"token_refresh_{client_ip}"
            
            # 检查距离上次刷新的时间
            last_refresh = cache.get(refresh_key)
            now = timezone.now()
            
            if last_refresh:
                time_diff = (now - last_refresh).total_seconds()
                if time_diff < refresh_threshold_seconds:
                    logger.warning(f"刷新请求过于频繁，间隔仅{time_diff}秒，IP: {client_ip}")
            
            # 更新最后刷新时间
            cache.set(refresh_key, now, timeout=60)
            
            # 处理刷新请求
            serializer = self.get_serializer(data=request.data)
            
            try:
                serializer.is_valid(raise_exception=True)
            except TokenError as e:
                # 捕获Token错误并返回友好消息
                logger.error(f"刷新令牌验证失败: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': '刷新令牌无效或已过期',
                    'code': 'token_not_valid'
                }, status=status.HTTP_401_UNAUTHORIZED)
            except ValidationError as e:
                # 捕获验证错误
                logger.error(f"刷新令牌数据验证失败: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': str(e),
                    'code': 'validation_error'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取刷新后的token
            data = serializer.validated_data
            
            # 记录令牌刷新成功
            logger.info(f"令牌刷新成功，用户IP: {client_ip}")
            
            # 符合前端期望的响应格式
            return Response({
                'status': 'success',
                'message': '刷新令牌成功',
                'access': data['access']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"刷新令牌时发生错误: {str(e)}")
            return Response({
                'status': 'error',
                'message': '刷新令牌时发生系统错误',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def options(self, request, *args, **kwargs):
        # 处理OPTIONS请求，适当设置CORS头
        response = Response()
        response["Allow"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response

# 帮助函数获取客户端IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip 

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def auth_test(request):
    """测试认证状态的简单视图"""
    return Response({
        'status': 'success', 
        'message': '认证成功', 
        'user': {
            'id': request.user.pk,
            'username': request.user.username,
            'is_authenticated': request.user.is_authenticated
        }
    }) 