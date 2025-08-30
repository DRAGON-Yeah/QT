"""
用户管理URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserManagementViewSet, RoleManagementViewSet,
    PermissionListView, RoleAssignmentView, UserLoginLogView,
    LoginView, LogoutView, LogoutAllView, RefreshTokenView,
    PasswordChangeView, PasswordResetView, UserProfileView, UserSessionView
)

# 创建路由器
router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user')
router.register(r'roles', RoleManagementViewSet, basename='role')

app_name = 'users'

urlpatterns = [
    # 用户和角色管理
    path('', include(router.urls)),
    
    # JWT认证相关
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/logout-all/', LogoutAllView.as_view(), name='logout-all'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    
    # 密码管理
    path('auth/change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('auth/reset-password/', PasswordResetView.as_view(), name='reset-password'),
    
    # 用户个人信息
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # 会话管理
    path('sessions/', UserSessionView.as_view(), name='user-sessions'),
    path('sessions/<int:session_id>/', UserSessionView.as_view(), name='terminate-session'),
    
    # 权限管理
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    
    # 角色分配
    path('role-assignment/', RoleAssignmentView.as_view(), name='role-assignment'),
    
    # 登录日志
    path('login-logs/', UserLoginLogView.as_view(), name='login-logs'),
    path('login-logs/<int:user_id>/', UserLoginLogView.as_view(), name='user-login-logs'),
]