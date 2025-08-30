"""
权限控制模块 - 提供多租户权限验证和装饰器
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status


class TenantPermission(BasePermission):
    """
    租户权限控制
    确保用户只能访问自己租户的数据
    """
    
    def has_permission(self, request, view):
        """检查用户是否有访问权限"""
        if not request.user.is_authenticated:
            return False
        
        # 检查用户是否有租户
        if not hasattr(request.user, 'tenant') or not request.user.tenant:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有访问特定对象的权限"""
        if not request.user.is_authenticated:
            return False
        
        # 检查对象是否属于用户的租户
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        
        # 如果对象没有租户字段，检查是否属于用户
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return True


class AdminPermission(BasePermission):
    """
    管理员权限控制
    """
    
    def has_permission(self, request, view):
        """检查用户是否是管理员"""
        return request.user.is_authenticated and request.user.is_staff


class SuperAdminPermission(BasePermission):
    """
    超级管理员权限控制
    """
    
    def has_permission(self, request, view):
        """检查用户是否是超级管理员"""
        return request.user.is_authenticated and request.user.is_superuser


class CustomPermission(BasePermission):
    """
    自定义权限控制基类
    支持基于权限代码的动态权限检查
    """
    
    def __init__(self, permission_codename=None):
        self.permission_codename = permission_codename
    
    def has_permission(self, request, view):
        """检查用户是否有指定权限"""
        if not request.user.is_authenticated:
            return False
        
        # 如果没有指定权限代码，则检查是否有租户权限
        if not self.permission_codename:
            return hasattr(request.user, 'tenant') and request.user.tenant
        
        # 检查用户是否有指定权限
        return request.user.has_permission(self.permission_codename)


def require_permission(permission_codename):
    """
    权限装饰器 - 用于函数视图和类方法
    
    Args:
        permission_codename (str): 权限代码，如 'trading.create_order'
    
    Returns:
        装饰器函数
    
    Example:
        @require_permission('trading.create_order')
        def create_order_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # 判断是类方法还是函数视图
            if len(args) > 0 and hasattr(args[0], 'request'):
                # 类方法：第一个参数是self，request在self.request中
                request = args[0].request
            elif len(args) > 0 and hasattr(args[0], 'user'):
                # 函数视图：第一个参数是request
                request = args[0]
            else:
                # 无法确定request对象
                return HttpResponseForbidden('无法确定请求对象')
            
            # 检查用户是否已认证
            if not request.user.is_authenticated:
                return HttpResponseForbidden('用户未登录')
            
            # 检查用户是否有指定权限
            if not request.user.has_permission(permission_codename):
                return HttpResponseForbidden(f'权限不足，需要权限: {permission_codename}')
            
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def require_permissions(*permission_codenames):
    """
    多权限装饰器 - 要求用户拥有所有指定权限
    
    Args:
        *permission_codenames: 权限代码列表
    
    Returns:
        装饰器函数
    
    Example:
        @require_permissions('trading.view_orders', 'trading.create_order')
        def trading_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('用户未登录')
            
            # 检查所有权限
            missing_permissions = []
            for permission in permission_codenames:
                if not request.user.has_permission(permission):
                    missing_permissions.append(permission)
            
            if missing_permissions:
                return HttpResponseForbidden(
                    f'权限不足，缺少权限: {", ".join(missing_permissions)}'
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_codenames):
    """
    任一权限装饰器 - 要求用户拥有任一指定权限
    
    Args:
        *permission_codenames: 权限代码列表
    
    Returns:
        装饰器函数
    
    Example:
        @require_any_permission('trading.view_orders', 'strategy.view_strategies')
        def dashboard_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('用户未登录')
            
            # 检查是否有任一权限
            has_permission = any(
                request.user.has_permission(permission) 
                for permission in permission_codenames
            )
            
            if not has_permission:
                return HttpResponseForbidden(
                    f'权限不足，需要以下任一权限: {", ".join(permission_codenames)}'
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name):
    """
    角色装饰器 - 要求用户拥有指定角色
    
    Args:
        role_name (str): 角色名称
    
    Returns:
        装饰器函数
    
    Example:
        @require_role('超级管理员')
        def admin_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('用户未登录')
            
            # 检查用户是否有指定角色
            if not request.user.has_role(role_name):
                return HttpResponseForbidden(f'权限不足，需要角色: {role_name}')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_tenant_admin(view_func):
    """
    租户管理员装饰器 - 要求用户是租户管理员
    
    Example:
        @require_tenant_admin
        def tenant_settings_view(request):
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('用户未登录')
        
        # 检查用户是否是租户管理员
        if not request.user.is_tenant_admin():
            return HttpResponseForbidden('权限不足，需要租户管理员权限')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_superuser(view_func):
    """
    超级用户装饰器 - 要求用户是超级用户
    
    Example:
        @require_superuser
        def system_admin_view(request):
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('用户未登录')
        
        if not request.user.is_superuser:
            return HttpResponseForbidden('权限不足，需要超级用户权限')
        
        return view_func(request, *args, **kwargs)
    return wrapper


