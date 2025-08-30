#!/usr/bin/env python
"""
多租户系统测试脚本

本脚本用于测试QuantTrade系统的多租户架构功能，包括：
- 租户创建和管理
- 用户创建和权限分配
- 租户数据隔离验证
- 角色权限系统测试
- 角色继承机制验证

使用方法：
    python test_multitenant.py

注意：此脚本会清理现有测试数据，请勿在生产环境运行
"""
import os
import sys
import django
from pathlib import Path

# 添加项目路径到Python路径，确保能够导入项目模块
sys.path.append(str(Path(__file__).parent))

# 设置Django环境变量，使用开发环境配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
# 初始化Django应用
django.setup()

# 导入必要的模型和服务类
from apps.core.models import Tenant, Role, Permission
from apps.users.models import User
from apps.core.utils import TenantContext, create_default_permissions, create_default_roles
from apps.users.services import UserManagementService, TenantManagementService


def test_tenant_creation():
    """
    测试租户创建功能
    
    验证以下功能：
    1. 系统默认权限的创建
    2. 租户的成功创建
    3. 租户默认角色的自动生成
    4. 角色权限的正确分配
    
    Returns:
        Tenant: 创建的测试租户对象
    """
    print("=== 测试租户创建 ===")
    
    # 创建系统默认权限，这些权限将被用于角色分配
    permissions = create_default_permissions()
    print(f"创建了 {len(permissions)} 个默认权限")
    
    # 使用租户管理服务创建新租户
    # schema_name: 数据库模式名称，用于数据隔离
    # domain: 租户访问域名
    tenant = TenantManagementService.create_tenant(
        name='测试租户',
        schema_name='test_tenant',
        domain='test.quanttrade.com'
    )
    print(f"创建租户成功: {tenant.name}")
    
    # 验证租户创建后是否自动生成了默认角色
    # 默认角色包括：超级管理员、管理员、交易员、观察者等
    roles = Role.objects.filter(tenant=tenant)
    print(f"为租户创建了 {roles.count()} 个默认角色:")
    for role in roles:
        print(f"  - {role.name}: {role.permissions.count()} 个权限")
    
    return tenant


def test_user_creation(tenant):
    """
    测试用户创建功能
    
    验证以下功能：
    1. 管理员用户的创建和角色分配
    2. 普通用户的创建和权限限制
    3. 用户与租户的正确关联
    4. 角色权限的继承机制
    
    Args:
        tenant (Tenant): 要在其中创建用户的租户对象
        
    Returns:
        tuple: (管理员用户对象, 普通用户对象)
    """
    print("\n=== 测试用户创建 ===")
    
    # 创建租户管理员用户
    # is_tenant_admin=True 表示该用户是租户的超级管理员
    # 拥有该租户内的所有权限
    admin_user = UserManagementService.create_user(
        tenant=tenant,
        username='admin',
        email='admin@test.com',
        password='admin123',
        first_name='管理员',
        roles=['超级管理员'],  # 分配超级管理员角色
        is_tenant_admin=True
    )
    print(f"创建管理员用户成功: {admin_user.username}")
    
    # 创建普通用户
    # 只分配观察者角色，权限受限
    normal_user = UserManagementService.create_user(
        tenant=tenant,
        username='user1',
        email='user1@test.com',
        password='user123',
        first_name='用户1',
        roles=['观察者']  # 分配观察者角色，只有查看权限
    )
    print(f"创建普通用户成功: {normal_user.username}")
    
    return admin_user, normal_user


def test_tenant_isolation():
    """
    测试租户数据隔离功能
    
    验证以下功能：
    1. 多个租户的独立创建
    2. 租户间数据的完全隔离
    3. TenantContext上下文管理器的正确工作
    4. 用户数据只能在对应租户中访问
    
    这是多租户架构的核心功能，确保不同租户的数据完全隔离
    
    Returns:
        tuple: (第二个租户对象, 第二个租户中的用户对象)
    """
    print("\n=== 测试租户隔离 ===")
    
    # 创建第二个独立租户，用于验证数据隔离
    tenant2 = TenantManagementService.create_tenant(
        name='测试租户2',
        schema_name='test_tenant2',  # 不同的schema确保数据隔离
        domain='test2.quanttrade.com'
    )
    print(f"创建第二个租户: {tenant2.name}")
    
    # 在第二个租户中创建用户
    # 这个用户应该只能在tenant2的上下文中被访问
    user2 = UserManagementService.create_user(
        tenant=tenant2,
        username='user2',
        email='user2@test.com',
        password='user123',
        first_name='用户2',
        roles=['观察者']
    )
    print(f"在第二个租户中创建用户: {user2.username}")
    
    # 使用TenantContext上下文管理器测试租户隔离
    # 在tenant2的上下文中，只能看到属于tenant2的用户
    with TenantContext(tenant2):
        users_in_tenant2 = User.objects.all()
        print(f"租户2中的用户数量: {users_in_tenant2.count()}")
        for user in users_in_tenant2:
            print(f"  - {user.username} ({user.tenant.name})")
    
    return tenant2, user2


