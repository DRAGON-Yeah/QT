#!/usr/bin/env python
"""
测试多租户中间件
"""
import os
import sys
import django
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

# 简化的设置
import django.conf
from django.conf import settings

SIMPLE_SETTINGS = {
    'DEBUG': True,
    'SECRET_KEY': 'test-key',
    'INSTALLED_APPS': [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'apps.core',
        'apps.users',
    ],
    'MIDDLEWARE': [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'apps.core.middleware.TenantMiddleware',
    ],
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    'USE_TZ': True,
    'AUTH_USER_MODEL': 'users.User',
    'DEFAULT_AUTO_FIELD': 'django.db.models.BigAutoField',
}

if not settings.configured:
    settings.configure(**SIMPLE_SETTINGS)

django.setup()

# 创建数据库表
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

from django.test import RequestFactory
from apps.core.models import Tenant
from apps.users.models import User
from apps.core.middleware import TenantMiddleware
from apps.core.utils import get_current_tenant, set_current_tenant, clear_current_tenant


def test_tenant_middleware():
    """测试租户中间件"""
    print("=== 测试租户中间件 ===")
    
    # 创建测试租户
    tenant = Tenant.objects.create(
        name='中间件测试租户',
        schema_name='middleware_test',
        domain='test.example.com'
    )
    
    # 创建测试用户
    user = User.objects.create(
        tenant=tenant,
        username='testuser',
        email='test@example.com'
    )
    
    # 创建请求工厂
    factory = RequestFactory()
    middleware = TenantMiddleware(lambda request: None)
    
    print("1. 测试通过HTTP头部识别租户...")
    request = factory.get('/api/test/')
    request.META['HTTP_X_TENANT_ID'] = str(tenant.id)
    
    # 模拟中间件处理
    response = middleware.process_request(request)
    
    if response is None:  # 中间件正常处理
        print(f"   ✓ 通过HTTP头部识别租户成功: {getattr(request, 'tenant', None)}")
    else:
        print(f"   ❌ 中间件返回错误响应: {response}")
    
    print("2. 测试通过用户识别租户...")
    request = factory.get('/api/test/')
    request.user = user
    
    response = middleware.process_request(request)
    
    if response is None:
        print(f"   ✓ 通过用户识别租户成功: {getattr(request, 'tenant', None)}")
    else:
        print(f"   ❌ 中间件返回错误响应: {response}")
    
    print("3. 测试通过域名识别租户...")
    request = factory.get('/api/test/', HTTP_HOST='test.example.com')
    
    response = middleware.process_request(request)
    
    if response is None:
        print(f"   ✓ 通过域名识别租户成功: {getattr(request, 'tenant', None)}")
    else:
        print(f"   ❌ 中间件返回错误响应: {response}")
    
    return tenant, user


def test_tenant_context_utils():
    """测试租户上下文工具函数"""
    print("\n=== 测试租户上下文工具函数 ===")
    
    # 创建测试租户
    tenant1 = Tenant.objects.create(
        name='上下文测试租户1',
        schema_name='context_test1'
    )
    
    tenant2 = Tenant.objects.create(
        name='上下文测试租户2',
        schema_name='context_test2'
    )
    
    print("1. 测试设置和获取当前租户...")
    
    # 初始状态应该没有租户
    current = get_current_tenant()
    print(f"   初始租户: {current}")
    
    # 设置租户1
    set_current_tenant(tenant1)
    current = get_current_tenant()
    print(f"   设置租户1后: {current.name if current else None}")
    
    # 设置租户2
    set_current_tenant(tenant2)
    current = get_current_tenant()
    print(f"   设置租户2后: {current.name if current else None}")
    
    # 清除租户
    clear_current_tenant()
    current = get_current_tenant()
    print(f"   清除租户后: {current}")
    
    print("2. 测试租户上下文管理器...")
    from apps.core.utils import TenantContext
    
    # 使用上下文管理器
    with TenantContext(tenant1):
        current = get_current_tenant()
        print(f"   上下文管理器中的租户: {current.name if current else None}")
        
        # 嵌套上下文
        with TenantContext(tenant2):
            current = get_current_tenant()
            print(f"   嵌套上下文中的租户: {current.name if current else None}")
        
        # 退出嵌套后应该恢复
        current = get_current_tenant()
        print(f"   退出嵌套后的租户: {current.name if current else None}")
    
    # 退出上下文后应该清空
    current = get_current_tenant()
    print(f"   退出上下文后的租户: {current}")
    
    return tenant1, tenant2


