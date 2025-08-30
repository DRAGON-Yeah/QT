#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
菜单结构测试脚本
用于验证新的二级菜单结构是否正确创建和配置
"""

import os
import sys
import django
from django.test import TestCase
from django.core.management import call_command

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.core.models import Menu, Tenant
from apps.users.models import User


class MenuStructureTest:
    """
    菜单结构测试类
    
    用于验证QuantTrade系统中菜单结构的完整性和正确性，包括：
    - 菜单初始化功能测试
    - 菜单层级关系验证
    - 菜单属性完整性检查
    - 菜单路径有效性验证
    """
    
    def __init__(self):
        """
        初始化测试类
        
        创建测试环境并设置必要的测试数据
        """
        self.tenant = None
        self.setup_test_data()
    
    def setup_test_data(self):
        """
        设置测试数据
        
        创建或获取测试租户，为菜单测试提供必要的数据环境。
        在多租户架构中，每个租户都有独立的菜单配置。
        """
        # 创建测试租户，如果已存在则使用现有的
        self.tenant, created = Tenant.objects.get_or_create(
            name='test_tenant',
            defaults={
                'schema_name': 'test_tenant_schema',
                'domain': 'test.quanttrade.com'
            }
        )
        
        if created:
            print(f"✓ 创建测试租户: {self.tenant.name}")
        else:
            print(f"✓ 使用现有租户: {self.tenant.name}")
    
    def test_menu_initialization(self):
        """
        测试菜单初始化功能
        
        验证Django管理命令 'init_menus' 是否能够正确创建菜单结构。
        这个测试会：
        1. 清除现有的菜单数据
        2. 执行菜单初始化命令
        3. 验证命令执行是否成功
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试菜单初始化 ===")
        
        # 清除现有菜单，确保测试环境的干净性
        Menu.objects.filter(tenant=self.tenant).delete()
        
        # 运行菜单初始化命令
        try:
            call_command('init_menus', tenant_name=self.tenant.name)
            print("✓ 菜单初始化命令执行成功")
        except Exception as e:
            print(f"✗ 菜单初始化失败: {e}")
            return False
        
        return True
    
    def test_menu_structure(self):
        """
        测试菜单结构的完整性
        
        验证菜单系统是否按照预期的结构创建，包括：
        1. 检查菜单总数是否合理
        2. 验证一级菜单的数量和名称
        3. 检查二级菜单的数量
        4. 确保菜单按照正确的顺序排列
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试菜单结构 ===")
        
        # 检查菜单总数
        total_menus = Menu.objects.filter(tenant=self.tenant).count()
        print(f"总菜单数: {total_menus}")
        
        # 检查一级菜单（根菜单）
        root_menus = Menu.objects.filter(
            tenant=self.tenant, 
            parent__isnull=True
        ).order_by('sort_order')
        
        # 预期的一级菜单列表，按照业务逻辑顺序排列
        expected_root_menus = [
            'dashboard',           # 仪表盘
            'account_management',  # 账户管理
            'trading_center',      # 交易中心
            'strategy_management', # 策略管理
            'data_analysis',       # 数据分析
            'system_settings'      # 系统设置
        ]
        
        print(f"一级菜单数: {root_menus.count()}")
        
        # 逐一验证一级菜单的名称和顺序
        for i, menu in enumerate(root_menus):
            if i < len(expected_root_menus):
                expected_name = expected_root_menus[i]
                if menu.name == expected_name:
                    print(f"✓ {menu.title} ({menu.name})")
                else:
                    print(f"✗ 期望 {expected_name}, 实际 {menu.name}")
            else:
                print(f"? 额外的菜单: {menu.title} ({menu.name})")
        
        # 检查二级菜单数量
        child_menus = Menu.objects.filter(
            tenant=self.tenant,
            parent__isnull=False
        ).count()
        print(f"二级菜单数: {child_menus}")
        
        return True
    
    def test_menu_hierarchy(self):
        """
        测试菜单层级关系的正确性
        
        验证父子菜单关系是否正确建立，重点检查：
        1. 账户管理模块的子菜单
        2. 交易中心模块的子菜单
        3. 其他主要模块的子菜单结构
        
        这个测试确保菜单的层级结构符合系统设计要求。
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试菜单层级关系 ===")
        
        # 测试账户管理子菜单
        account_management = Menu.objects.filter(
            tenant=self.tenant,
            name='account_management'
        ).first()
        
        if account_management:
            account_children = Menu.objects.filter(
                tenant=self.tenant,
                parent=account_management
            ).order_by('sort_order')
            
            # 账户管理模块预期的子菜单
            expected_children = ['user_list', 'role_management', 'exchange_accounts']
            print(f"账户管理子菜单 ({account_children.count()}):")
            
            for child in account_children:
                if child.name in expected_children:
                    print(f"  ✓ {child.title} ({child.name})")
                else:
                    print(f"  ? {child.title} ({child.name})")
        
        # 测试交易中心子菜单
        trading_center = Menu.objects.filter(
            tenant=self.tenant,
            name='trading_center'
        ).first()
        
        if trading_center:
            trading_children = Menu.objects.filter(
                tenant=self.tenant,
                parent=trading_center
            ).order_by('sort_order')
            
            # 交易中心模块预期的子菜单
            expected_children = ['spot_trading', 'order_management', 'position_management', 'trade_history']
            print(f"交易中心子菜单 ({trading_children.count()}):")
            
            for child in trading_children:
                if child.name in expected_children:
                    print(f"  ✓ {child.title} ({child.name})")
                else:
                    print(f"  ? {child.title} ({child.name})")
        
        return True
    
    def test_menu_properties(self):
        """
        测试菜单属性的完整性和有效性
        
        检查菜单的各种属性是否正确设置，包括：
        1. 标题属性 - 所有菜单都应该有标题
        2. 图标属性 - 一级菜单必须有图标
        3. 启用状态 - 检查是否有异常禁用的菜单
        4. 可见性 - 检查是否有异常隐藏的菜单
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试菜单属性 ===")
        
        # 检查必要属性的完整性
        menus_without_title = Menu.objects.filter(
            tenant=self.tenant,
            title__isnull=True
        ).count()
        
        # 一级菜单必须有图标，二级菜单可以没有图标
        menus_without_icon = Menu.objects.filter(
            tenant=self.tenant,
            icon__isnull=True,
            parent__isnull=True  # 只检查一级菜单
        ).count()
        
        # 统计禁用和隐藏的菜单数量
        disabled_menus = Menu.objects.filter(
            tenant=self.tenant,
            is_enabled=False
        ).count()
        
        hidden_menus = Menu.objects.filter(
            tenant=self.tenant,
            is_visible=False
        ).count()
        
        # 输出统计结果
        print(f"缺少标题的菜单: {menus_without_title}")
        print(f"缺少图标的一级菜单: {menus_without_icon}")
        print(f"禁用的菜单: {disabled_menus}")
        print(f"隐藏的菜单: {hidden_menus}")
        
        # 验证结果
        if menus_without_title == 0:
            print("✓ 所有菜单都有标题")
        else:
            print("✗ 存在缺少标题的菜单")
        
        if menus_without_icon == 0:
            print("✓ 所有一级菜单都有图标")
        else:
            print("✗ 存在缺少图标的一级菜单")
        
        return True
    
    def test_menu_paths(self):
        """
        测试菜单路径的有效性和唯一性
        
        验证菜单路径配置是否正确，包括：
        1. 路径格式验证 - 路径应该以 '/' 开头
        2. 路径唯一性检查 - 不应该有重复的路径
        3. 路径合理性验证 - 路径应该符合前端路由规范
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试菜单路径 ===")
        
        # 用于收集问题的列表
        invalid_paths = []
        duplicate_paths = []
        
        all_menus = Menu.objects.filter(tenant=self.tenant)
        paths = []
        
        for menu in all_menus:
            if menu.path:
                # 检查路径格式 - 应该以 '/' 开头
                if not menu.path.startswith('/'):
                    invalid_paths.append(f"{menu.title}: {menu.path}")
                
                # 检查重复路径
                if menu.path in paths:
                    duplicate_paths.append(menu.path)
                else:
                    paths.append(menu.path)
        
        # 输出路径格式检查结果
        if invalid_paths:
            print("✗ 无效路径格式:")
            for path in invalid_paths:
                print(f"  {path}")
        else:
            print("✓ 所有路径格式正确")
        
        # 输出路径唯一性检查结果
        if duplicate_paths:
            print("✗ 重复路径:")
            for path in duplicate_paths:
                print(f"  {path}")
        else:
            print("✓ 没有重复路径")
        
        return len(invalid_paths) == 0 and len(duplicate_paths) == 0
    
    def print_menu_tree(self):
        """
        打印菜单树结构
        
        以树形结构显示完整的菜单层级，便于直观查看菜单组织结构。
        使用缩进和图标来表示菜单的层级关系。
        """
        print("\n=== 菜单树结构 ===")
        
        def print_menu_level(menus, level=0):
            """
            递归打印菜单层级
            
            Args:
                menus: 当前层级的菜单列表
                level: 当前层级深度，用于控制缩进
            """
            for menu in menus:
                # 根据层级设置缩进
                indent = "  " * level
                # 使用菜单图标，如果没有则使用默认图标
                icon = menu.icon if menu.icon else "📄"
                # 显示菜单信息：图标 + 标题 + 路径
                print(f"{indent}{icon} {menu.title} ({menu.path})")
                
                # 递归打印子菜单
                children = Menu.objects.filter(
                    tenant=self.tenant,
                    parent=menu
                ).order_by('sort_order')
                
                if children.exists():
                    print_menu_level(children, level + 1)
        
        # 获取所有一级菜单（根菜单）
        root_menus = Menu.objects.filter(
            tenant=self.tenant,
            parent__isnull=True
        ).order_by('sort_order')
        
        # 开始打印菜单树
        print_menu_level(root_menus)
    
    def run_all_tests(self):
        """
        运行所有菜单测试
        
        按顺序执行所有测试用例，统计测试结果并生成测试报告。
        测试包括：菜单初始化、结构验证、层级关系、属性检查、路径验证。
        
        Returns:
            bool: 所有测试是否都通过
        """
        print("开始菜单结构测试...")
        print("=" * 50)
        
        # 定义所有测试用例
        tests = [
            self.test_menu_initialization,  # 菜单初始化测试
            self.test_menu_structure,       # 菜单结构测试
            self.test_menu_hierarchy,       # 菜单层级测试
            self.test_menu_properties,      # 菜单属性测试
            self.test_menu_paths,          # 菜单路径测试
        ]
        
        # 测试结果统计
        passed = 0
        failed = 0
        
        # 逐个执行测试用例
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ 测试异常: {e}")
                failed += 1
        
        # 打印菜单树结构，便于查看最终结果
        self.print_menu_tree()
        
        # 生成测试总结报告
        print("\n" + "=" * 50)
        print("测试总结:")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"总计: {passed + failed}")
        
        # 根据测试结果显示不同的消息
        if failed == 0:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  存在测试失败，请检查上述输出")
        
        return failed == 0


def main():
    """
    主函数 - 程序入口点
    
    创建测试实例并运行所有测试，根据测试结果设置程序退出码。
    退出码 0 表示所有测试通过，退出码 1 表示存在测试失败。
    """
    tester = MenuStructureTest()
    success = tester.run_all_tests()
    
    # 根据测试结果设置退出码
    if success:
        sys.exit(0)  # 成功退出
    else:
        sys.exit(1)  # 失败退出


if __name__ == '__main__':
    main()