from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FuelRateViewSet, FuelRateHistoryViewSet

# 创建路由器实例
router = DefaultRouter()

# 注册视图集，使用正确的basename
router.register(r'rates', FuelRateViewSet, basename='fuelrate')
router.register(r'histories', FuelRateHistoryViewSet, basename='fuelratehistory')

urlpatterns = [
    path('', include(router.urls)),
]
