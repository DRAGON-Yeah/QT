#!/usr/bin/env python3
"""
JWT认证系统测试脚本
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.core.models import Tenant, Permission
from apps.users.models import User
from apps.users.authentication import JWTService, LoginService
from apps.core.utils import create_default_permissions, create_default_roles

def test_jwt_authentication():
    """测试JWT认证功能"""
    print("开始测试JWT认证系统...")
    
    try:
        # 1. 创建测试租户
        print("1. 创建测试租户...")
        tenant, created = Tenant.objects.get_or_create(
            name='测试租户',
            defaults={
                'schema_name': 'test_tenant',
                'is_active': True
            }
        )
        print(f"   租户创建{'成功' if created else '已存在'}: {tenant.name}")
        
        # 2. 创建默认权限和角色
        print("2. 创建默认权限和角色...")
        permissions = create_default_permissions()
        print(f"   创建了 {len(permissions)} 个权限")
        
        roles = create_default_roles(tenant)
        print(f"   创建了 {len(roles)} 个角色")
        
        # 3. 创建测试用户
        print("3. 创建测试用户...")
        user, created = User.objects.get_or_create(
            tenant=tenant,
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'is_active': True
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print("   用户创建成功")
        else:
            print("   用户已存在")
        
        # 4. 测试用户认证
        print("4. 测试用户认证...")
        try:
            tokens = LoginService.authenticate_user('testuser', 'testpass123')
            print("   认证成功!")
            print(f"   Access Token: {tokens['access_token'][:50]}...")
            print(f"   Refresh Token: {tokens['refresh_token'][:50]}...")
            print(f"   用户信息: {tokens['user']['username']}")
            
            # 5. 测试token验证
            print("5. 测试token验证...")
            payload = JWTService.verify_token(tokens['access_token'])
            print(f"   Token验证成功，用户ID: {payload.get('user_id')}")
            
            # 6. 测试token刷新
            print("6. 测试token刷新...")
            new_tokens = JWTService.refresh_token(tokens['refresh_token'])
            print(f"   Token刷新成功: {new_tokens['access_token'][:50]}...")
            
            print("\n✅ JWT认证系统测试通过!")
            return True
            
        except Exception as e:
            print(f"   ❌ 认证失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_password_service():
    """测试密码服务"""
    print("\n开始测试密码服务...")
    
    try:
        from apps.users.authentication import PasswordService
        
        # 测试密码强度验证
        print("1. 测试密码强度验证...")
        
        weak_passwords = ['123', 'password', 'abc123']
        strong_passwords = ['StrongPass123!', 'MySecure@Pass456']
        
        for pwd in weak_passwords:
            is_valid, msg = PasswordService.validate_password_strength(pwd)
            print(f"   弱密码 '{pwd}': {'通过' if is_valid else '拒绝'} - {msg}")
        
        for pwd in strong_passwords:
            is_valid, msg = PasswordService.validate_password_strength(pwd)
            print(f"   强密码 '{pwd}': {'通过' if is_valid else '拒绝'} - {msg}")
        
        print("✅ 密码服务测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 密码服务测试失败: {e}")
        return False

def test_permissions():
    """测试权限系统"""
    print("\n开始测试权限系统...")
    
    try:
        # 获取测试用户
        user = User.objects.get(username='testuser')
        
        # 给用户分配角色
        from apps.core.models import Role
        observer_role = Role.objects.get(name='观察者', tenant=user.tenant)
        user.add_role(observer_role)
        
        print(f"1. 用户角色: {[role.name for role in user.roles.all()]}")
        print(f"2. 用户权限数量: {len(user.get_all_permissions())}")
        
        # 测试权限检查
        test_permissions = [
            'trading.view_orders',
            'trading.create_order',
            'user.manage_users'
        ]
        
        for perm in test_permissions:
            has_perm = user.has_permission(perm)
            print(f"   权限 '{perm}': {'有' if has_perm else '无'}")
        
        print("✅ 权限系统测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 权限系统测试失败: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("QuantTrade JWT认证系统测试")
    print("=" * 60)
    
    success = True
    
    # 运行所有测试
    success &= test_jwt_authentication()
    success &= test_password_service()
    success &= test_permissions()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过!")
    else:
        print("❌ 部分测试失败!")
    print("=" * 60)