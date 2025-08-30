"""
核心模块测试
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Tenant, Permission, Role, Menu, TenantModel
from .middleware import TenantMiddleware
from .utils import (
    TenantContext, get_current_tenant, set_current_tenant, clear_current_tenant,
    create_default_permissions, create_default_roles
)

User = get_user_model()


class TenantModelTest(TestCase):
    """租户模型测试"""
    
    def test_create_tenant(self):
        """测试创建租户"""
        tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        self.assertEqual(tenant.name, '测试租户')
        self.assertEqual(tenant.schema_name, 'test_tenant')
        self.assertTrue(tenant.is_active)
        self.assertEqual(tenant.max_users, 100)
    
    def test_tenant_validation(self):
        """测试租户验证"""
        # 测试无效的schema_name
        with self.assertRaises(ValidationError):
            tenant = Tenant(
                name='测试租户',
                schema_name='invalid-schema-name'  # 包含连字符，无效
            )
            tenant.full_clean()
    
    def test_tenant_user_limit(self):
        """测试租户用户限制"""
        tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant',
            max_users=2
        )
        
        # 创建用户直到达到限制
        User.objects.create(tenant=tenant, username='user1')
        User.objects.create(tenant=tenant, username='user2')
        
        # 应该达到限制
        self.assertFalse(tenant.can_add_user())
    
    def test_subscription_status(self):
        """测试订阅状态"""
        from django.utils import timezone
        from datetime import timedelta
        
        tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        # 没有设置过期时间，应该是有效的
        self.assertTrue(tenant.is_subscription_active())
        
        # 设置未来的过期时间
        tenant.subscription_expires_at = timezone.now() + timedelta(days=30)
        tenant.save()
        self.assertTrue(tenant.is_subscription_active())
        
        # 设置过去的过期时间
        tenant.subscription_expires_at = timezone.now() - timedelta(days=1)
        tenant.save()
        self.assertFalse(tenant.is_subscription_active())


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
    
    def test_create_default_permissions(self):
        """测试创建默认权限"""
        permissions = create_default_permissions()
        
        self.assertGreater(len(permissions), 0)
        
        # 检查是否包含预期的权限
        permission_codes = [p.codename for p in Permission.objects.all()]
        self.assertIn('user.view_users', permission_codes)
        self.assertIn('trading.create_order', permission_codes)
        self.assertIn('strategy.view_strategies', permission_codes)


class RoleModelTest(TestCase):
    """角色模型测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='测试租户',
            schema_name='test_tenant'
        )
        
        # 创建一些权限
        self.permission1 = Permission.objects.create(
            name='权限1',
            codename='perm1',
            category='system'
        )
        self.permission2 = Permission.objects.create(
            name='权限2',
            codename='perm2',
            category='system'
        )
        self.permission3 = Permission.objects.create(
            name='权限3',
            codename='perm3',
            category='system'
        )
    
    def test_create_role(self):
        """测试创建角色"""
        role = Role.objects.create(
            name='测试角色',
            tenant=self.tenant,
            description='测试角色描述'
        )
        
        self.assertEqual(role.name, '测试角色')
        self.assertEqual(role.tenant, self.tenant)
        self.assertTrue(role.is_active)
    
    def test_role_permissions(self):
        """测试角色权限"""
        role = Role.objects.create(
            name='测试角色',
            tenant=self.tenant
        )
        
        # 添加权限
        role.permissions.add(self.permission1, self.permission2)
        
        # 检查权限
        self.assertTrue(role.has_permission('perm1'))
        self.assertTrue(role.has_permission('perm2'))
        self.assertFalse(role.has_permission('perm3'))
        
        # 检查直接权限
        direct_permissions = role.get_direct_permissions()
        self.assertEqual(len(direct_permissions), 2)
    
    def test_role_inheritance(self):
        """测试角色继承"""
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
        
        # 检查继承的权限
        all_permissions = child_role.get_all_permissions()
        self.assertEqual(len(all_permissions), 2)
        self.assertIn(self.permission1, all_permissions)
        self.assertIn(self.permission2, all_permissions)
        
        # 检查继承链
        inheritance_chain = child_role.get_inheritance_chain()
        self.assertEqual(len(inheritance_chain), 2)
        self.assertEqual(inheritance_chain[0], child_role)
        self.assertEqual(inheritance_chain[1], parent_role)
    
    def test_circular_inheritance_prevention(self):
        """测试防止循环继承"""
        role1 = Role.objects.create(
            name='角色1',
            tenant=self.tenant
        )
        
        role2 = Role.objects.create(
            name='角色2',
            tenant=self.tenant,
            parent_role=role1
        )
        
        # 尝试创建循环继承
        role1.parent_role = role2
        
        with self.assertRaises(ValidationError):
            role1.full_clean()
    
    def test_create_system_roles(self):
        """测试创建系统角色"""
        # 先创建默认权限
        create_default_permissions()
        
        # 创建系统角色
        roles = Role.create_system_roles(self.tenant)
        
        self.assertGreater(len(roles), 0)
        
        # 检查是否创建了预期的角色
        role_names = [role.name for role in Role.objects.filter(tenant=self.tenant)]
        self.assertIn('超级管理员', role_names)
        self.assertIn('管理员', role_names)
        self.assertIn('交易员', role_names)
        self.assertIn('观察者', role_names)
    
    def test_role_deletion_constraints(self):
        """测试角色删除约束"""
        role = Role.objects.create(
            name='测试角色',
            tenant=self.tenant,
            role_type='system'  # 系统角色
        )
        
        # 系统角色不能删除
        can_delete, reason = role.can_be_deleted()
        self.assertFalse(can_delete)
        self.assertIn('系统预定义角色', reason)