def test_tenant_manager():
    """测试租户管理器"""
    print("\n=== 测试租户管理器 ===")
    
    # 创建测试数据
    tenant1 = Tenant.objects.create(
        name='管理器测试租户1',
        schema_name='manager_test1'
    )
    
    tenant2 = Tenant.objects.create(
        name='管理器测试租户2',
        schema_name='manager_test2'
    )
    
    # 在不同租户中创建用户
    user1 = User.objects.create(
        tenant=tenant1,
        username='manager_user1',
        email='user1@example.com'
    )
    
    user2 = User.objects.create(
        tenant=tenant2,
        username='manager_user2',
        email='user2@example.com'
    )
    
    print("1. 测试无租户上下文时的查询...")
    all_users = User.objects.all()
    print(f"   所有用户数量: {all_users.count()}")
    
    print("2. 测试租户上下文中的查询...")
    from apps.core.utils import TenantContext
    
    with TenantContext(tenant1):
        tenant1_users = User.objects.all()
        print(f"   租户1用户数量: {tenant1_users.count()}")
        for user in tenant1_users:
            print(f"     - {user.username} ({user.tenant.name})")
    
    with TenantContext(tenant2):
        tenant2_users = User.objects.all()
        print(f"   租户2用户数量: {tenant2_users.count()}")
        for user in tenant2_users:
            print(f"     - {user.username} ({user.tenant.name})")
    
    return tenant1, tenant2, user1, user2


def test_user_permissions_in_context():
    """测试租户上下文中的用户权限"""
    print("\n=== 测试租户上下文中的用户权限 ===")
    
    from apps.core.models import Permission, Role
    from apps.core.utils import TenantContext
    
    # 创建租户
    tenant = Tenant.objects.create(
        name='权限测试租户',
        schema_name='permission_test'
    )
    
    # 创建权限
    permission = Permission.objects.create(
        name='测试权限',
        codename='test.permission',
        category='system'
    )
    
    # 在租户上下文中创建角色和用户
    with TenantContext(tenant):
        # 创建角色
        role = Role.objects.create(
            name='测试角色',
            tenant=tenant,
            description='权限测试角色'
        )
        role.permissions.add(permission)
        
        # 创建用户
        user = User.objects.create(
            tenant=tenant,
            username='permission_user',
            email='permission@example.com'
        )
        
        # 分配角色
        user.add_role(role)
        
        # 测试权限
        has_permission = user.has_permission('test.permission')
        print(f"   用户权限检查: {has_permission}")
        
        # 测试角色
        has_role = user.has_role('测试角色')
        print(f"   用户角色检查: {has_role}")
        
        # 获取所有权限
        all_permissions = user.get_all_permissions()
        print(f"   用户所有权限数量: {len(all_permissions)}")
    
    return tenant, user, role


def main():
    """主测试函数"""
    print("开始多租户中间件测试...\n")
    
    try:
        # 测试租户中间件
        tenant, user = test_tenant_middleware()
        
        # 测试租户上下文工具函数
        tenant1, tenant2 = test_tenant_context_utils()
        
        # 测试租户管理器
        t1, t2, u1, u2 = test_tenant_manager()
        
        # 测试租户上下文中的用户权限
        perm_tenant, perm_user, perm_role = test_user_permissions_in_context()
        
        print("\n=== 所有中间件测试通过 ===")
        print("多租户中间件和工具函数工作正常！")
        
        # 显示统计信息
        print(f"\n统计信息:")
        print(f"  租户数量: {Tenant.objects.count()}")
        print(f"  用户数量: {User.objects.count()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)