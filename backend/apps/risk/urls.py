"""
风险控制URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# 注册视图集
# router.register(r'risk-metrics', RiskMetricViewSet)
# router.register(r'alerts', AlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]