class TenantContextTest(TestCase):
    """租户上下文测试"""
    
    def setUp(self):
        self.tenant1 = Tenant.objects.create(
            name='租户1',
            schema_name='tenant1'
        )
        self.tenant2 = Tenant.objects.create(
            name='租户2',
            schema_name='tenant2'
        )
    
    def test_tenant_context_manager(self):
        """测试租户上下文管理器"""
        # 初始状态
        self.assertIsNone(get_current_tenant())
        
        # 使用上下文管理器
        with TenantContext(self.tenant1):
            self.assertEqual(get_current_tenant(), self.tenant1)
            
            # 嵌套上下文
            with TenantContext(self.tenant2):
                self.assertEqual(get_current_tenant(), self.tenant2)
            
            # 退出嵌套后恢复
            self.assertEqual(get_current_tenant(), self.tenant1)
        
        # 退出上下文后清空
        self.assertIsNone(get_current_tenant())
    
    def test_manual_tenant_context(self):
        """测试手动设置租户上下文"""
        # 设置租户
        set_current_tenant(self.tenant1)
        self.assertEqual(get_current_tenant(), self.tenant1)
        
        # 切换租户
        set_current_tenant(self.tenant2)
        self.assertEqual(get_current_tenant(), self.tenant2)
        
        # 清除租户
        clear_current_tenant()
        self.assertIsNone(get_current_tenant())


class TenantManagerTest(TestCase):
    """租户管理器测试"""
    
    def setUp(self):
        self.tenant1 = Tenant.objects.create(
            name='租户1',
            schema_name='tenant1'
        )
        self.tenant2 = Tenant.objects.create(
            name='租户2',
            schema_name='tenant2'
        )
        
        # 创建用户
        self.user1 = User.objects.create(
            tenant=self.tenant1,
            username='user1'
        )
        self.user2 = User.objects.create(
            tenant=self.tenant2,
            username='user2'
        )
    
    def test_tenant_filtering(self):
        """测试租户过滤"""
        # 无租户上下文时，应该返回所有数据
        all_users = User.objects.all()
        self.assertEqual(all_users.count(), 2)
        
        # 在租户1上下文中，应该只返回租户1的数据
        with TenantContext(self.tenant1):
            tenant1_users = User.objects.all()
            self.assertEqual(tenant1_users.count(), 1)
            self.assertEqual(tenant1_users.first().username, 'user1')
        
        # 在租户2上下文中，应该只返回租户2的数据
        with TenantContext(self.tenant2):
            tenant2_users = User.objects.all()
            self.assertEqual(tenant2_users.count(), 1)
            self.assertEqual(tenant2_users.first().username, 'user2')
    
    def test_all_tenants_method(self):
        """测试获取所有租户数据的方法"""
        with TenantContext(self.tenant1):
            # 使用普通管理器应该只返回当前租户的数据
            filtered_users = User.objects.all()
            self.assertEqual(filtered_users.count(), 1)
            
            # 使用all_tenants方法应该返回所有数据
            all_users = User.objects.all_tenants()
            self.assertEqual(all_users.count(), 2)


class TenantMiddlewareTest(TestCase):
    """租户中间件测试"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(lambda request: None)
        
        self.tenant = Tenant.objects.create(
            name='中间件测试租户',
            schema_name='middleware_test',
            domain='test.example.com'
        )
        
        self.user = User.objects.create(
            tenant=self.tenant,
            username='testuser'
        )
    
    def test_tenant_identification_by_header(self):
        """测试通过HTTP头部识别租户"""
        request = self.factory.get('/api/test/')
        request.META['HTTP_X_TENANT_ID'] = str(self.tenant.id)
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)  # 中间件正常处理
        self.assertEqual(request.tenant, self.tenant)
    
    def test_tenant_identification_by_user(self):
        """测试通过用户识别租户"""
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)
        self.assertEqual(request.tenant, self.tenant)
    
    def test_admin_path_skip(self):
        """测试管理员路径跳过租户设置"""
        request = self.factory.get('/admin/test/')
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)
        self.assertFalse(hasattr(request, 'tenant'))
    
    def test_inactive_tenant_rejection(self):
        """测试拒绝非激活租户"""
        self.tenant.is_active = False
        self.tenant.save()
        
        request = self.factory.get('/api/test/')
        request.META['HTTP_X_TENANT_ID'] = str(self.tenant.id)
        
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)


class MenuModelTest(TestCase):
    """菜单模型测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='菜单测试租户',
            schema_name='menu_test'
        )
    
    def test_create_menu(self):
        """测试创建菜单"""
        menu = Menu.objects.create(
            tenant=self.tenant,
            name='test_menu',
            title='测试菜单',
            path='/test',
            icon='test-icon'
        )
        
        self.assertEqual(menu.name, 'test_menu')
        self.assertEqual(menu.title, '测试菜单')
        self.assertEqual(menu.level, 1)
        self.assertTrue(menu.is_visible)
    
    def test_menu_hierarchy(self):
        """测试菜单层级"""
        parent_menu = Menu.objects.create(
            tenant=self.tenant,
            name='parent_menu',
            title='父菜单',
            path='/parent'
        )
        
        child_menu = Menu.objects.create(
            tenant=self.tenant,
            name='child_menu',
            title='子菜单',
            path='/child',
            parent=parent_menu
        )
        
        # 检查层级自动计算
        self.assertEqual(parent_menu.level, 1)
        self.assertEqual(child_menu.level, 2)
        
        # 检查父子关系
        self.assertTrue(parent_menu.has_children())
        self.assertEqual(parent_menu.get_children_count(), 1)
    
    def test_menu_breadcrumb(self):
        """测试面包屑导航"""
        parent_menu = Menu.objects.create(
            tenant=self.tenant,
            name='parent',
            title='父菜单',
            path='/parent'
        )
        
        child_menu = Menu.objects.create(
            tenant=self.tenant,
            name='child',
            title='子菜单',
            path='/child',
            parent=parent_menu
        )
        
        breadcrumb = child_menu.get_breadcrumb()
        
        self.assertEqual(len(breadcrumb), 2)
        self.assertEqual(breadcrumb[0]['title'], '父菜单')
        self.assertEqual(breadcrumb[1]['title'], '子菜单')


class TenantModelBaseTest(TestCase):
    """租户模型基类测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='基类测试租户',
            schema_name='base_test'
        )
    
    def test_auto_tenant_assignment(self):
        """测试自动租户分配"""
        with TenantContext(self.tenant):
            # 创建菜单（继承自TenantModel）
            menu = Menu.objects.create(
                name='auto_tenant_menu',
                title='自动租户菜单',
                path='/auto'
            )
            
            # 应该自动分配租户
            self.assertEqual(menu.tenant, self.tenant)
    
    def test_tenant_required_error(self):
        """测试租户必需错误"""
        # 在没有租户上下文的情况下创建对象
        with self.assertRaises(ValidationError):
            menu = Menu(
                name='no_tenant_menu',
                title='无租户菜单',
                path='/no-tenant'
            )
            menu.save()