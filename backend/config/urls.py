"""
QuantTrade URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# API路由器
router = DefaultRouter()

# 注册API视图集
# router.register(r'users', UserViewSet)
# router.register(r'orders', OrderViewSet)

urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    
    # API根路径
    path('api/', include(router.urls)),
    
    # 应用URL
    path('api/users/', include('apps.users.urls')),  # 用户管理
    path('api/core/', include('apps.core.menu_urls')),  # 菜单管理
    path('api/trading/', include('apps.trading.urls')),
    path('api/strategies/', include('apps.strategies.urls')),
    path('api/market/', include('apps.market.urls')),
    path('api/risk/', include('apps.risk.urls')),
    path('api/monitoring/', include('apps.monitoring.urls')),
    
    # 健康检查
    path('health/', include('apps.monitoring.urls')),
]

# 开发环境静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug工具栏
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns