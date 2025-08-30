"""
系统监控URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'system-metrics', views.SystemMetricsViewSet, basename='system-metrics')
router.register(r'process-metrics', views.ProcessMetricsViewSet, basename='process-metrics')
router.register(r'alert-rules', views.AlertRuleViewSet, basename='alert-rules')
router.register(r'alerts', views.AlertViewSet, basename='alerts')
router.register(r'celery-workers', views.CeleryWorkerViewSet, basename='celery-workers')
router.register(r'celery-tasks', views.CeleryTaskViewSet, basename='celery-tasks')
router.register(r'celery-queues', views.CeleryQueueViewSet, basename='celery-queues')
router.register(r'celery-management', views.CeleryManagementViewSet, basename='celery-management')
router.register(r'management', views.MonitoringManagementViewSet, basename='monitoring-management')

urlpatterns = [
    # 健康检查
    path('health/', views.health_check, name='health_check'),
    
    # API路由
    path('api/', include(router.urls)),
]