class PermissionMixin:
    """
    权限混入类 - 用于类视图的权限控制
    """
    
    required_permissions = []  # 必需权限列表
    required_any_permissions = []  # 任一权限列表
    required_role = None  # 必需角色
    require_tenant_admin = False  # 是否需要租户管理员权限
    require_superuser = False  # 是否需要超级用户权限
    
    def check_permissions(self, request):
        """
        检查权限
        
        Args:
            request: HTTP请求对象
        
        Raises:
            PermissionDenied: 权限不足时抛出异常
        """
        if not request.user.is_authenticated:
            raise PermissionDenied('用户未登录')
        
        # 检查超级用户权限
        if self.require_superuser and not request.user.is_superuser:
            raise PermissionDenied('需要超级用户权限')
        
        # 检查租户管理员权限
        if self.require_tenant_admin and not request.user.is_tenant_admin():
            raise PermissionDenied('需要租户管理员权限')
        
        # 检查角色权限
        if self.required_role and not request.user.has_role(self.required_role):
            raise PermissionDenied(f'需要角色: {self.required_role}')
        
        # 检查必需权限
        if self.required_permissions:
            missing_permissions = []
            for permission in self.required_permissions:
                if not request.user.has_permission(permission):
                    missing_permissions.append(permission)
            
            if missing_permissions:
                raise PermissionDenied(
                    f'权限不足，缺少权限: {", ".join(missing_permissions)}'
                )
        
        # 检查任一权限
        if self.required_any_permissions:
            has_permission = any(
                request.user.has_permission(permission) 
                for permission in self.required_any_permissions
            )
            
            if not has_permission:
                raise PermissionDenied(
                    f'权限不足，需要以下任一权限: {", ".join(self.required_any_permissions)}'
                )
    
    def dispatch(self, request, *args, **kwargs):
        """重写dispatch方法，在处理请求前检查权限"""
        try:
            self.check_permissions(request)
        except PermissionDenied as e:
            if hasattr(self, 'permission_denied'):
                return self.permission_denied(request, str(e))
            else:
                return HttpResponseForbidden(str(e))
        
        return super().dispatch(request, *args, **kwargs)


class APIPermissionMixin:
    """
    API权限混入类 - 用于DRF视图的权限控制
    """
    
    required_permissions = []
    required_any_permissions = []
    required_role = None
    require_tenant_admin = False
    require_superuser = False
    
    def check_permissions(self, request):
        """检查API权限"""
        if not request.user.is_authenticated:
            self.permission_denied(
                request, 
                message='用户未登录',
                code='not_authenticated'
            )
        
        # 检查超级用户权限
        if self.require_superuser and not request.user.is_superuser:
            self.permission_denied(
                request,
                message='需要超级用户权限',
                code='superuser_required'
            )
        
        # 检查租户管理员权限
        if self.require_tenant_admin and not request.user.is_tenant_admin():
            self.permission_denied(
                request,
                message='需要租户管理员权限',
                code='tenant_admin_required'
            )
        
        # 检查角色权限
        if self.required_role and not request.user.has_role(self.required_role):
            self.permission_denied(
                request,
                message=f'需要角色: {self.required_role}',
                code='role_required'
            )
        
        # 检查必需权限
        if self.required_permissions:
            missing_permissions = []
            for permission in self.required_permissions:
                if not request.user.has_permission(permission):
                    missing_permissions.append(permission)
            
            if missing_permissions:
                self.permission_denied(
                    request,
                    message=f'权限不足，缺少权限: {", ".join(missing_permissions)}',
                    code='permission_required'
                )
        
        # 检查任一权限
        if self.required_any_permissions:
            has_permission = any(
                request.user.has_permission(permission) 
                for permission in self.required_any_permissions
            )
            
            if not has_permission:
                self.permission_denied(
                    request,
                    message=f'权限不足，需要以下任一权限: {", ".join(self.required_any_permissions)}',
                    code='any_permission_required'
                )
    
    def initial(self, request, *args, **kwargs):
        """重写initial方法，在处理请求前检查权限"""
        super().initial(request, *args, **kwargs)
        self.check_permissions(request)


def permission_required(permission_codename):
    """
    类装饰器 - 为整个视图类添加权限要求
    
    Args:
        permission_codename (str): 权限代码
    
    Returns:
        装饰器函数
    
    Example:
        @permission_required('trading.view_orders')
        class OrderListView(ListView):
            pass
    """
    def decorator(cls):
        original_dispatch = cls.dispatch
        
        @wraps(original_dispatch)
        def new_dispatch(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('用户未登录')
            
            if not request.user.has_permission(permission_codename):
                return HttpResponseForbidden(f'权限不足，需要权限: {permission_codename}')
            
            return original_dispatch(self, request, *args, **kwargs)
        
        cls.dispatch = new_dispatch
        return cls
    return decorator


def validate_tenant_access(user, obj):
    """
    验证用户是否有权限访问指定对象
    
    Args:
        user: 用户对象
        obj: 要访问的对象
    
    Returns:
        bool: 是否有权限访问
    
    Raises:
        PermissionDenied: 权限不足时抛出异常
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied('用户未登录')
    
    # 超级用户可以访问所有数据
    if user.is_superuser:
        return True
    
    # 检查对象是否属于用户的租户
    if hasattr(obj, 'tenant'):
        if obj.tenant_id != user.tenant_id:
            raise PermissionDenied('无权限访问其他租户的数据')
    
    # 检查对象是否属于用户
    if hasattr(obj, 'user'):
        if obj.user_id != user.id:
            raise PermissionDenied('无权限访问其他用户的数据')
    
    return True


def check_object_permission(user, obj, permission_codename=None):
    """
    检查用户对特定对象的权限
    
    Args:
        user: 用户对象
        obj: 要检查的对象
        permission_codename: 权限代码（可选）
    
    Returns:
        bool: 是否有权限
    """
    try:
        # 验证租户访问权限
        validate_tenant_access(user, obj)
        
        # 如果指定了权限代码，检查用户是否有该权限
        if permission_codename and not user.has_permission(permission_codename):
            return False
        
        return True
    except PermissionDenied:
        return False