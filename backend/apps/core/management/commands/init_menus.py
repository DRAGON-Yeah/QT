# -*- coding: utf-8 -*-
"""
初始化菜单数据的管理命令
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Tenant, Menu


class Command(BaseCommand):
    help = '初始化系统菜单数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='default',
            help='租户名称'
        )

    def handle(self, *args, **options):
        tenant_name = options['tenant_name']
        
        try:
            tenant = Tenant.objects.get(name=tenant_name)
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'租户 "{tenant_name}" 不存在')
            )
            return

        self.stdout.write(f'为租户 "{tenant_name}" 初始化菜单数据...')
        
        with transaction.atomic():
            self.create_menus(tenant)
        
        self.stdout.write(
            self.style.SUCCESS('菜单数据初始化完成！')
        )

    def create_menus(self, tenant):
        """创建菜单数据"""
        
        # 清除现有菜单
        Menu.objects.filter(tenant=tenant).delete()
        
        # 创建主菜单
        dashboard = Menu.objects.create(
            tenant=tenant,
            name='dashboard',
            title='仪表盘',
            icon='fas fa-tachometer-alt',
            path='/dashboard',
            component='Dashboard/index',
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True,
            meta_info={'keepAlive': True}
        )
        
        # 用户管理
        user_management = Menu.objects.create(
            tenant=tenant,
            name='user_management',
            title='用户管理',
            icon='fas fa-users',
            path='/users',
            component='UserManagement/index',
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        # 用户管理子菜单
        Menu.objects.create(
            tenant=tenant,
            name='user_list',
            title='用户列表',
            icon='fas fa-user',
            path='/users/list',
            component='UserManagement/UserList',
            parent=user_management,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='role_management',
            title='角色管理',
            icon='fas fa-user-tag',
            path='/users/roles',
            component='UserManagement/RoleManagement',
            parent=user_management,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        # 菜单管理
        menu_management = Menu.objects.create(
            tenant=tenant,
            name='menu_management',
            title='菜单管理',
            icon='fas fa-bars',
            path='/menus',
            component='MenuManagement/index',
            menu_type='menu',
            sort_order=3,
            is_visible=True,
            is_enabled=True
        )
        
        # 交易管理
        trading = Menu.objects.create(
            tenant=tenant,
            name='trading',
            title='交易管理',
            icon='fas fa-exchange-alt',
            path='/trading',
            menu_type='menu',
            sort_order=4,
            is_visible=True,
            is_enabled=True
        )
        
        # 交易管理子菜单
        Menu.objects.create(
            tenant=tenant,
            name='exchanges',
            title='交易所管理',
            icon='fas fa-building',
            path='/trading/exchanges',
            component='Exchanges/index',
            parent=trading,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='orders',
            title='订单管理',
            icon='fas fa-list-alt',
            path='/trading/orders',
            component='Trading/index',
            parent=trading,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        # 策略管理
        strategies = Menu.objects.create(
            tenant=tenant,
            name='strategies',
            title='策略管理',
            icon='fas fa-chart-line',
            path='/strategies',
            component='Strategies/index',
            menu_type='menu',
            sort_order=5,
            is_visible=True,
            is_enabled=True
        )
        
        # 市场数据
        market = Menu.objects.create(
            tenant=tenant,
            name='market',
            title='市场数据',
            icon='fas fa-chart-bar',
            path='/market',
            component='Market/index',
            menu_type='menu',
            sort_order=6,
            is_visible=True,
            is_enabled=True
        )
        
        # 风险控制
        risk = Menu.objects.create(
            tenant=tenant,
            name='risk',
            title='风险控制',
            icon='fas fa-shield-alt',
            path='/risk',
            component='Risk/index',
            menu_type='menu',
            sort_order=7,
            is_visible=True,
            is_enabled=True
        )
        
        # 系统管理
        system = Menu.objects.create(
            tenant=tenant,
            name='system',
            title='系统管理',
            icon='fas fa-cogs',
            path='/system',
            menu_type='menu',
            sort_order=8,
            is_visible=True,
            is_enabled=True
        )
        
        # 系统管理子菜单
        Menu.objects.create(
            tenant=tenant,
            name='monitoring',
            title='系统监控',
            icon='fas fa-desktop',
            path='/system/monitoring',
            component='System/index',
            parent=system,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='database',
            title='数据库管理',
            icon='fas fa-database',
            path='/system/database',
            component='Database/index',
            parent=system,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        self.stdout.write('菜单数据创建完成')
        
        # 显示创建的菜单统计
        total_menus = Menu.objects.filter(tenant=tenant).count()
        root_menus = Menu.objects.filter(tenant=tenant, parent__isnull=True).count()
        child_menus = Menu.objects.filter(tenant=tenant, parent__isnull=False).count()
        
        self.stdout.write(f'总菜单数: {total_menus}')
        self.stdout.write(f'根菜单数: {root_menus}')
        self.stdout.write(f'子菜单数: {child_menus}')