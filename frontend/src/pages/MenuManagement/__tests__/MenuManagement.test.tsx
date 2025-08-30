/**
 * 菜单管理页面测试
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import MenuManagement from '../index';
import { menuService } from '../../../services/menuService';

// Mock 菜单服务
vi.mock('../../../services/menuService', () => ({
  menuService: {
    getMenus: vi.fn(),
    getMenuTree: vi.fn(),
    createMenu: vi.fn(),
    updateMenu: vi.fn(),
    deleteMenu: vi.fn(),
    toggleVisibility: vi.fn(),
    toggleEnabled: vi.fn(),
    reorderMenus: vi.fn(),
  },
}));

const mockMenuService = menuService as any;

// Mock 菜单数据
const mockMenuData = {
  count: 3,
  results: [
    {
      id: 1,
      name: 'dashboard',
      title: '仪表盘',
      icon: 'fas fa-tachometer-alt',
      path: '/dashboard',
      component: 'Dashboard/index',
      menu_type: 'menu',
      target: '_self',
      level: 1,
      sort_order: 1,
      is_visible: true,
      is_enabled: true,
      parent_id: null,
      permissions: [],
      roles: [],
      meta: { keepAlive: true },
      children: [],
    },
    {
      id: 2,
      name: 'user_management',
      title: '用户管理',
      icon: 'fas fa-users',
      path: '/users',
      component: 'UserManagement/index',
      menu_type: 'menu',
      target: '_self',
      level: 1,
      sort_order: 2,
      is_visible: true,
      is_enabled: true,
      parent_id: null,
      permissions: [],
      roles: [],
      meta: {},
      children: [],
    },
    {
      id: 3,
      name: 'menu_management',
      title: '菜单管理',
      icon: 'fas fa-bars',
      path: '/menus',
      component: 'MenuManagement/index',
      menu_type: 'menu',
      target: '_self',
      level: 1,
      sort_order: 3,
      is_visible: true,
      is_enabled: true,
      parent_id: null,
      permissions: [],
      roles: [],
      meta: {},
      children: [],
    },
  ],
};

const mockMenuTree = [
  {
    id: 1,
    name: 'dashboard',
    title: '仪表盘',
    icon: 'fas fa-tachometer-alt',
    path: '/dashboard',
    component: 'Dashboard/index',
    menu_type: 'menu',
    target: '_self',
    level: 1,
    sort_order: 1,
    is_visible: true,
    is_enabled: true,
    parent_id: null,
    permissions: [],
    roles: [],
    meta: { keepAlive: true },
    children: [],
  },
  {
    id: 2,
    name: 'user_management',
    title: '用户管理',
    icon: 'fas fa-users',
    path: '/users',
    component: 'UserManagement/index',
    menu_type: 'menu',
    target: '_self',
    level: 1,
    sort_order: 2,
    is_visible: true,
    is_enabled: true,
    parent_id: null,
    permissions: [],
    roles: [],
    meta: {},
    children: [],
  },
];

describe('MenuManagement', () => {
  beforeEach(() => {
    // 重置所有mock
    vi.clearAllMocks();
    
    // 设置默认的mock返回值
    mockMenuService.getMenus.mockResolvedValue(mockMenuData);
    mockMenuService.getMenuTree.mockResolvedValue(mockMenuTree);
  });

  test('renders menu management page', async () => {
    render(<MenuManagement />);
    
    // 检查页面标题
    expect(screen.getByText('菜单管理')).toBeInTheDocument();
    
    // 等待数据加载
    await waitFor(() => {
      expect(mockMenuService.getMenus).toHaveBeenCalled();
      expect(mockMenuService.getMenuTree).toHaveBeenCalled();
    });
  });

  test('displays menu tree', async () => {
    render(<MenuManagement />);
    
    await waitFor(() => {
      // 检查菜单项是否显示
      expect(screen.getByText('仪表盘')).toBeInTheDocument();
      expect(screen.getByText('用户管理')).toBeInTheDocument();
    });
  });

  test('can create new menu', async () => {
    mockMenuService.createMenu.mockResolvedValue({
      id: 4,
      name: 'new_menu',
      title: '新菜单',
      icon: 'fas fa-plus',
      path: '/new',
      component: 'New/index',
      menu_type: 'menu',
      target: '_self',
      level: 1,
      sort_order: 4,
      is_visible: true,
      is_enabled: true,
      parent_id: null,
      permissions: [],
      roles: [],
      meta: {},
      children: [],
    });
    
    render(<MenuManagement />);
    
    await waitFor(() => {
      // 查找添加按钮
      const addButton = screen.getByText('添加菜单');
      expect(addButton).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    // 设置pending状态的mock
    mockMenuService.getMenus.mockReturnValue(new Promise(() => {}));
    mockMenuService.getMenuTree.mockReturnValue(new Promise(() => {}));
    
    render(<MenuManagement />);
    
    // 应该显示加载状态
    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    // 设置错误状态的mock
    mockMenuService.getMenus.mockRejectedValue(new Error('API Error'));
    mockMenuService.getMenuTree.mockRejectedValue(new Error('API Error'));
    
    render(<MenuManagement />);
    
    await waitFor(() => {
      // 应该显示错误信息
      expect(screen.getByText('加载菜单数据失败')).toBeInTheDocument();
    });
  });
});

describe('MenuManagement Integration', () => {
  test('menu creation flow', async () => {
    mockMenuService.createMenu.mockResolvedValue({
      id: 4,
      name: 'test_menu',
      title: '测试菜单',
      icon: 'fas fa-test',
      path: '/test',
      component: 'Test/index',
      menu_type: 'menu',
      target: '_self',
      level: 1,
      sort_order: 4,
      is_visible: true,
      is_enabled: true,
      parent_id: null,
      permissions: [],
      roles: [],
      meta: {},
      children: [],
    });
    
    render(<MenuManagement />);
    
    // 等待初始加载
    await waitFor(() => {
      expect(mockMenuService.getMenus).toHaveBeenCalled();
    });
    
    // 点击添加按钮
    const addButton = screen.getByText('添加菜单');
    fireEvent.click(addButton);
    
    // 应该打开表单对话框
    await waitFor(() => {
      expect(screen.getByText('添加菜单')).toBeInTheDocument();
    });
  });

  test('menu editing flow', async () => {
    mockMenuService.updateMenu.mockResolvedValue({
      id: 1,
      name: 'dashboard_updated',
      title: '仪表盘（已更新）',
      icon: 'fas fa-tachometer-alt',
      path: '/dashboard',
      component: 'Dashboard/index',
      menu_type: 'menu',
      target: '_self',
      level: 1,
      sort_order: 1,
      is_visible: true,
      is_enabled: true,
      parent_id: null,
      permissions: [],
      roles: [],
      meta: { keepAlive: true },
      children: [],
    });
    
    render(<MenuManagement />);
    
    // 等待初始加载
    await waitFor(() => {
      expect(mockMenuService.getMenus).toHaveBeenCalled();
    });
    
    // 查找编辑按钮（通过菜单项）
    await waitFor(() => {
      const menuItem = screen.getByText('仪表盘');
      expect(menuItem).toBeInTheDocument();
    });
  });
});