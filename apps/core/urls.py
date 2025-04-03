from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceProviderViewSet, SystemConfigViewSet, HealthCheckView, MetricsView,
    LoginView, APIErrorView, task_history, NotificationViewSet,
    NotificationSettingsViewSet, performance_stats, configs_view,
    csrf_token_view, slow_request_monitor, performance_monitor
)
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

router = DefaultRouter()
router.register(r'service-providers', ServiceProviderViewSet)
router.register(r'system-configs', SystemConfigViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-settings', NotificationSettingsViewSet, basename='notification-settings')

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
    path('health/', HealthCheckView.as_view(), name='health'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
    path('login/', LoginView.as_view(), name='login'),
    path('error/', APIErrorView.as_view(), name='api_error'),
    path('tasks/history/', task_history, name='task_history'),
    path('monitoring/performance/', performance_monitor, name='performance_monitor'),
    path('monitoring/slow-request/', slow_request_monitor, name='slow_request_monitor'),
    path('configs/', configs_view, name='configs_view'),
    path('csrf/', csrf_token_view, name='csrf_token'),
] 