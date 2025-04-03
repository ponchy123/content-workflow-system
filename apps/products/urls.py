from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
    path('product-types/', ProductViewSet.as_view({'get': 'product_types'}), name='product-types'),
    path('base-fees/by_product/', ProductViewSet.as_view({'get': 'base_fees_by_product', 'post': 'update_base_fees_by_product', 'put': 'base_fees_by_product'}), name='base_fees_by_product'),
    path('surcharges/by_product/', ProductViewSet.as_view({'get': 'surcharges_by_product', 'post': 'update_surcharges_by_product'}), name='surcharges_by_product'),
    path('peak-season-surcharges/by_product/', ProductViewSet.as_view({'get': 'peak_season_surcharges_by_product', 'post': 'update_peak_season_surcharges_by_product'}), name='peak_season_surcharges_by_product'),
    path('products/clear-cache/<str:pk>/', ProductViewSet.as_view({'post': 'clear_cache'}), name='product-clear-cache'),
]