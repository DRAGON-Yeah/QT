#!/usr/bin/env python3
"""
API端点测试脚本
"""
import os
import sys
import django
import json

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.test import Client
from django.urls import reverse
from apps.core.models import Tenant
from apps.users.models import User
from apps.core.utils import create_default_permissions, create_default_roles

def test_api_endpoints():
    """测试API端点"""
    print("开始测试API端点...")
    
    try:
        # 1. 创建测试数据
        print("1. 准备测试数据...")
        tenant, _ = Tenant.objects.get_or_create(
            name='API测试租户',
            defaults={'schema_name': 'api_test_tenant'}
        )
        
        create_default_permissions()
        create_default_roles(tenant)
        
        user, created = User.objects.get_or_create(
            tenant=tenant,
            username='apiuser',
            defaults={'email': 'api@example.com', 'is_active': True}
        )
        
        if created:
            user.set_password('apipass123')
            user.save()
            
            # 给用户分配观察者角色
            from apps.core.models import Role
            try:
                observer_role = Role.objects.get(name='观察者', tenant=tenant)
                user.add_role(observer_role)
                print("   已为用户分配观察者角色")
            except Role.DoesNotExist:
                print("   观察者角色不存在，跳过角色分配")
        
        # 2. 创建测试客户端
        client = Client()
        
        # 3. 测试登录API
        print("2. 测试登录API...")
        login_url = '/api/users/auth/login/'
        login_data = {
            'username': 'apiuser',
            'password': 'apipass123'
        }
        
        response = client.post(
            login_url, 
            json.dumps(login_data),
            content_type='application/json'
        )
        
        print(f"   登录响应状态: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("   ✅ 登录成功!")
            
            access_token = response_data['data']['access_token']
            print(f"   获得访问令牌: {access_token[:50]}...")
            
            # 4. 测试需要认证的API
            print("3. 测试用户信息API...")
            profile_url = '/api/users/profile/'
            
            response = client.get(
                profile_url,
                HTTP_AUTHORIZATION=f'Bearer {access_token}',
                HTTP_X_TENANT_ID=str(tenant.id)
            )
            
            print(f"   用户信息响应状态: {response.status_code}")
            
            if response.status_code == 200:
                profile_data = response.json()
                print(f"   ✅ 获取用户信息成功: {profile_data['data']['username']}")
            else:
                print(f"   ❌ 获取用户信息失败: {response.content}")
            
            # 5. 测试用户列表API
            print("4. 测试用户列表API...")
            users_url = '/api/users/users/'
            
            response = client.get(
                users_url,
                HTTP_AUTHORIZATION=f'Bearer {access_token}',
                HTTP_X_TENANT_ID=str(tenant.id)
            )
            
            print(f"   用户列表响应状态: {response.status_code}")
            
            if response.status_code == 200:
                users_data = response.json()
                print(f"   ✅ 获取用户列表成功，共 {len(users_data.get('results', []))} 个用户")
            else:
                print(f"   ❌ 获取用户列表失败: {response.content}")
            
            # 6. 测试登出API
            print("5. 测试登出API...")
            logout_url = '/api/users/auth/logout/'
            
            response = client.post(
                logout_url,
                HTTP_AUTHORIZATION=f'Bearer {access_token}',
                HTTP_X_TENANT_ID=str(tenant.id)
            )
            
            print(f"   登出响应状态: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 登出成功!")
            else:
                print(f"   ❌ 登出失败: {response.content}")
            
            print("\n✅ 所有API端点测试通过!")
            return True
            
        else:
            print(f"   ❌ 登录失败: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("QuantTrade API端点测试")
    print("=" * 60)
    
    success = test_api_endpoints()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 API端点测试通过!")
    else:
        print("❌ API端点测试失败!")
    print("=" * 60)