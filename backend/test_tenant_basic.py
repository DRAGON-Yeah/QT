#!/usr/bin/env python
"""
基础多租户测试
"""
import os
import sys
import django
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')
django.setup()

from django.test import TestCase
from apps.core.models import Tenant, Role, Permission
from apps.users.models import User
from apps.core.utils import TenantContext, create_default_permissions


class BasicTenantTest:
    """基础租户测试"""
    
    def test_create_tenant(self):
        """测试创建租户"""
        print("测试创建租户...")
        
        tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        assert tenant.name == '测试租户'
        assert tenant.schema_name == 'test_tenant'
        assert tenant.is_active == True
        print("✓ 租户创建成功")
        
        return tenant
    
    def test_create_permissions(self):
        """测试创建权限"""
        print("测试创建权限...")
        
        permissions = create_default_permissions()
        
        assert len(permissions) > 0
        print(f"✓ 创建了 {len(permissions)} 个权限")
        
        return permissions
    
    def test_create_role(self):
        """测试创建角色"""
        print("测试创建角色...")
        
        tenant = Tenant.objects.create(
            name='测试租户2',
            schema_name='test_tenant2'
        )
        
        # 创建权限
        permission = Permission.objects.create(
            name='测试权限',
            codename='test.permission',
            category='system'
        )
        
        # 创建角色
        role = Role.objects.create(
            name='测试角色',
            tenant=tenant,
            description='测试角色描述'
        )
        role.permissions.add(permission)
        
        assert role.name == '测试角色'
        assert role.tenant == tenant
        assert role.permissions.count() == 1
        print("✓ 角色创建成功")
        
        return role
    
    def test_create_user(self):
        """测试创建用户"""
        print("测试创建用户...")
        
        tenant = Tenant.objects.create(
            name='测试租户3',
            schema_name='test_tenant3'
        )
        
        user = User.objects.create(
            tenant=tenant,
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpass123')
        user.save()
        
        assert user.username == 'testuser'
        assert user.tenant == tenant
        assert user.check_password('testpass123')
        print("✓ 用户创建成功")
        
        return user
    
    def test_tenant_context(self):
        """测试租户上下文"""
        print("测试租户上下文...")
        
        tenant1 = Tenant.objects.create(
            name='租户1',
            schema_name='tenant1'
        )
        
        tenant2 = Tenant.objects.create(
            name='租户2',
            schema_name='tenant2'
        )
        
        # 在租户1上下文中创建用户
        with TenantContext(tenant1):
            user1 = User.objects.create(
                tenant=tenant1,
                username='user1',
                email='user1@example.com'
            )
        
        # 在租户2上下文中创建用户
        with TenantContext(tenant2):
            user2 = User.objects.create(
                tenant=tenant2,
                username='user2',
                email='user2@example.com'
            )
        
        # 验证用户属于正确的租户
        assert user1.tenant == tenant1
        assert user2.tenant == tenant2
        print("✓ 租户上下文工作正常")
        
        return tenant1, tenant2, user1, user2
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=== 开始基础多租户测试 ===\n")
        
        try:
            self.test_create_tenant()
            self.test_create_permissions()
            self.test_create_role()
            self.test_create_user()
            self.test_tenant_context()
            
            print("\n=== 所有测试通过 ===")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    test = BasicTenantTest()
    success = test.run_all_tests()
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)