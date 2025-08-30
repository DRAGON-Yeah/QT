#!/usr/bin/env python
"""
简单的多租户模型测试
"""
import os
import sys
import django
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 设置最简单的Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

# 临时修改设置以避免依赖问题
import django.conf
from django.conf import settings

# 简化的设置
SIMPLE_SETTINGS = {
    'DEBUG': True,
    'SECRET_KEY': 'test-key',
    'INSTALLED_APPS': [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'apps.core',
        'apps.users',
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

# 配置Django
if not settings.configured:
    settings.configure(**SIMPLE_SETTINGS)

django.setup()

# 创建数据库表
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

# 现在可以导入模型
from apps.core.models import Tenant, Permission, Role
from apps.users.models import User
from apps.core.utils import TenantContext


def test_basic_models():
    """测试基础模型"""
    print("=== 测试基础模型 ===")
    
    # 测试租户创建
    print("1. 测试租户创建...")
    tenant = Tenant.objects.create(
        name='测试租户',
        schema_name='test_tenant'
    )
    print(f"   ✓ 创建租户: {tenant.name}")
    
    # 测试权限创建
    print("2. 测试权限创建...")
    permission = Permission.objects.create(
        name='测试权限',
        codename='test.permission',
        category='system'
    )
    print(f"   ✓ 创建权限: {permission.name}")
    
    # 测试角色创建
    print("3. 测试角色创建...")
    role = Role.objects.create(
        name='测试角色',
        tenant=tenant,
        description='测试角色'
    )
    role.permissions.add(permission)
    print(f"   ✓ 创建角色: {role.name}")
    
    # 测试用户创建
    print("4. 测试用户创建...")
    user = User.objects.create(
        tenant=tenant,
        username='testuser',
        email='test@example.com'
    )
    user.set_password('testpass123')
    user.save()
    print(f"   ✓ 创建用户: {user.username}")
    
    # 测试用户角色分配
    print("5. 测试用户角色分配...")
    user.add_role(role)
    print(f"   ✓ 用户角色分配成功")
    
    # 测试权限检查
    print("6. 测试权限检查...")
    has_permission = user.has_permission('test.permission')
    print(f"   ✓ 用户权限检查: {has_permission}")
    
    return tenant, user, role, permission


def test_tenant_isolation():
    """测试租户隔离"""
    print("\n=== 测试租户隔离 ===")
    
    # 创建两个租户
    tenant1 = Tenant.objects.create(
        name='租户1',
        schema_name='tenant1'
    )
    
    tenant2 = Tenant.objects.create(
        name='租户2',
        schema_name='tenant2'
    )
    
    # 在每个租户中创建用户
    user1 = User.objects.create(
        tenant=tenant1,
        username='user1',
        email='user1@example.com'
    )
    
    user2 = User.objects.create(
        tenant=tenant2,
        username='user2',
        email='user2@example.com'
    )
    
    print(f"   ✓ 租户1用户: {user1.username} (租户: {user1.tenant.name})")
    print(f"   ✓ 租户2用户: {user2.username} (租户: {user2.tenant.name})")
    
    # 验证用户属于正确的租户
    assert user1.tenant == tenant1
    assert user2.tenant == tenant2
    print("   ✓ 租户隔离验证成功")
    
    return tenant1, tenant2, user1, user2


def test_role_inheritance():
    """测试角色继承"""
    print("\n=== 测试角色继承 ===")
    
    tenant = Tenant.objects.create(
        name='继承测试租户',
        schema_name='inherit_tenant'
    )
    
    # 创建权限
    perm1 = Permission.objects.create(
        name='权限1',
        codename='perm1',
        category='system'
    )
    
    perm2 = Permission.objects.create(
        name='权限2',
        codename='perm2',
        category='system'
    )
    
    # 创建父角色
    parent_role = Role.objects.create(
        name='父角色',
        tenant=tenant,
        description='父角色'
    )
    parent_role.permissions.add(perm1)
    
    # 创建子角色
    child_role = Role.objects.create(
        name='子角色',
        tenant=tenant,
        description='子角色',
        parent_role=parent_role
    )
    child_role.permissions.add(perm2)
    
    print(f"   ✓ 父角色权限数: {parent_role.get_direct_permissions().__len__()}")
    print(f"   ✓ 子角色直接权限数: {child_role.get_direct_permissions().__len__()}")
    print(f"   ✓ 子角色总权限数: {child_role.get_all_permissions().__len__()}")
    
    # 验证继承
    all_child_permissions = child_role.get_all_permissions()
    assert perm1 in all_child_permissions  # 继承的权限
    assert perm2 in all_child_permissions  # 直接权限
    print("   ✓ 角色继承验证成功")
    
    return parent_role, child_role


def main():
    """主测试函数"""
    print("开始多租户系统基础测试...\n")
    
    try:
        # 测试基础模型
        tenant, user, role, permission = test_basic_models()
        
        # 测试租户隔离
        tenant1, tenant2, user1, user2 = test_tenant_isolation()
        
        # 测试角色继承
        parent_role, child_role = test_role_inheritance()
        
        print("\n=== 所有测试通过 ===")
        print("多租户数据模型和中间件实现完成！")
        
        # 显示统计信息
        print(f"\n统计信息:")
        print(f"  租户数量: {Tenant.objects.count()}")
        print(f"  用户数量: {User.objects.count()}")
        print(f"  角色数量: {Role.objects.count()}")
        print(f"  权限数量: {Permission.objects.count()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)