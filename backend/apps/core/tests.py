"""
核心模块单元测试
"""
import uuid
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch, Mock

from .models import Tenant, Role, Permission, Menu
from .utils import (
    set_current_tenant, get_current_tenant, clear_current_tenant,
    TenantContext, get_tenant_cache_key, create_default_permissions,
    create_default_roles
)
from .middleware import TenantMiddleware, TenantAccessControlMiddleware

User = get_user_model()


class TenantModelTest(TestCase):
    """租户模型测试"""
    
    def setUp(self):
        self.tenant_data = {
            'name': '测试租户',
            'schema_name': 'test_tenant',
            'domain': 'test.example.com',
            'max_users': 50,
            'max_strategies': 25,
            'max_exchange_accounts': 5
        }
    
    def test_create_tenant(self):
        """测试创建租户"""
        tenant = Tenant.objects.create(**self.tenant_data)
        
        self.assertEqual(tenant.name, '测试租户')
        self.assertEqual(tenant.schema_name, 'test_tenant')
        self.assertTrue(tenant.is_active)
        self.assertIsNotNone(tenant.id)
        self.assertTrue(isinstance(tenant.id, uuid.UUID))
    
    def test_tenant_validation(self):
        """测试租户数据验证"""
        # 测试无效的schema_name
        invalid_data = self.tenant_data.copy()
        invalid_data['schema_name'] = 'invalid-schema-name'
        
        tenant = Tenant(**invalid_data)
        with self.assertRaises(ValidationError):
            tenant.clean()
    
    def test_tenant_subscription_check(self):
        """测试租户订阅检查"""
        tenant = Tenant.objects.create(**self.tenant_data)
        
        # 没有设置过期时间，应该是有效的
        self.assertTrue(tenant.is_subscription_active())
        
        # 设置未来的过期时间
        tenant.subscription_expires_at = timezone.now() + timezone.timedelta(days=30)
        tenant.save()
        self.assertTrue(tenant.is_subscription_active())
        
        # 设置过去的过期时间
        tenant.subscription_expires_at = timezone.now() - timezone.timedelta(days=1)
        tenant.save()
        self.assertFalse(tenant.is_subscription_active())
    
    def test_tenant_user_limit(self):
        """测试租户用户数量限制"""
        tenant = Tenant.objects.create(**self.tenant_data)
        
        # 创建用户直到达到限制
        for i in range(tenant.max_users):
            User.objects.create(
                username=f'user{i}',
                tenant=tenant,
                email=f'user{i}@test.com'
            )
        
        # 应该无法再添加用户
        self.assertFalse(tenant.can_add_user())
        
        # 删除一个用户后应该可以添加
        User.objects.filter(tenant=tenant).first().delete()
        self.assertTrue(tenant.can_add_user())


class PermissionModelTest(TestCase):
    """权限模型测试"""
    
    def test_create_permission(self):
        """测试创建权限"""
        permission = Permission.objects.create(
            name='测试权限',
            codename='test.permission',
            category='system',
            description='这是一个测试权限'
        )
        
        self.assertEqual(permission.name, '测试权限')
        self.assertEqual(permission.codename, 'test.permission')
        self.assertEqual(permission.category, 'system')
    
    def test_permission_str(self):
        """测试权限字符串表示"""
        permission = Permission.objects.create(
            name='测试权限',
            codename='test.permission',
            category='system'
        )
        
        expected_str = "测试权限 (test.permission)"
        self.assertEqual(str(permission), expected_str)


