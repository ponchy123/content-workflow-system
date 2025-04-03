from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZipZoneViewSet, RemoteAreaViewSet, import_zip_zones, import_remote_areas, direct_query_zip_zone
from django.http import JsonResponse
from django.db.models import Q
from .models import ZipZone, RemoteArea
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

router = DefaultRouter()
router.register(r'zip-zones', ZipZoneViewSet)
router.register(r'remote-areas', RemoteAreaViewSet)

# 添加视图函数获取邮编数据
@api_view(['GET'])
def postal_codes(request):
    """获取邮编分区列表"""
    zones = ZipZone.objects.all()[:10]  # 限制数量避免数据过多
    results = [
        {
            'provider_id': zone.provider_id,
            'origin_zip': zone.origin_zip,
            'dest_zip_start': zone.dest_zip_start,
            'dest_zip_end': zone.dest_zip_end,
            'zone_number': zone.zone_number
        } for zone in zones
    ]
    return JsonResponse({
        'results': results,
        'count': len(results),
        'page': 1,
        'page_size': 10
    })

@api_view(['GET'])
def postal_address(request, postal_code):
    """根据邮编获取地址信息"""
    # 查找邮编对应的偏远地区信息
    try:
        remote_area = RemoteArea.objects.filter(zip_code=postal_code).first()
        if remote_area:
            return JsonResponse({
                'provider_id': remote_area.provider_id,
                'origin_zip': remote_area.origin_zip,
                'zip_code': remote_area.zip_code,
                'remote_level': remote_area.remote_level
            })
        # 如果在偏远地区中找不到，查找分区信息
        zip_zone = ZipZone.objects.filter(
            Q(dest_zip_start__lte=postal_code) & 
            Q(dest_zip_end__gte=postal_code)
        ).first()
        if zip_zone:
            return JsonResponse({
                'provider_id': zip_zone.provider_id,
                'origin_zip': zip_zone.origin_zip,
                'zone_number': zip_zone.zone_number
            })
        return JsonResponse({
            'zip_code': postal_code,
            'message': '未找到相关信息'
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def postal_search(request, keyword=None):
    """搜索邮编"""
    if not keyword:
        keyword = request.GET.get('q', '')
    
    # 在两个模型中搜索相关邮编
    remote_areas = RemoteArea.objects.filter(zip_code__contains=keyword)[:5]
    zip_zones = ZipZone.objects.filter(
        Q(dest_zip_start__contains=keyword) | 
        Q(dest_zip_end__contains=keyword)
    )[:5]
    
    results = []
    # 添加偏远地区结果
    for area in remote_areas:
        results.append({
            'provider_id': area.provider_id,
            'zip_code': area.zip_code,
            'origin_zip': area.origin_zip,
            'remote_level': area.remote_level
        })
    
    # 添加分区结果
    for zone in zip_zones:
        results.append({
            'provider_id': zone.provider_id,
            'origin_zip': zone.origin_zip,
            'dest_zip_start': zone.dest_zip_start,
            'dest_zip_end': zone.dest_zip_end,
            'zone_number': zone.zone_number
        })
    
    return JsonResponse(results, safe=False)

# 主要URL路径
app_urlpatterns = [
    # 先添加特定的查询路径，确保它有最高优先级
    path('zip-zones/query/', direct_query_zip_zone, name='query-zip-zone'),
    
    # 添加额外的兼容路径，确保原来direct-api-query-zip-zone仍然可访问
    path('../postcodes/zip-zones/query/', direct_query_zip_zone, name='compat-query-zip-zone'),
    
    # 然后添加其他路径
    path('', include(router.urls)),
    path('import-zip-zones/', import_zip_zones, name='import-zip-zones'),
    path('import-remote-areas/', import_remote_areas, name='import-remote-areas'),
    
    # 添加新的路径，匹配前端请求
    path('codes/', postal_codes, name='postal-codes'),
    path('address/<str:postal_code>/', postal_address, name='postal-address'),
    path('search/', postal_search, name='postal-search-empty'),
    path('search/<str:keyword>/', postal_search, name='postal-search'),
]

# 确保主要URL模式可以正确解析
urlpatterns = app_urlpatterns 