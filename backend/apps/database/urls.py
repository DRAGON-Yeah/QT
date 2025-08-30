from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'connections', views.DatabaseConnectionViewSet, basename='database-connection')
router.register(r'query-history', views.QueryHistoryViewSet, basename='query-history')
router.register(r'redis-connections', views.RedisConnectionViewSet, basename='redis-connection')
router.register(r'redis-history', views.RedisCommandHistoryViewSet, basename='redis-history')

urlpatterns = [
    path('', include(router.urls)),
]