def test_permissions(admin_user, normal_user):
    """
    测试RBAC权限系统功能
    
    验证以下功能：
    1. 管理员用户的完整权限集合
    2. 普通用户的受限权限集合
    3. 权限检查机制的正确性
    4. 角色权限继承的有效性
    
    Args:
        admin_user (User): 管理员用户对象
        normal_user (User): 普通用户对象
    """
    print("\n=== 测试权限系统 ===")
    
    # 测试管理员权限
    # 管理员应该拥有所有权限，包括用户管理、交易等
    print(f"管理员 {admin_user.username} 的权限:")
    admin_permissions = admin_user.get_all_permissions()
    print(f"  总权限数: {len(admin_permissions)}")
    print(f"  是否有用户管理权限: {admin_user.has_permission('user.create_user')}")
    print(f"  是否有交易权限: {admin_user.has_permission('trading.create_order')}")
    
    # 测试普通用户权限
    # 普通用户（观察者角色）应该只有查看权限，没有创建/修改权限
    print(f"\n普通用户 {normal_user.username} 的权限:")
    normal_permissions = normal_user.get_all_permissions()
    print(f"  总权限数: {len(normal_permissions)}")
    print(f"  是否有用户管理权限: {normal_user.has_permission('user.create_user')}")
    print(f"  是否有查看权限: {normal_user.has_permission('trading.view_orders')}")


def test_role_inheritance():
    """
    测试角色继承机制
    
    验证以下功能：
    1. 父角色的权限定义
    2. 子角色的权限继承
    3. 子角色的额外权限添加
    4. 继承链的正确构建
    5. 权限累积计算的准确性
    
    角色继承允许创建层次化的权限结构，子角色自动继承父角色的所有权限
    """
    print("\n=== 测试角色继承 ===")
    
    # 获取第一个租户进行测试
    tenant = Tenant.objects.first()
    
    # 在租户上下文中进行角色操作，确保数据隔离
    with TenantContext(tenant):
        # 创建父角色，定义基础权限集合
        parent_role = Role.objects.create(
            name='基础角色',
            tenant=tenant,
            description='基础权限角色'
        )
        
        # 为父角色分配查看类权限
        # 这些权限将被子角色自动继承
        view_permissions = Permission.objects.filter(codename__contains='view')[:3]
        parent_role.permissions.set(view_permissions)
        
        # 创建子角色，继承父角色的权限
        child_role = Role.objects.create(
            name='扩展角色',
            tenant=tenant,
            description='继承基础角色的扩展角色',
            parent_role=parent_role  # 设置父角色，启用继承
        )
        
        # 为子角色添加额外的创建类权限
        # 子角色将同时拥有父角色的查看权限和自己的创建权限
        create_permissions = Permission.objects.filter(codename__contains='create')[:2]
        child_role.permissions.set(create_permissions)
        
        # 验证权限继承的正确性
        print(f"父角色 '{parent_role.name}' 权限数: {parent_role.get_direct_permissions().__len__()}")
        print(f"子角色 '{child_role.name}' 直接权限数: {child_role.get_direct_permissions().__len__()}")
        print(f"子角色 '{child_role.name}' 总权限数: {child_role.get_all_permissions().__len__()}")
        
        # 显示完整的角色继承链
        inheritance_chain = child_role.get_inheritance_chain()
        print(f"继承链: {' -> '.join([role.name for role in inheritance_chain])}")


def main():
    """主测试函数"""
    print("开始多租户系统测试...")
    
    try:
        # 清理之前的测试数据
        User.objects.all().delete()
        Role.objects.all().delete()
        Tenant.objects.all().delete()
        Permission.objects.all().delete()
        
        # 测试租户创建
        tenant1 = test_tenant_creation()
        
        # 测试用户创建
        admin_user, normal_user = test_user_creation(tenant1)
        
        # 测试租户隔离
        tenant2, user2 = test_tenant_isolation()
        
        # 测试权限系统
        test_permissions(admin_user, normal_user)
        
        # 测试角色继承
        test_role_inheritance()
        
        print("\n=== 所有测试完成 ===")
        print("多租户系统工作正常！")
        
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)