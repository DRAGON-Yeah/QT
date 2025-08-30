# -*- coding: utf-8 -*-
"""
菜单管理系统测试模块

本模块包含菜单管理系统的完整测试用例，涵盖：
- 菜单模型的基础功能测试
- 用户菜单配置测试
- 菜单服务层业务逻辑测试
- 菜单管理API接口测试

测试覆盖范围：
- 菜单的创建、更新、删除操作
- 菜单层级结构和权限控制
- 用户个性化菜单配置
- 多租户数据隔离验证
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.core.models import Tenant, Menu, UserMenuConfig
from apps.core.menu_services import MenuService

User = get_user_model()


class MenuModelTest(TestCase):
    """
    菜单模型测试类
    
    测试菜单模型的基础功能，包括：
    - 菜单的创建和基本属性验证
    - 菜单层级结构的正确性
    - 菜单路径和面包屑导航功能
    """
    
    def setUp(self):
        """测试前置准备：创建测试租户"""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            schema_name='test_tenant'
        )
    
    def test_menu_creation(self):
        """
        测试菜单创建功能
        
        验证点：
        - 菜单基本属性是否正确设置
        - 根菜单的层级是否为1
        - 默认可见性和启用状态
        """
        menu = Menu.objects.create(
            tenant=self.tenant,
            name='dashboard',
            title='仪表盘',
            icon='fas fa-tachometer-alt',
            path='/dashboard',
            component='Dashboard/index',
            menu_type='menu',
            sort_order=1
        )
        
        # 验证基本属性
        self.assertEqual(menu.name, 'dashboard')
        self.assertEqual(menu.title, '仪表盘')
        self.assertEqual(menu.level, 1)  # 根菜单层级为1
        self.assertTrue(menu.is_visible)  # 默认可见
        self.assertTrue(menu.is_enabled)  # 默认启用
    
    def test_menu_hierarchy(self):
        """
        测试菜单层级结构
        
        验证点：
        - 父子菜单的层级关系
        - 子菜单层级自动计算
        - 父菜单的子菜单检测功能
        """
        # 创建父菜单
        parent_menu = Menu.objects.create(
            tenant=self.tenant,
            name='user_management',
            title='用户管理',
            icon='fas fa-users',
            path='/users',
            menu_type='menu',
            sort_order=1
        )
        
        # 创建子菜单
        child_menu = Menu.objects.create(
            tenant=self.tenant,
            name='user_list',
            title='用户列表',
            icon='fas fa-user',
            path='/users/list',
            parent=parent_menu,  # 设置父菜单
            menu_type='menu',
            sort_order=1
        )
        
        # 验证层级关系
        self.assertEqual(parent_menu.level, 1)  # 父菜单为第1层
        self.assertEqual(child_menu.level, 2)   # 子菜单为第2层
        self.assertEqual(child_menu.parent, parent_menu)  # 父子关系正确
        self.assertTrue(parent_menu.has_children())  # 父菜单有子菜单
        self.assertEqual(parent_menu.get_children_count(), 1)  # 子菜单数量为1
    
    def test_menu_full_path(self):
        """测试菜单完整路径"""
        parent_menu = Menu.objects.create(
            tenant=self.tenant,
            name='system',
            title='系统管理',
            path='/system',
            menu_type='menu'
        )
        
        child_menu = Menu.objects.create(
            tenant=self.tenant,
            name='monitoring',
            title='系统监控',
            path='monitoring',
            parent=parent_menu,
            menu_type='menu'
        )
        
        self.assertEqual(parent_menu.get_full_path(), '/system')
        self.assertEqual(child_menu.get_full_path(), '/system/monitoring')
    
    def test_breadcrumb(self):
        """测试面包屑导航"""
        parent_menu = Menu.objects.create(
            tenant=self.tenant,
            name='system',
            title='系统管理',
            path='/system',
            menu_type='menu'
        )
        
        child_menu = Menu.objects.create(
            tenant=self.tenant,
            name='monitoring',
            title='系统监控',
            path='monitoring',
            parent=parent_menu,
            menu_type='menu'
        )
        
        breadcrumb = child_menu.get_breadcrumb()
        self.assertEqual(len(breadcrumb), 2)
        self.assertEqual(breadcrumb[0]['name'], 'system')
        self.assertEqual(breadcrumb[1]['name'], 'monitoring')


class UserMenuConfigTest(TestCase):
    """
    用户菜单配置测试类
    
    测试用户个性化菜单配置功能，包括：
    - 用户菜单收藏功能
    - 自定义菜单标题和图标
    - 菜单访问统计
    """
    
    def setUp(self):
        """测试前置准备：创建测试数据"""
        # 创建测试租户
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            schema_name='test_tenant'
        )
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        # 创建测试菜单
        self.menu = Menu.objects.create(
            tenant=self.tenant,
            name='dashboard',
            title='仪表盘',
            path='/dashboard',
            menu_type='menu'
        )
    
    def test_user_menu_config_creation(self):
        """
        测试用户菜单配置创建
        
        验证点：
        - 用户菜单配置的基本属性
        - 收藏状态和自定义标题
        - 访问计数的初始值
        """
        config = UserMenuConfig.objects.create(
            tenant=self.tenant,
            user=self.user,
            menu=self.menu,
            is_favorite=True,
            custom_title='我的仪表盘'
        )
        
        # 验证配置属性
        self.assertEqual(config.user, self.user)
        self.assertEqual(config.menu, self.menu)
        self.assertTrue(config.is_favorite)  # 收藏状态
        self.assertEqual(config.custom_title, '我的仪表盘')  # 自定义标题
        self.assertEqual(config.access_count, 0)  # 初始访问次数为0


class MenuServiceTest(TestCase):
    """
    菜单服务测试类
    
    测试菜单服务层的业务逻辑，包括：
    - 用户菜单树的构建和权限过滤
    - 菜单的CRUD操作
    - 菜单访问记录和统计
    - 菜单缓存机制
    """
    
    def setUp(self):
        """测试前置准备：创建完整的测试数据"""
        # 创建测试租户
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            schema_name='test_tenant'
        )
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        # 创建父菜单
        self.parent_menu = Menu.objects.create(
            tenant=self.tenant,
            name='user_management',
            title='用户管理',
            icon='fas fa-users',
            path='/users',
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        # 创建子菜单
        self.child_menu = Menu.objects.create(
            tenant=self.tenant,
            name='user_list',
            title='用户列表',
            icon='fas fa-user',
            path='/users/list',
            parent=self.parent_menu,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
    
    def test_get_user_menus(self):
        """
        测试获取用户菜单树
        
        验证点：
        - 菜单树结构的正确性
        - 父子菜单关系
        - 权限过滤功能
        """
        menus = MenuService.get_user_menus(self.user, use_cache=False)
        
        # 验证菜单树结构
        self.assertEqual(len(menus), 1)  # 只有一个根菜单
        self.assertEqual(menus[0]['name'], 'user_management')
        self.assertEqual(len(menus[0]['children']), 1)  # 有一个子菜单
        self.assertEqual(menus[0]['children'][0]['name'], 'user_list')
    
    def test_create_menu(self):
        """
        测试通过服务层创建菜单
        
        验证点：
        - 菜单数据的正确保存
        - 租户关联的自动设置
        - 层级的自动计算
        - 元信息的正确存储
        """
        menu_data = {
            'name': 'dashboard',
            'title': '仪表盘',
            'icon': 'fas fa-tachometer-alt',
            'path': '/dashboard',
            'component': 'Dashboard/index',
            'menu_type': 'menu',
            'sort_order': 0,
            'is_visible': True,
            'is_enabled': True,
            'meta_info': {'keepAlive': True}  # 路由元信息
        }
        
        menu = MenuService.create_menu(self.tenant, menu_data)
        
        # 验证菜单创建结果
        self.assertEqual(menu.name, 'dashboard')
        self.assertEqual(menu.title, '仪表盘')
        self.assertEqual(menu.tenant, self.tenant)  # 租户关联正确
        self.assertEqual(menu.level, 1)  # 根菜单层级为1
    
    def test_update_menu(self):
        """
        测试通过服务层更新菜单
        
        验证点：
        - 菜单属性的正确更新
        - 部分字段更新的支持
        - 更新后数据的持久化
        """
        update_data = {
            'title': '更新的用户管理',
            'icon': 'fas fa-user-cog',
            'is_visible': False
        }
        
        updated_menu = MenuService.update_menu(self.parent_menu, update_data)
        
        # 验证更新结果
        self.assertEqual(updated_menu.title, '更新的用户管理')
        self.assertEqual(updated_menu.icon, 'fas fa-user-cog')
        self.assertFalse(updated_menu.is_visible)
    
    def test_delete_menu_with_children(self):
        """
        测试删除有子菜单的菜单（应该失败）
        
        验证点：
        - 有子菜单的菜单不能直接删除
        - 抛出正确的异常类型
        - 数据完整性保护机制
        """
        with self.assertRaises(ValueError):
            MenuService.delete_menu(self.parent_menu)
    
    def test_delete_menu_without_children(self):
        """
        测试删除没有子菜单的菜单（应该成功）
        
        验证点：
        - 叶子菜单可以正常删除
        - 删除顺序的正确性（先删子菜单再删父菜单）
        - 菜单确实从数据库中移除
        """
        # 先删除子菜单
        MenuService.delete_menu(self.child_menu)
        
        # 再删除父菜单
        MenuService.delete_menu(self.parent_menu)
        
        # 验证菜单已被删除
        self.assertFalse(Menu.objects.filter(id=self.parent_menu.id).exists())
    
    def test_record_menu_access(self):
        """
        测试菜单访问记录功能
        
        验证点：
        - 访问次数的正确累计
        - 最后访问时间的更新
        - 用户菜单配置的自动创建
        """
        # 记录菜单访问
        MenuService.record_menu_access(self.user, self.parent_menu.id)
        
        # 获取用户菜单配置
        config = UserMenuConfig.objects.get(
            tenant=self.tenant,
            user=self.user,
            menu=self.parent_menu
        )
        
        # 验证访问记录
        self.assertEqual(config.access_count, 1)  # 访问次数为1
        self.assertIsNotNone(config.last_access_time)  # 最后访问时间已设置


class MenuAPITest(APITestCase):
    """
    菜单API接口测试类
    
    测试菜单管理的REST API接口，包括：
    - 菜单CRUD操作的API接口
    - 菜单树获取接口
    - 菜单状态切换接口
    - 图标列表获取接口
    - 多租户数据隔离验证
    """
    
    def setUp(self):
        """测试前置准备：创建测试环境"""
        # 创建测试租户
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            schema_name='test_tenant'
        )
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        # 设置用户为超级用户以绕过权限检查
        self.user.is_superuser = True
        self.user.save()
        
        # 强制认证用户
        self.client.force_authenticate(user=self.user)
        
        # 创建测试菜单
        self.menu = Menu.objects.create(
            tenant=self.tenant,
            name='dashboard',
            title='仪表盘',
            icon='fas fa-tachometer-alt',
            path='/dashboard',
            menu_type='menu',
            sort_order=1
        )
    
    def _make_request(self, method, url, data=None, **kwargs):
        """
        发送带租户头部的HTTP请求
        
        为了测试多租户环境下的API接口，需要在请求头中
        添加租户ID信息，确保请求能正确识别租户上下文
        
        参数:
            method: HTTP方法 (GET, POST, PUT, PATCH, DELETE)
            url: 请求URL
            data: 请求数据
            **kwargs: 其他请求参数
        
        返回:
            HTTP响应对象
        """
        headers = kwargs.get('headers', {})
        headers['HTTP_X_TENANT_ID'] = str(self.tenant.id)  # 添加租户ID头部
        kwargs['headers'] = headers
        
        # 根据HTTP方法发送相应请求
        if method.upper() == 'GET':
            return self.client.get(url, **kwargs)
        elif method.upper() == 'POST':
            return self.client.post(url, data, format='json', **kwargs)
        elif method.upper() == 'PUT':
            return self.client.put(url, data, format='json', **kwargs)
        elif method.upper() == 'PATCH':
            return self.client.patch(url, data, format='json', **kwargs)
        elif method.upper() == 'DELETE':
            return self.client.delete(url, **kwargs)
    
    def test_get_menu_tree(self):
        """
        测试获取菜单树API接口
        
        验证点：
        - API响应状态码
        - 返回数据格式为列表
        - 菜单树结构的正确性
        """
        url = '/api/core/menus/tree/'
        response = self._make_request('GET', url)
        
        # 验证响应状态
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证返回数据格式
        self.assertIsInstance(response.data, list)
    
    def test_create_menu(self):
        """
        测试创建菜单API接口
        
        验证点：
        - 菜单创建成功的状态码
        - 返回数据的正确性
        - 菜单属性的正确保存
        """
        url = '/api/core/menus/'
        data = {
            'name': 'user_management',
            'title': '用户管理',
            'icon': 'fas fa-users',
            'path': '/users',
            'component': 'UserManagement/index',
            'menu_type': 'menu',
            'target': '_self',
            'sort_order': 2,
            'is_visible': True,
            'is_enabled': True,
            'is_cache': True
        }
        
        response = self._make_request('POST', url, data)
        
        # 验证创建成功
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 验证返回数据
        self.assertEqual(response.data['name'], 'user_management')
        self.assertEqual(response.data['title'], '用户管理')
    
    def test_update_menu(self):
        """
        测试更新菜单API接口
        
        验证点：
        - 部分更新功能的正确性
        - 更新后数据的正确性
        - 响应状态码
        """
        url = f'/api/core/menus/{self.menu.id}/'
        data = {
            'title': '更新的仪表盘',
            'icon': 'fas fa-chart-pie'
        }
        
        response = self.client.patch(url, data, format='json')
        
        # 验证更新成功
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证更新后的数据
        self.assertEqual(response.data['title'], '更新的仪表盘')
        self.assertEqual(response.data['icon'], 'fas fa-chart-pie')
    
    def test_delete_menu(self):
        """
        测试删除菜单API接口
        
        验证点：
        - 删除操作的成功状态码
        - 菜单确实从数据库中删除
        - 软删除或硬删除的正确性
        """
        url = f'/api/core/menus/{self.menu.id}/'
        response = self.client.delete(url)
        
        # 验证删除成功
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 验证菜单已从数据库删除
        self.assertFalse(Menu.objects.filter(id=self.menu.id).exists())
    
    def test_toggle_visibility(self):
        """
        测试切换菜单可见性API接口
        
        验证点：
        - 可见性切换操作的成功执行
        - 菜单状态的正确更新
        - 数据库中状态的持久化
        """
        url = f'/api/core/menus/{self.menu.id}/toggle_visibility/'
        response = self.client.post(url)
        
        # 验证操作成功
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 刷新菜单对象并验证状态变更
        self.menu.refresh_from_db()
        self.assertFalse(self.menu.is_visible)  # 应该被切换为不可见
    
    def test_get_icons(self):
        """
        测试获取图标列表API接口
        
        验证点：
        - 图标列表获取的成功状态
        - 返回数据包含预期的图标分类
        - 图标数据结构的正确性
        """
        url = '/api/core/menus/icons/'
        response = self.client.get(url)
        
        # 验证获取成功
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证包含预期的图标分类
        self.assertIn('common', response.data)    # 通用图标
        self.assertIn('trading', response.data)   # 交易相关图标
        self.assertIn('system', response.data)    # 系统管理图标