class RoleModelTest(TestCase):
    """角色模型测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        self.permission1 = Permission.objects.create(
            name='权限1',
            codename='perm1',
            category='system'
        )
        
        self.permission2 = Permission.objects.create(
            name='权限2',
            codename='perm2',
            category='user'
        )
    
    def test_create_role(self):
        """测试创建角色"""
        with TenantContext(self.tenant):
            role = Role.objects.create(
                name='测试角色',
                description='这是一个测试角色',
                tenant=self.tenant,
                priority=50,
                color='#FF5722'
            )
            
            role.permissions.add(self.permission1, self.permission2)
            
            self.assertEqual(role.name, '测试角色')
            self.assertEqual(role.tenant, self.tenant)
            self.assertEqual(role.priority, 50)
            self.assertEqual(role.color, '#FF5722')
            self.assertEqual(role.permissions.count(), 2)
    
    def test_role_priority_ordering(self):
        """测试角色优先级排序"""
        with TenantContext(self.tenant):
            role1 = Role.objects.create(
                name='低优先级角色',
                tenant=self.tenant,
                priority=10
            )
            role2 = Role.objects.create(
                name='高优先级角色',
                tenant=self.tenant,
                priority=90
            )
            role3 = Role.objects.create(
                name='中优先级角色',
                tenant=self.tenant,
                priority=50
            )
            
            # 测试排序：应该按优先级降序排列
            roles = list(Role.objects.all())
            self.assertEqual(roles[0], role2)  # 优先级90
            self.assertEqual(roles[1], role3)  # 优先级50
            self.assertEqual(roles[2], role1)  # 优先级10
    
    def test_circular_inheritance_prevention(self):
        """测试循环继承防护"""
        with TenantContext(self.tenant):
            role1 = Role.objects.create(
                name='角色1',
                tenant=self.tenant
            )
            role2 = Role.objects.create(
                name='角色2',
                tenant=self.tenant,
                parent_role=role1
            )
            
            # 尝试创建循环继承：role1 -> role2 -> role1
            role1.parent_role = role2
            
            with self.assertRaises(ValidationError):
                role1.clean()
    
    def test_role_permission_inheritance(self):
        """测试角色权限继承"""
        with TenantContext(self.tenant):
            # 创建父角色
            parent_role = Role.objects.create(
                name='父角色',
                tenant=self.tenant
            )
            parent_role.permissions.add(self.permission1)
            
            # 创建子角色
            child_role = Role.objects.create(
                name='子角色',
                tenant=self.tenant,
                parent_role=parent_role
            )
            child_role.permissions.add(self.permission2)
            
            # 子角色应该拥有父角色的权限
            all_permissions = child_role.get_all_permissions()
            permission_codenames = {perm.codename for perm in all_permissions}
            
            self.assertIn('perm1', permission_codenames)  # 继承的权限
            self.assertIn('perm2', permission_codenames)  # 自己的权限
            
            # 测试权限来源分析
            direct_perms = child_role.get_direct_permissions()
            inherited_perms = child_role.get_inherited_permissions()
            
            self.assertEqual(len(direct_perms), 1)
            self.assertEqual(len(inherited_perms), 1)
            self.assertIn(self.permission2, direct_perms)
            self.assertIn(self.permission1, inherited_perms)
    
    def test_role_has_permission(self):
        """测试角色权限检查"""
        with TenantContext(self.tenant):
            role = Role.objects.create(
                name='测试角色',
                tenant=self.tenant
            )
            role.permissions.add(self.permission1)
            
            self.assertTrue(role.has_permission('perm1'))
            self.assertFalse(role.has_permission('perm2'))
    
    def test_inheritance_chain(self):
        """测试角色继承链"""
        with TenantContext(self.tenant):
            # 创建三级继承：观察者 -> 交易员 -> 管理员
            admin_role = Role.objects.create(
                name='管理员',
                tenant=self.tenant,
                priority=80
            )
            trader_role = Role.objects.create(
                name='交易员',
                tenant=self.tenant,
                parent_role=admin_role,
                priority=60
            )
            observer_role = Role.objects.create(
                name='观察者',
                tenant=self.tenant,
                parent_role=trader_role,
                priority=20
            )
            
            # 测试继承链
            chain = observer_role.get_inheritance_chain()
            self.assertEqual(len(chain), 3)
            self.assertEqual(chain[0], observer_role)
            self.assertEqual(chain[1], trader_role)
            self.assertEqual(chain[2], admin_role)
    
    def test_role_deletion_constraints(self):
        """测试角色删除限制"""
        with TenantContext(self.tenant):
            # 测试系统角色不能删除
            system_role = Role.objects.create(
                name='系统角色',
                tenant=self.tenant,
                role_type='system'
            )
            can_delete, reason = system_role.can_be_deleted()
            self.assertFalse(can_delete)
            self.assertIn('系统预定义角色', reason)
            
            # 测试有子角色的角色不能删除
            parent_role = Role.objects.create(
                name='父角色',
                tenant=self.tenant,
                role_type='custom'
            )
            child_role = Role.objects.create(
                name='子角色',
                tenant=self.tenant,
                parent_role=parent_role,
                role_type='custom'
            )
            
            can_delete, reason = parent_role.can_be_deleted()
            self.assertFalse(can_delete)
            self.assertIn('子角色', reason)
            
            # 测试可以删除的角色
            can_delete, reason = child_role.can_be_deleted()
            self.assertTrue(can_delete)
    
    def test_copy_permissions(self):
        """测试权限复制"""
        with TenantContext(self.tenant):
            source_role = Role.objects.create(
                name='源角色',
                tenant=self.tenant
            )
            source_role.permissions.add(self.permission1, self.permission2)
            
            target_role = Role.objects.create(
                name='目标角色',
                tenant=self.tenant
            )
            
            # 复制权限
            target_role.copy_permissions_from(source_role)
            
            # 验证权限已复制
            self.assertEqual(
                set(source_role.permissions.all()),
                set(target_role.permissions.all())
            )
    
    def test_create_system_roles(self):
        """测试系统角色创建"""
        with TenantContext(self.tenant):
            # 创建一些权限用于测试
            Permission.objects.create(
                name='查看用户',
                codename='user.view_users',
                category='user'
            )
            Permission.objects.create(
                name='创建订单',
                codename='trading.create_order',
                category='trading'
            )
            
            # 创建系统角色
            created_roles = Role.create_system_roles(self.tenant)
            
            # 验证创建了4个角色
            self.assertEqual(len(created_roles), 4)
            
            # 验证角色名称和优先级
            role_names = {role.name for role in created_roles}
            expected_names = {'超级管理员', '管理员', '交易员', '观察者'}
            self.assertEqual(role_names, expected_names)
            
            # 验证优先级设置
            admin_role = next(r for r in created_roles if r.name == '超级管理员')
            self.assertEqual(admin_role.priority, 100)
            self.assertEqual(admin_role.color, '#F5222D')
            
            # 验证不会重复创建
            created_again = Role.create_system_roles(self.tenant)
            self.assertEqual(len(created_again), 0)


class TenantUtilsTest(TestCase):
    """租户工具函数测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
    
    def test_tenant_context(self):
        """测试租户上下文管理"""
        # 初始状态没有租户
        self.assertIsNone(get_current_tenant())
        
        # 设置租户
        set_current_tenant(self.tenant)
        self.assertEqual(get_current_tenant(), self.tenant)
        
        # 清除租户
        clear_current_tenant()
        self.assertIsNone(get_current_tenant())
    
    def test_tenant_context_manager(self):
        """测试租户上下文管理器"""
        # 使用上下文管理器
        with TenantContext(self.tenant):
            self.assertEqual(get_current_tenant(), self.tenant)
        
        # 退出上下文后应该清除
        self.assertIsNone(get_current_tenant())
    
    def test_nested_tenant_context(self):
        """测试嵌套租户上下文"""
        tenant2 = Tenant.objects.create(
            name='租户2',
            schema_name='tenant2'
        )
        
        with TenantContext(self.tenant):
            self.assertEqual(get_current_tenant(), self.tenant)
            
            with TenantContext(tenant2):
                self.assertEqual(get_current_tenant(), tenant2)
            
            # 应该恢复到外层租户
            self.assertEqual(get_current_tenant(), self.tenant)
    
    def test_tenant_cache_key(self):
        """测试租户缓存键生成"""
        with TenantContext(self.tenant):
            cache_key = get_tenant_cache_key('test_key')
            expected_key = f"tenant_{self.tenant.id}:test_key"
            self.assertEqual(cache_key, expected_key)
    
    def test_create_default_permissions(self):
        """测试创建默认权限"""
        # 清除现有权限
        Permission.objects.all().delete()
        
        permissions = create_default_permissions()
        
        self.assertGreater(len(permissions), 0)
        
        # 验证一些关键权限是否创建
        self.assertTrue(Permission.objects.filter(codename='user.view_users').exists())
        self.assertTrue(Permission.objects.filter(codename='trading.create_order').exists())
        self.assertTrue(Permission.objects.filter(codename='strategy.run_backtest').exists())
    
    def test_create_default_roles(self):
        """测试创建默认角色"""
        # 先创建默认权限
        create_default_permissions()
        
        roles = create_default_roles(self.tenant)
        
        self.assertGreater(len(roles), 0)
        
        # 验证默认角色是否创建
        with TenantContext(self.tenant):
            self.assertTrue(Role.objects.filter(name='超级管理员').exists())
            self.assertTrue(Role.objects.filter(name='交易员').exists())
            self.assertTrue(Role.objects.filter(name='策略开发者').exists())
            self.assertTrue(Role.objects.filter(name='观察者').exists())


