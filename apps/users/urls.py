from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, RoleViewSet, UserLoginLogViewSet, 
    get_csrf_token, me_view, 
    password_reset_request, password_reset_confirm,
    CustomTokenObtainPairView, CustomTokenRefreshView, auth_test,
    login_view
)

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('roles', RoleViewSet)
router.register('login_logs', UserLoginLogViewSet, basename='login_logs')

# API路由
urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/test/', auth_test, name='auth_test'),
    path('auth/csrf/', get_csrf_token, name='csrf_token'),
    path('auth/login/', login_view, name='login'),
    path('me/', me_view, name='me_view'),
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/', password_reset_confirm, name='password_reset_confirm'),
] 