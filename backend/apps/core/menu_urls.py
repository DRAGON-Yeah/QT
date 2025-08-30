# -*- coding: utf-8 -*-
"""
菜单管理URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .menu_views import MenuViewSet, UserMenuConfigViewSet

router = DefaultRouter()
router.register(r'menus', MenuViewSet, basename='menu')
router.register(r'user-menu-configs', UserMenuConfigViewSet, basename='user-menu-config')

urlpatterns = [
    path('', include(router.urls)),
]