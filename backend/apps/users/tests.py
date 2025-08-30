"""
用户管理测试
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.core.models import Tenant, Role, Permission
from apps.core.utils import TenantContext, create_default_permissions, create_default_roles
from .models import User, UserProfile, UserRole
from .services import UserManagementService, AuthenticationService

User = get_user_model()


class UserModelTest(TestCase):
    """用户模型测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        # 创建默认权限和角色
        create_default_permissions()
        create_default_roles(self.tenant)
    
    def test_create_user(self):
        """测试创建用户"""
        user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.tenant, self.tenant)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_tenant_admin)
    
    def test_user_permissions(self):
        """测试用户权限"""
        user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        
        # 创建权限
        permission = Permission.objects.create(
            name='测试权限',
            codename='test.permission',
            category='system'
        )
        
        # 创建角色并分配权限
        role = Role.objects.create(
            name='测试角色',
            tenant=self.tenant
        )
        role.permissions.add(permission)
        
        # 给用户分配角色
        user.add_role(role)
        
        # 测试权限检查
        self.assertTrue(user.has_permission('test.permission'))
        self.assertFalse(user.has_permission('nonexistent.permission'))
    
    def test_user_roles(self):
        """测试用户角色"""
        user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        
        role = Role.objects.create(
            name='测试角色',
            tenant=self.tenant
        )
        
        # 添加角色
        user.add_role(role)
        self.assertTrue(user.has_role('测试角色'))
        
        # 移除角色
        user.remove_role(role)
        self.assertFalse(user.has_role('测试角色'))
    
    def test_account_locking(self):
        """测试账户锁定"""
        user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        
        # 测试账户锁定
        user.lock_account(30)
        self.assertTrue(user.is_account_locked())
        
        # 测试账户解锁
        user.unlock_account()
        self.assertFalse(user.is_account_locked())
    
    def test_failed_login_attempts(self):
        """测试登录失败次数"""
        user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        
        # 记录登录失败
        for i in range(4):
            user.record_failed_login()
            self.assertFalse(user.is_account_locked())
        
        # 第5次失败应该锁定账户
        user.record_failed_login()
        self.assertTrue(user.is_account_locked())


