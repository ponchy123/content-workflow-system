"""
freight URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from apps.core.views import configs, slow_request_monitor, performance_monitor
from django.http import HttpResponse

# API Schema URLs
schema_patterns = [
    # API schema & documentation
    path('schema/', SpectacularAPIView.as_view(), name='api_schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='api_schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api_schema'), name='redoc'),
]

# Default API patterns
api_patterns = [
    # Admin
    path('admin/', admin.site.urls, name='admin'),
    
    # Core modules
    path('users/', include(('apps.users.urls', 'api_users'))),
    path('products/', include(('apps.products.urls', 'api_products'))),
    path('postal-codes/', include(('apps.postal_codes.urls', 'api_postal_codes'))),
    
    # Modules
    path('calculator/', include(('apps.calculator.urls', 'api_calculator'))),
    path('fuel-rates/', include(('apps.fuel_rates.urls', 'api_fuel_rates'))),
    
    # Docs
    path('docs/', include((schema_patterns, 'api_docs'))),

    # 配置API
    path('configs', configs, name='configs'),
]

# v1版本API模式
api_v1_patterns = [
    # Admin
    path('admin/', admin.site.urls, name='admin'),
    
    # Core modules
    path('users/', include(('apps.users.urls', 'api_v1_users'))),
    path('products/', include(('apps.products.urls', 'api_v1_products'))),
    path('postal-codes/', include(('apps.postal_codes.urls', 'api_v1_postal_codes'))),
    
    # Modules
    path('calculator/', include(('apps.calculator.urls', 'api_v1_calculator'))),
    path('fuel-rates/', include(('apps.fuel_rates.urls', 'api_v1_fuel_rates'))),
    
    # Docs
    path('docs/', include((schema_patterns, 'api_v1_docs'))),

    # 配置API
    path('configs', configs, name='configs'),
]

# Global URL patterns
urlpatterns = [
    # Default API path
    path('api/', include((api_patterns, 'api'))),
    # 添加v1版本API路径
    path('api/v1/', include((api_v1_patterns, 'api_v1'))),
    # API文档直接路径
    path('schema/', SpectacularAPIView.as_view(), name='api_schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='api_schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api_schema'), name='redoc'),
    # 直接访问API文档路径
    path('api/docs/', lambda request: HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>运费计算系统 API 文档</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
            h1 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .links { margin-top: 20px; }
            .links a { display: block; margin-bottom: 10px; color: #0066cc; text-decoration: none; }
            .links a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>运费计算系统 API 文档</h1>
            <div class="links">
                <a href="/api/docs/schema/">API Schema (JSON)</a>
                <a href="/api/docs/swagger/">Swagger UI 文档</a>
                <a href="/api/docs/redoc/">ReDoc 文档</a>
            </div>
        </div>
    </body>
    </html>
    """), name='api_docs_root'),
    path('admin/', admin.site.urls, name='admin_root'),
    # 添加根路径处理
    path('', lambda request: HttpResponse('运费计算系统 API 服务正在运行'), name='root'),
    # 监控API路由
    path('api/v1/core/monitoring/slow-request/', slow_request_monitor, name='slow_request_monitor'),
    path('api/v1/core/monitoring/performance/', performance_monitor, name='performance_monitor'),
] 

# Add debug URLs in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