class TenantMiddlewareTest(TestCase):
    """租户中间件测试"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(lambda request: Mock())
        
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant',
            domain='test.example.com'
        )
        
        self.user = User.objects.create(
            username='testuser',
            tenant=self.tenant,
            email='test@example.com'
        )
    
    def test_tenant_from_header(self):
        """测试从HTTP头部获取租户"""
        request = self.factory.get('/', HTTP_X_TENANT_ID=str(self.tenant.id))
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # 没有错误
        self.assertEqual(request.tenant, self.tenant)
    
    def test_tenant_from_domain(self):
        """测试从域名获取租户"""
        request = self.factory.get('/', HTTP_HOST='test.example.com')
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # 没有错误
        self.assertEqual(request.tenant, self.tenant)
    
    def test_tenant_from_user(self):
        """测试从用户获取租户"""
        request = self.factory.get('/')
        request.user = self.user
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # 没有错误
        self.assertEqual(request.tenant, self.tenant)
    
    def test_inactive_tenant(self):
        """测试非激活租户"""
        self.tenant.is_active = False
        self.tenant.save()
        
        request = self.factory.get('/', HTTP_X_TENANT_ID=str(self.tenant.id))
        
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
    
    def test_expired_subscription(self):
        """测试过期订阅"""
        self.tenant.subscription_expires_at = timezone.now() - timezone.timedelta(days=1)
        self.tenant.save()
        
        request = self.factory.get('/', HTTP_X_TENANT_ID=str(self.tenant.id))
        
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
    
    def test_admin_path_skip(self):
        """测试管理员路径跳过租户检查"""
        request = self.factory.get('/admin/users/')
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # 应该跳过
        self.assertFalse(hasattr(request, 'tenant'))
    
    def test_api_without_tenant(self):
        """测试API请求缺少租户上下文"""
        request = self.factory.get('/api/users/')
        
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)


class TenantAccessControlMiddlewareTest(TestCase):
    """租户访问控制中间件测试"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantAccessControlMiddleware(lambda request: Mock())
        
        self.tenant1 = Tenant.objects.create(
            name='租户1',
            schema_name='tenant1'
        )
        
        self.tenant2 = Tenant.objects.create(
            name='租户2',
            schema_name='tenant2'
        )
        
        self.user1 = User.objects.create(
            username='user1',
            tenant=self.tenant1,
            email='user1@example.com'
        )
        
        self.user2 = User.objects.create(
            username='user2',
            tenant=self.tenant2,
            email='user2@example.com'
        )
    
    def test_same_tenant_access(self):
        """测试同租户访问"""
        request = self.factory.get('/api/users/')
        request.user = self.user1
        request.tenant = self.tenant1
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # 应该允许访问
    
    def test_cross_tenant_access_denied(self):
        """测试跨租户访问被拒绝"""
        request = self.factory.get('/api/users/')
        request.user = self.user1
        request.tenant = self.tenant2  # 不同的租户
        
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
    
    def test_superuser_access(self):
        """测试超级用户访问"""
        self.user1.is_superuser = True
        self.user1.save()
        
        request = self.factory.get('/api/users/')
        request.user = self.user1
        request.tenant = self.tenant2  # 不同的租户
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # 超级用户应该可以访问
    
    def test_skip_paths(self):
        """测试跳过的路径"""
        skip_paths = ['/admin/', '/api/auth/login/', '/health/']
        
        for path in skip_paths:
            request = self.factory.get(path)
            request.user = self.user1
            request.tenant = self.tenant2
            
            response = self.middleware.process_request(request)
            
            self.assertIsNone(response, f"路径 {path} 应该被跳过")


