"""
多租户工具函数
"""
import threading
from typing import Optional
from django.core.cache import cache


# 线程本地存储，用于存储当前租户信息
_thread_local = threading.local()


def set_current_tenant(tenant):
    """设置当前线程的租户"""
    _thread_local.tenant = tenant


def get_current_tenant():
    """获取当前线程的租户"""
    return getattr(_thread_local, 'tenant', None)


def clear_current_tenant():
    """清除当前线程的租户"""
    if hasattr(_thread_local, 'tenant'):
        delattr(_thread_local, 'tenant')


def get_tenant_cache_key(key: str, tenant_id: Optional[str] = None) -> str:
    """
    生成租户级别的缓存键
    
    Args:
        key: 基础缓存键
        tenant_id: 租户ID，如果不提供则使用当前租户
    
    Returns:
        带租户前缀的缓存键
    """
    if not tenant_id:
        tenant = get_current_tenant()
        tenant_id = str(tenant.id) if tenant else 'global'
    
    return f"tenant_{tenant_id}:{key}"


def set_tenant_cache(key: str, value, timeout: int = 3600, tenant_id: Optional[str] = None):
    """
    设置租户级别的缓存
    
    Args:
        key: 缓存键
        value: 缓存值
        timeout: 过期时间（秒）
        tenant_id: 租户ID
    """
    cache_key = get_tenant_cache_key(key, tenant_id)
    cache.set(cache_key, value, timeout)


def get_tenant_cache(key: str, default=None, tenant_id: Optional[str] = None):
    """
    获取租户级别的缓存
    
    Args:
        key: 缓存键
        default: 默认值
        tenant_id: 租户ID
    
    Returns:
        缓存值或默认值
    """
    cache_key = get_tenant_cache_key(key, tenant_id)
    return cache.get(cache_key, default)


def delete_tenant_cache(key: str, tenant_id: Optional[str] = None):
    """
    删除租户级别的缓存
    
    Args:
        key: 缓存键
        tenant_id: 租户ID
    """
    cache_key = get_tenant_cache_key(key, tenant_id)
    cache.delete(cache_key)


def clear_tenant_cache(tenant_id: Optional[str] = None):
    """
    清除租户的所有缓存
    
    Args:
        tenant_id: 租户ID，如果不提供则使用当前租户
    """
    if not tenant_id:
        tenant = get_current_tenant()
        tenant_id = str(tenant.id) if tenant else None
    
    if tenant_id:
        # 获取所有匹配的缓存键并删除
        pattern = f"tenant_{tenant_id}:*"
        # 注意：这里需要根据实际的缓存后端实现
        # Redis后端可以使用 cache.delete_pattern(pattern)
        try:
            cache.delete_pattern(pattern)
        except AttributeError:
            # 如果缓存后端不支持模式删除，则跳过
            pass


class TenantContext:
    """
    租户上下文管理器
    用于在特定代码块中设置租户上下文
    """
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.previous_tenant = None
    
    def __enter__(self):
        self.previous_tenant = get_current_tenant()
        set_current_tenant(self.tenant)
        return self.tenant
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_tenant:
            set_current_tenant(self.previous_tenant)
        else:
            clear_current_tenant()


