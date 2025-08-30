"""
QuantTrade URL 配置

QuantTrade 量化交易平台的主要 URL 路由配置文件。
定义了所有 API 端点、管理后台、静态文件服务等路由规则。

支持的主要功能模块：
- 用户管理和认证
- 菜单权限管理  
- 交易订单管理
- 策略管理
- 市场数据
- 风险控制
- 系统监控

更多信息请参考: https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from apps.monitoring import views

# DRF API 路由器 - 用于自动生成 RESTful API 路由
router = DefaultRouter()

# 注册 API 视图集到路由器
# 注意：这些视图集将在各个应用中定义后取消注释
# router.register(r'users', UserViewSet, basename='user')
# router.register(r'orders', OrderViewSet, basename='order')

# 主要 URL 路由配置
urlpatterns = [
    # Django 管理后台 - 用于系统管理员管理用户、权限等
    path('admin/', admin.site.urls),
    
    # DRF API 根路径 - 包含所有通过路由器注册的 API
    path('api/', include(router.urls)),
    
    # 各应用模块的 API 路由
    path('api/users/', include('apps.users.urls')),        # 用户管理：登录、注册、权限
    path('api/core/', include('apps.core.menu_urls')),     # 核心功能：菜单管理、权限控制
    path('api/trading/', include('apps.trading.urls')),    # 交易管理：订单、持仓、交易历史
    path('api/strategies/', include('apps.strategies.urls')),  # 策略管理：策略创建、回测、监控
    path('api/market/', include('apps.market.urls')),      # 市场数据：行情、K线、订单簿
    path('api/risk/', include('apps.risk.urls')),          # 风险控制：风险规则、预警
    path('api/monitoring/', include('apps.monitoring.urls')),  # 系统监控：性能、日志、告警
    
    # 系统健康检查端点 - 用于负载均衡器和监控系统
    path('health/', views.health_check, name='health_check'),
]

# 开发环境配置 - 仅在 DEBUG=True 时生效
if settings.DEBUG:
    # 静态文件服务 - 生产环境由 Nginx 处理
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # 用户上传文件
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # CSS、JS、图片等
    
    # Django Debug Toolbar - 开发调试工具
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns