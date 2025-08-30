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
        """
        创建菜单数据 - 重新设计的二级菜单结构
        
        本方法为指定租户创建完整的菜单体系，包括：
        - 6个一级菜单：仪表盘、账户管理、交易中心、策略管理、数据分析、系统设置
        - 每个一级菜单下包含相应的二级菜单项
        - 菜单结构遵循量化交易平台的业务逻辑
        
        Args:
            tenant: 租户对象，用于多租户数据隔离
        """
        
        # 清除现有菜单数据，确保重新初始化时的数据一致性
        Menu.objects.filter(tenant=tenant).delete()
        
        # ==================== 一级菜单创建 ====================
        # 按照业务重要性和使用频率排序
        
        # 1. 仪表盘
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
        
        # 2. 账户管理
        account_management = Menu.objects.create(
            tenant=tenant,
            name='account_management',
            title='账户管理',
            icon='fas fa-user-cog',
            path='/account',
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        # 3. 交易中心
        trading_center = Menu.objects.create(
            tenant=tenant,
            name='trading_center',
            title='交易中心',
            icon='fas fa-chart-line',
            path='/trading',
            menu_type='menu',
            sort_order=3,
            is_visible=True,
            is_enabled=True
        )
        
        # 4. 策略管理
        strategy_management = Menu.objects.create(
            tenant=tenant,
            name='strategy_management',
            title='策略管理',
            icon='fas fa-brain',
            path='/strategy',
            menu_type='menu',
            sort_order=4,
            is_visible=True,
            is_enabled=True
        )
        
        # 5. 数据分析
        data_analysis = Menu.objects.create(
            tenant=tenant,
            name='data_analysis',
            title='数据分析',
            icon='fas fa-chart-bar',
            path='/analysis',
            menu_type='menu',
            sort_order=5,
            is_visible=True,
            is_enabled=True
        )
        
        # 6. 系统设置
        system_settings = Menu.objects.create(
            tenant=tenant,
            name='system_settings',
            title='系统设置',
            icon='fas fa-cogs',
            path='/system',
            menu_type='menu',
            sort_order=6,
            is_visible=True,
            is_enabled=True
        )
        
        # ==================== 二级菜单创建 ====================
        # 为每个一级菜单创建对应的功能子菜单
        
        # 账户管理子菜单 - 用户、角色、交易账户管理
        Menu.objects.create(
            tenant=tenant,
            name='user_list',
            title='用户管理',
            icon='fas fa-users',
            path='/account/users',
            component='UserManagement/index',
            parent=account_management,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='role_management',
            title='角色权限',
            icon='fas fa-user-shield',
            path='/account/roles',
            component='UserManagement/RoleManagement',
            parent=account_management,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='exchange_accounts',
            title='交易账户',
            icon='fas fa-wallet',
            path='/account/exchanges',
            component='ExchangeAccount/index',
            parent=account_management,
            menu_type='menu',
            sort_order=3,
            is_visible=True,
            is_enabled=True
        )
        
        # 交易中心子菜单 - 现货交易、订单管理、持仓管理、交易历史
        Menu.objects.create(
            tenant=tenant,
            name='spot_trading',
            title='现货交易',
            icon='fas fa-coins',
            path='/trading/spot',
            component='Trading/SpotTrading',
            parent=trading_center,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='order_management',
            title='订单管理',
            icon='fas fa-list-alt',
            path='/trading/orders',
            component='Trading/OrderManagement',
            parent=trading_center,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='position_management',
            title='持仓管理',
            icon='fas fa-briefcase',
            path='/trading/positions',
            component='Trading/PositionManagement',
            parent=trading_center,
            menu_type='menu',
            sort_order=3,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='trade_history',
            title='交易历史',
            icon='fas fa-history',
            path='/trading/history',
            component='Trading/TradeHistory',
            parent=trading_center,
            menu_type='menu',
            sort_order=4,
            is_visible=True,
            is_enabled=True
        )
        
        # 策略管理子菜单 - 策略列表、回测、监控、风险控制
        Menu.objects.create(
            tenant=tenant,
            name='strategy_list',
            title='策略列表',
            icon='fas fa-list',
            path='/strategy/list',
            component='Strategy/StrategyList',
            parent=strategy_management,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='strategy_backtest',
            title='策略回测',
            icon='fas fa-flask',
            path='/strategy/backtest',
            component='Strategy/Backtest',
            parent=strategy_management,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='strategy_monitor',
            title='策略监控',
            icon='fas fa-eye',
            path='/strategy/monitor',
            component='Strategy/Monitor',
            parent=strategy_management,
            menu_type='menu',
            sort_order=3,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='risk_control',
            title='风险控制',
            icon='fas fa-shield-alt',
            path='/strategy/risk',
            component='Strategy/RiskControl',
            parent=strategy_management,
            menu_type='menu',
            sort_order=4,
            is_visible=True,
            is_enabled=True
        )
        
        # 数据分析子菜单 - 市场行情、收益分析、风险分析、报表中心
        Menu.objects.create(
            tenant=tenant,
            name='market_data',
            title='市场行情',
            icon='fas fa-chart-area',
            path='/analysis/market',
            component='Analysis/MarketData',
            parent=data_analysis,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='performance_analysis',
            title='收益分析',
            icon='fas fa-chart-pie',
            path='/analysis/performance',
            component='Analysis/Performance',
            parent=data_analysis,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='risk_analysis',
            title='风险分析',
            icon='fas fa-exclamation-triangle',
            path='/analysis/risk',
            component='Analysis/RiskAnalysis',
            parent=data_analysis,
            menu_type='menu',
            sort_order=3,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='reports',
            title='报表中心',
            icon='fas fa-file-alt',
            path='/analysis/reports',
            component='Analysis/Reports',
            parent=data_analysis,
            menu_type='menu',
            sort_order=4,
            is_visible=True,
            is_enabled=True
        )
        
        # 系统设置子菜单 - 菜单管理、系统监控、数据库管理、日志、配置
        Menu.objects.create(
            tenant=tenant,
            name='menu_management',
            title='菜单管理',
            icon='fas fa-bars',
            path='/system/menus',
            component='MenuManagement/index',
            parent=system_settings,
            menu_type='menu',
            sort_order=1,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='system_monitor',
            title='系统监控',
            icon='fas fa-desktop',
            path='/system/monitor',
            component='System/Monitor',
            parent=system_settings,
            menu_type='menu',
            sort_order=2,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='database_management',
            title='数据库管理',
            icon='fas fa-database',
            path='/system/database',
            component='Database/index',
            parent=system_settings,
            menu_type='menu',
            sort_order=3,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='system_logs',
            title='系统日志',
            icon='fas fa-file-text',
            path='/system/logs',
            component='System/Logs',
            parent=system_settings,
            menu_type='menu',
            sort_order=4,
            is_visible=True,
            is_enabled=True
        )
        
        Menu.objects.create(
            tenant=tenant,
            name='system_config',
            title='系统配置',
            icon='fas fa-sliders-h',
            path='/system/config',
            component='System/Config',
            parent=system_settings,
            menu_type='menu',
            sort_order=5,
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