class UserManagementServiceTest(TestCase):
    """用户管理服务测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        create_default_permissions()
        create_default_roles(self.tenant)
    
    def test_create_user_service(self):
        """测试用户创建服务"""
        user = UserManagementService.create_user(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            roles=['观察者']
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.has_role('观察者'))
        
        # 检查是否创建了用户配置
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_update_user_service(self):
        """测试用户更新服务"""
        user = UserManagementService.create_user(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        updated_user = UserManagementService.update_user(
            user,
            first_name='Updated',
            last_name='Name',
            roles=['交易员']
        )
        
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertTrue(updated_user.has_role('交易员'))
    
    def test_delete_user_service(self):
        """测试用户删除服务"""
        user = UserManagementService.create_user(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        success = UserManagementService.delete_user(user)
        
        self.assertTrue(success)
        user.refresh_from_db()
        self.assertFalse(user.is_active)


class AuthenticationServiceTest(TestCase):
    """认证服务测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        self.user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpass123')
        self.user.save()
    
    def test_authenticate_user_success(self):
        """测试用户认证成功"""
        user = AuthenticationService.authenticate_user(
            username='testuser',
            password='testpass123',
            tenant=self.tenant,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
    
    def test_authenticate_user_failure(self):
        """测试用户认证失败"""
        user = AuthenticationService.authenticate_user(
            username='testuser',
            password='wrongpassword',
            tenant=self.tenant,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertIsNone(user)
    
    def test_authenticate_locked_user(self):
        """测试锁定用户认证"""
        self.user.lock_account()
        
        user = AuthenticationService.authenticate_user(
            username='testuser',
            password='testpass123',
            tenant=self.tenant,
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertIsNone(user)


class UserManagementAPITest(APITestCase):
    """用户管理API测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        create_default_permissions()
        create_default_roles(self.tenant)
        
        # 创建管理员用户
        self.admin_user = User.objects.create(
            tenant=self.tenant,
            username='admin',
            email='admin@example.com',
            is_tenant_admin=True
        )
        self.admin_user.set_password('adminpass123')
        self.admin_user.save()
        
        # 创建普通用户
        self.normal_user = User.objects.create(
            tenant=self.tenant,
            username='user',
            email='user@example.com'
        )
        self.normal_user.set_password('userpass123')
        self.normal_user.save()
        
        self.client = APIClient()
    
    def test_get_user_list_as_admin(self):
        """测试管理员获取用户列表"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('users:user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_create_user_as_admin(self):
        """测试管理员创建用户"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('users:user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role_ids': []
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_update_user_as_admin(self):
        """测试管理员更新用户"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('users:user-detail', kwargs={'pk': self.normal_user.id})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.first_name, 'Updated')
    
    def test_delete_user_as_admin(self):
        """测试管理员删除用户"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('users:user-detail', kwargs={'pk': self.normal_user.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)
    
    def test_change_password(self):
        """测试修改密码"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('users:user-change-password', kwargs={'pk': self.normal_user.id})
        data = {
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
            'force_change': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_toggle_user_status(self):
        """测试切换用户状态"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('users:user-toggle-status', kwargs={'pk': self.normal_user.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)
    
    def test_get_user_statistics(self):
        """测试获取用户统计"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('users:user-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data['data'])
        self.assertIn('active_users', response.data['data'])


class RoleManagementAPITest(APITestCase):
    """角色管理API测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        create_default_permissions()
        create_default_roles(self.tenant)
        
        self.admin_user = User.objects.create(
            tenant=self.tenant,
            username='admin',
            email='admin@example.com',
            is_tenant_admin=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_get_role_list(self):
        """测试获取角色列表"""
        url = reverse('users:role-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_create_role(self):
        """测试创建角色"""
        url = reverse('users:role-list')
        data = {
            'name': '测试角色',
            'description': '这是一个测试角色',
            'permission_ids': []
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Role.objects.filter(name='测试角色').exists())
    
    def test_update_role(self):
        """测试更新角色"""
        role = Role.objects.create(
            name='测试角色',
            tenant=self.tenant
        )
        
        url = reverse('users:role-detail', kwargs={'pk': role.id})
        data = {
            'description': '更新后的描述'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        role.refresh_from_db()
        self.assertEqual(role.description, '更新后的描述')
    
    def test_delete_role(self):
        """测试删除角色"""
        role = Role.objects.create(
            name='测试角色',
            tenant=self.tenant
        )
        
        url = reverse('users:role-detail', kwargs={'pk': role.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Role.objects.filter(id=role.id).exists())
    
    def test_get_permissions(self):
        """测试获取权限列表"""
        url = reverse('users:permission-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['data'], dict)


class TenantIsolationTest(APITestCase):
    """租户隔离测试"""
    
    def setUp(self):
        # 创建两个租户
        self.tenant1 = Tenant.objects.create(
            name='租户1',
            schema_name='tenant1'
        )
        self.tenant2 = Tenant.objects.create(
            name='租户2',
            schema_name='tenant2'
        )
        
        create_default_permissions()
        create_default_roles(self.tenant1)
        create_default_roles(self.tenant2)
        
        # 为每个租户创建用户
        self.user1 = User.objects.create(
            tenant=self.tenant1,
            username='user1',
            email='user1@example.com',
            is_tenant_admin=True
        )
        
        self.user2 = User.objects.create(
            tenant=self.tenant2,
            username='user2',
            email='user2@example.com',
            is_tenant_admin=True
        )
        
        self.client = APIClient()
    
    def test_user_cannot_see_other_tenant_users(self):
        """测试用户不能看到其他租户的用户"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('users:user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 应该只能看到自己租户的用户
        usernames = [user['username'] for user in response.data['results']]
        self.assertIn('user1', usernames)
        self.assertNotIn('user2', usernames)
    
    def test_user_cannot_access_other_tenant_user_detail(self):
        """测试用户不能访问其他租户的用户详情"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('users:user-detail', kwargs={'pk': self.user2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_role_isolation(self):
        """测试角色隔离"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('users:role-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 应该只能看到自己租户的角色
        for role in response.data:
            # 这里需要根据实际的序列化器结构调整
            pass  # 实际测试中需要检查角色的租户ID


class JWTAuthenticationTest(APITestCase):
    """JWT认证测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        create_default_permissions()
        create_default_roles(self.tenant)
        
        self.user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpass123')
        self.user.save()
        
        self.client = APIClient()
    
    def test_login_success(self):
        """测试登录成功"""
        url = reverse('users:login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data['data'])
        self.assertIn('refresh_token', response.data['data'])
        self.assertIn('user', response.data['data'])
    
    def test_login_failure(self):
        """测试登录失败"""
        url = reverse('users:login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_login_locked_user(self):
        """测试锁定用户登录"""
        self.user.lock_account()
        
        url = reverse('users:login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_logout(self):
        """测试登出"""
        # 先登录获取token
        login_url = reverse('users:login')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['data']['access_token']
        
        # 使用token认证
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 登出
        logout_url = reverse('users:logout')
        response = self.client.post(logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_token_refresh(self):
        """测试token刷新"""
        # 先登录获取token
        login_url = reverse('users:login')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['data']['refresh_token']
        
        # 刷新token
        refresh_url = reverse('users:token-refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data['data'])
    
    def test_change_password(self):
        """测试修改密码"""
        # 先登录
        login_url = reverse('users:login')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['data']['access_token']
        
        # 使用token认证
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 修改密码
        change_password_url = reverse('users:change-password')
        change_data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(change_password_url, change_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # 验证新密码可以登录
        new_login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'newpass123'
        }, format='json')
        
        self.assertEqual(new_login_response.status_code, status.HTTP_200_OK)
    
    def test_user_profile(self):
        """测试获取用户个人信息"""
        # 先登录
        login_url = reverse('users:login')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['data']['access_token']
        
        # 使用token认证
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 获取用户信息
        profile_url = reverse('users:user-profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'testuser')
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        # 不提供token，直接访问需要认证的接口
        profile_url = reverse('users:user-profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_token(self):
        """测试无效token"""
        # 使用无效token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        profile_url = reverse('users:user-profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordServiceTest(TestCase):
    """密码服务测试"""
    
    def setUp(self):
        from .authentication import PasswordService
        self.password_service = PasswordService
        
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        self.user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('oldpass123')
        self.user.save()
    
    def test_validate_password_strength(self):
        """测试密码强度验证"""
        # 测试弱密码
        is_valid, message = self.password_service.validate_password_strength('123')
        self.assertFalse(is_valid)
        
        # 测试强密码
        is_valid, message = self.password_service.validate_password_strength('StrongPass123!')
        self.assertTrue(is_valid)
    
    def test_change_password_success(self):
        """测试修改密码成功"""
        success = self.password_service.change_password(
            self.user, 'oldpass123', 'NewPass123!'
        )
        
        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))
    
    def test_change_password_wrong_old_password(self):
        """测试修改密码时旧密码错误"""
        from rest_framework import exceptions
        
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.password_service.change_password(
                self.user, 'wrongpass', 'NewPass123!'
            )
    
    def test_reset_password(self):
        """测试重置密码"""
        success = self.password_service.reset_password(
            self.user, 'ResetPass123!'
        )
        
        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ResetPass123!'))


class SessionServiceTest(TestCase):
    """会话服务测试"""
    
    def setUp(self):
        from .authentication import SessionService
        self.session_service = SessionService
        
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        self.user = User.objects.create(
            tenant=self.tenant,
            username='testuser',
            email='test@example.com'
        )
        
        # 创建测试会话
        from .models import UserSession
        from django.utils import timezone
        
        self.session = UserSession.objects.create(
            user=self.user,
            session_key='test_session_key',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
    
    def test_get_active_sessions(self):
        """测试获取活跃会话"""
        sessions = self.session_service.get_active_sessions(self.user)
        
        self.assertEqual(sessions.count(), 1)
        self.assertEqual(sessions.first().session_key, 'test_session_key')
    
    def test_terminate_session(self):
        """测试终止会话"""
        success = self.session_service.terminate_session(
            self.user, self.session.id
        )
        
        self.assertTrue(success)
        self.session.refresh_from_db()
        self.assertFalse(self.session.is_active)
    
    def test_cleanup_expired_sessions(self):
        """测试清理过期会话"""
        # 创建过期会话
        from .models import UserSession
        from django.utils import timezone
        
        expired_session = UserSession.objects.create(
            user=self.user,
            session_key='expired_session',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        
        count = self.session_service.cleanup_expired_sessions()
        
        self.assertGreater(count, 0)
        expired_session.refresh_from_db()
        self.assertFalse(expired_session.is_active)