class MenuModelTest(TestCase):
    """菜单模型测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        self.permission = Permission.objects.create(
            name='查看用户',
            codename='user.view_users',
            category='user'
        )
        
        self.user = User.objects.create(
            username='testuser',
            tenant=self.tenant,
            email='test@example.com'
        )
    
    def test_create_menu(self):
        """测试创建菜单"""
        with TenantContext(self.tenant):
            menu = Menu.objects.create(
                name='user_management',
                title='用户管理',
                icon='user',
                path='/users',
                tenant=self.tenant
            )
            
            self.assertEqual(menu.name, 'user_management')
            self.assertEqual(menu.title, '用户管理')
            self.assertEqual(menu.tenant, self.tenant)
    
    def test_menu_hierarchy(self):
        """测试菜单层级"""
        with TenantContext(self.tenant):
            parent_menu = Menu.objects.create(
                name='system',
                title='系统管理',
                tenant=self.tenant
            )
            
            child_menu = Menu.objects.create(
                name='users',
                title='用户管理',
                parent=parent_menu,
                tenant=self.tenant
            )
            
            self.assertEqual(child_menu.parent, parent_menu)
            self.assertIn(child_menu, parent_menu.get_children())
    
    def test_menu_permission_check(self):
        """测试菜单权限检查"""
        with TenantContext(self.tenant):
            menu = Menu.objects.create(
                name='users',
                title='用户管理',
                tenant=self.tenant
            )
            menu.required_permissions.add(self.permission)
            
            # 用户没有权限，应该返回False
            self.assertFalse(menu.has_permission(self.user))
            
            # 给用户添加权限后应该返回True
            # 这里需要实现用户权限系统后才能完整测试