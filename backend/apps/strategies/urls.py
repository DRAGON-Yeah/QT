"""
策略管理URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# 注册视图集
# router.register(r'strategies', StrategyViewSet)
# router.register(r'backtests', BacktestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]