def with_tenant(tenant):
    """
    装饰器：在指定租户上下文中执行函数
    
    Args:
        tenant: 租户对象
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TenantContext(tenant):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def ensure_tenant_context(func):
    """
    装饰器：确保函数在租户上下文中执行
    如果没有租户上下文，则抛出异常
    """
    def wrapper(*args, **kwargs):
        if not get_current_tenant():
            raise ValueError("此操作需要在租户上下文中执行")
        return func(*args, **kwargs)
    return wrapper


def get_tenant_upload_path(instance, filename: str) -> str:
    """
    生成租户级别的文件上传路径
    
    Args:
        instance: 模型实例
        filename: 文件名
    
    Returns:
        上传路径
    """
    tenant = instance.tenant if hasattr(instance, 'tenant') else get_current_tenant()
    tenant_id = str(tenant.id) if tenant else 'global'
    
    # 按年月组织文件夹
    from datetime import datetime
    now = datetime.now()
    year_month = now.strftime('%Y/%m')
    
    return f'tenant_{tenant_id}/{year_month}/{filename}'


def validate_tenant_access(user, obj):
    """
    验证用户是否有权限访问指定对象
    
    Args:
        user: 用户对象
        obj: 要访问的对象
    
    Returns:
        bool: 是否有权限访问
    """
    if not user or not user.is_authenticated:
        return False
    
    # 超级用户可以访问所有数据
    if user.is_superuser:
        return True
    
    # 检查对象是否属于用户的租户
    if hasattr(obj, 'tenant'):
        return obj.tenant_id == user.tenant_id
    
    return True


def get_tenant_by_domain(domain: str):
    """
    根据域名获取租户
    
    Args:
        domain: 域名
    
    Returns:
        租户对象或None
    """
    from .models import Tenant
    
    try:
        return Tenant.objects.get(domain=domain, is_active=True)
    except Tenant.DoesNotExist:
        return None


def create_default_permissions():
    """
    创建系统默认权限
    """
    from .models import Permission
    
    default_permissions = [
        # 系统管理权限
        ('system.view_dashboard', '查看系统仪表盘', 'system'),
        ('system.manage_tenants', '管理租户', 'system'),
        ('system.manage_system_settings', '管理系统设置', 'system'),
        
        # 用户管理权限
        ('user.view_users', '查看用户', 'user'),
        ('user.create_user', '创建用户', 'user'),
        ('user.edit_user', '编辑用户', 'user'),
        ('user.delete_user', '删除用户', 'user'),
        ('user.manage_roles', '管理角色', 'user'),
        ('user.manage_permissions', '管理权限', 'user'),
        
        # 交易管理权限
        ('trading.view_orders', '查看订单', 'trading'),
        ('trading.create_order', '创建订单', 'trading'),
        ('trading.cancel_order', '取消订单', 'trading'),
        ('trading.view_positions', '查看持仓', 'trading'),
        ('trading.manage_exchanges', '管理交易所', 'trading'),
        
        # 策略管理权限
        ('strategy.view_strategies', '查看策略', 'strategy'),
        ('strategy.create_strategy', '创建策略', 'strategy'),
        ('strategy.edit_strategy', '编辑策略', 'strategy'),
        ('strategy.delete_strategy', '删除策略', 'strategy'),
        ('strategy.run_backtest', '运行回测', 'strategy'),
        
        # 风险控制权限
        ('risk.view_risk_metrics', '查看风险指标', 'risk'),
        ('risk.manage_risk_rules', '管理风险规则', 'risk'),
        ('risk.view_alerts', '查看预警', 'risk'),
        
        # 市场数据权限
        ('market.view_market_data', '查看市场数据', 'market'),
        ('market.export_data', '导出数据', 'market'),
        
        # 监控权限
        ('monitoring.view_system_status', '查看系统状态', 'monitoring'),
        ('monitoring.manage_logs', '管理日志', 'monitoring'),
        ('monitoring.view_performance', '查看性能指标', 'monitoring'),
    ]
    
    created_permissions = []
    for codename, name, category in default_permissions:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': name,
                'category': category,
                'description': f'{name}权限'
            }
        )
        if created:
            created_permissions.append(permission)
    
    return created_permissions


def create_default_roles(tenant):
    """
    为租户创建默认角色
    
    Args:
        tenant: 租户对象
    
    Returns:
        创建的角色列表
    """
    from .models import Role, Permission
    
    # 定义默认角色及其权限
    default_roles = {
        '超级管理员': [
            'system.view_dashboard', 'system.manage_system_settings',
            'user.view_users', 'user.create_user', 'user.edit_user', 'user.delete_user',
            'user.manage_roles', 'user.manage_permissions',
            'trading.view_orders', 'trading.create_order', 'trading.cancel_order',
            'trading.view_positions', 'trading.manage_exchanges',
            'strategy.view_strategies', 'strategy.create_strategy', 'strategy.edit_strategy',
            'strategy.delete_strategy', 'strategy.run_backtest',
            'risk.view_risk_metrics', 'risk.manage_risk_rules', 'risk.view_alerts',
            'market.view_market_data', 'market.export_data',
            'monitoring.view_system_status', 'monitoring.manage_logs', 'monitoring.view_performance',
        ],
        '交易员': [
            'trading.view_orders', 'trading.create_order', 'trading.cancel_order',
            'trading.view_positions', 'strategy.view_strategies', 'strategy.run_backtest',
            'risk.view_risk_metrics', 'risk.view_alerts', 'market.view_market_data',
        ],
        '策略开发者': [
            'strategy.view_strategies', 'strategy.create_strategy', 'strategy.edit_strategy',
            'strategy.run_backtest', 'market.view_market_data', 'market.export_data',
            'risk.view_risk_metrics',
        ],
        '观察者': [
            'trading.view_orders', 'trading.view_positions', 'strategy.view_strategies',
            'risk.view_risk_metrics', 'market.view_market_data',
        ],
    }
    
    created_roles = []
    
    with TenantContext(tenant):
        for role_name, permission_codenames in default_roles.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                tenant=tenant,
                defaults={
                    'description': f'{role_name}角色',
                    'role_type': 'system'
                }
            )
            
            if created:
                # 添加权限
                permissions = Permission.objects.filter(codename__in=permission_codenames)
                role.permissions.set(permissions)
                created_roles.append(role)
    
    return created_roles


def get_client_ip(request):
    """
    获取客户端IP地址
    
    Args:
        request: HTTP请求对象
    
    Returns:
        str: 客户端IP地址
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_user_agent(request):
    """
    获取用户代理字符串
    
    Args:
        request: HTTP请求对象
    
    Returns:
        str: 用户代理字符串
    """
    return request.META.get('HTTP_USER_AGENT', '')


def parse_user_agent(user_agent_string):
    """
    解析用户代理字符串，提取设备信息
    
    Args:
        user_agent_string: 用户代理字符串
    
    Returns:
        dict: 设备信息字典
    """
    # 简单的用户代理解析，实际项目中可以使用 user-agents 库
    device_info = {
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Unknown'
    }
    
    if not user_agent_string:
        return device_info
    
    user_agent_lower = user_agent_string.lower()
    
    # 检测浏览器
    if 'chrome' in user_agent_lower:
        device_info['browser'] = 'Chrome'
    elif 'firefox' in user_agent_lower:
        device_info['browser'] = 'Firefox'
    elif 'safari' in user_agent_lower:
        device_info['browser'] = 'Safari'
    elif 'edge' in user_agent_lower:
        device_info['browser'] = 'Edge'
    
    # 检测操作系统
    if 'windows' in user_agent_lower:
        device_info['os'] = 'Windows'
    elif 'mac' in user_agent_lower:
        device_info['os'] = 'macOS'
    elif 'linux' in user_agent_lower:
        device_info['os'] = 'Linux'
    elif 'android' in user_agent_lower:
        device_info['os'] = 'Android'
    elif 'ios' in user_agent_lower:
        device_info['os'] = 'iOS'
    
    # 检测设备类型
    if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
        device_info['device'] = 'Mobile'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        device_info['device'] = 'Tablet'
    else:
        device_info['device'] = 'Desktop'
    
    return device_info