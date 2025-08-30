"""
市场数据URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# 注册视图集
# router.register(r'symbols', SymbolViewSet)
# router.register(r'klines', KlineViewSet)

urlpatterns = [
    path('', include(router.urls)),
]