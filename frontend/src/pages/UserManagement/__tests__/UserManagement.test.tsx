/**
 * 用户管理页面测试
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import UserManagement from '../index';
import { userService } from '../../../services/userService';

// Mock userService
vi.mock('../../../services/userService');
const mockUserService = userService as any;

// Mock数据
const mockUsers = [
  {
    id: '1',
    username: 'testuser1',
    email: 'test1@example.com',
    firstName: 'Test',
    lastName: 'User1',
    phone: '13800138001',
    isActive: true,
    isTenantAdmin: false,
    tenant: {
      id: '1',
      name: '测试租户',
      schemaName: 'test_tenant',
      domain: '',
      isActive: true,
      maxUsers: 100,
      maxStrategies: 50,
      maxExchangeAccounts: 10,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    roles: [],
    roleNames: ['观察者'],
    permissions: [],
    lastLoginDisplay: '2024-01-01 10:00:00',
    dateJoined: '2024-01-01T00:00:00Z',
    language: 'zh-hans',
    timezoneName: 'Asia/Shanghai',
    failedLoginAttempts: 0,
  },
  {
    id: '2',
    username: 'admin',
    email: 'admin@example.com',
    firstName: 'Admin',
    lastName: 'User',
    phone: '13800138002',
    isActive: true,
    isTenantAdmin: true,
    tenant: {
      id: '1',
      name: '测试租户',
      schemaName: 'test_tenant',
      domain: '',
      isActive: true,
      maxUsers: 100,
      maxStrategies: 50,
      maxExchangeAccounts: 10,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    roles: [],
    roleNames: ['超级管理员'],
    permissions: [],
    lastLoginDisplay: '2024-01-01 12:00:00',
    dateJoined: '2024-01-01T00:00:00Z',
    language: 'zh-hans',
    timezoneName: 'Asia/Shanghai',
    failedLoginAttempts: 0,
  },
];

const mockRoles = [
  {
    id: 1,
    name: '超级管理员',
    description: '拥有所有权限的管理员角色',
    roleType: 'system' as const,
    isActive: true,
    permissions: [],
    userCount: 1,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: '观察者',
    description: '只能查看数据的角色',
    roleType: 'system' as const,
    isActive: true,
    permissions: [],
    userCount: 1,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

const mockStatistics = {
  totalUsers: 2,
  activeUsers: 2,
  adminUsers: 1,
  lockedUsers: 0,
  recentLogins: 2,
  roleDistribution: [
    { name: '超级管理员', userCount: 1 },
    { name: '观察者', userCount: 1 },
  ],
};

describe('UserManagement', () => {
  beforeEach(() => {
    // 重置所有mock
    vi.clearAllMocks();
    
    // 设置默认的mock返回值
    mockUserService.getUserList = vi.fn().mockResolvedValue({
      results: mockUsers,
      count: mockUsers.length,
      next: null,
      previous: null,
    });
    
    mockUserService.getRoleList = vi.fn().mockResolvedValue(mockRoles);
    mockUserService.getUserStatistics = vi.fn().mockResolvedValue(mockStatistics);
  });

  test('renders user management page', async () => {
    render(<UserManagement />);
    
    // 检查页面标题
    expect(screen.getByText('用户管理')).toBeInTheDocument();
    
    // 检查标签页
    expect(screen.getByText('用户管理')).toBeInTheDocument();
    expect(screen.getByText('角色管理')).toBeInTheDocument();
    
    // 等待数据加载
    await waitFor(() => {
      expect(mockUserService.getUserList).toHaveBeenCalled();
      expect(mockUserService.getRoleList).toHaveBeenCalled();
      expect(mockUserService.getUserStatistics).toHaveBeenCalled();
    });
  });

  test('displays user statistics', async () => {
    render(<UserManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('总用户数')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('活跃用户')).toBeInTheDocument();
      expect(screen.getByText('管理员')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });

  test('displays user list', async () => {
    render(<UserManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('testuser1')).toBeInTheDocument();
      expect(screen.getByText('admin')).toBeInTheDocument();
      expect(screen.getByText('test1@example.com')).toBeInTheDocument();
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });
  });

  test('can search users', async () => {
    render(<UserManagement />);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('搜索用户名、邮箱、姓名...')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('搜索用户名、邮箱、姓名...');
    fireEvent.change(searchInput, { target: { value: 'admin' } });
    
    await waitFor(() => {
      expect(mockUserService.getUserList).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'admin',
        })
      );
    });
  });

  test('can filter users by role', async () => {
    render(<UserManagement />);
    
    await waitFor(() => {
      const roleFilter = screen.getByDisplayValue('所有角色');
      expect(roleFilter).toBeInTheDocument();
    });
    
    const roleFilter = screen.getByDisplayValue('所有角色');
    fireEvent.change(roleFilter, { target: { value: '超级管理员' } });
    
    await waitFor(() => {
      expect(mockUserService.getUserList).toHaveBeenCalledWith(
        expect.objectContaining({
          role: '超级管理员',
        })
      );
    });
  });

  test('can create new user', async () => {
    render(<UserManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('创建用户')).toBeInTheDocument();
    });
    
    const createButton = screen.getByText('创建用户');
    fireEvent.click(createButton);
    
    // 应该显示用户表单
    await waitFor(() => {
      expect(screen.getByText('创建用户')).toBeInTheDocument();
    });
  });

  test('can edit user', async () => {
    render(<UserManagement />);
    
    await waitFor(() => {
      const editButtons = screen.getAllByText('编辑');
      expect(editButtons.length).toBeGreaterThan(0);
    });
    
    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);
    
    // 应该显示用户表单
    await waitFor(() => {
      expect(screen.getByText('编辑用户')).toBeInTheDocument();
    });
  });

  test('can toggle user status', async () => {
    mockUserService.toggleUserStatus = vi.fn().mockResolvedValue({ isActive: false });
    
    render(<UserManagement />);
    
    await waitFor(() => {
      const disableButtons = screen.getAllByText('禁用');
      expect(disableButtons.length).toBeGreaterThan(0);
    });
    
    const disableButton = screen.getAllByText('禁用')[0];
    fireEvent.click(disableButton);
    
    await waitFor(() => {
      expect(mockUserService.toggleUserStatus).toHaveBeenCalledWith('1');
    });
  });

  test('can delete user', async () => {
    mockUserService.deleteUser = vi.fn().mockResolvedValue(undefined);
    
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);
    
    render(<UserManagement />);
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByText('删除');
      expect(deleteButtons.length).toBeGreaterThan(0);
    });
    
    const deleteButton = screen.getAllByText('删除')[0];
    fireEvent.click(deleteButton);
    
    await waitFor(() => {
      expect(mockUserService.deleteUser).toHaveBeenCalledWith('1');
    });
    
    // 恢复原始的confirm函数
    window.confirm = originalConfirm;
  });

  test('can switch to role management tab', async () => {
    render(<UserManagement />);
    
    const roleTab = screen.getByText('角色管理');
    fireEvent.click(roleTab);
    
    // 应该显示角色管理内容
    await waitFor(() => {
      expect(screen.getByText('角色列表')).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    // 让getUserList返回一个永远不resolve的Promise来模拟加载状态
    mockUserService.getUserList = vi.fn().mockReturnValue(new Promise(() => {}));
    
    render(<UserManagement />);
    
    // 应该显示加载状态
    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  test('handles empty user list', async () => {
    mockUserService.getUserList = vi.fn().mockResolvedValue({
      results: [],
      count: 0,
      next: null,
      previous: null,
    });
    
    render(<UserManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('暂无用户数据')).toBeInTheDocument();
    });
  });

  test('handles API errors', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockUserService.getUserList = vi.fn().mockRejectedValue(new Error('API Error'));
    
    render(<UserManagement />);
    
    await waitFor(() => {
      expect(consoleError).toHaveBeenCalledWith('加载数据失败:', expect.any(Error));
    });
    
    consoleError.mockRestore();
  });
});

describe('UserManagement Integration', () => {
  test('user creation flow', async () => {
    mockUserService.createUser = vi.fn().mockResolvedValue({
      ...mockUsers[0],
      id: '3',
      username: 'newuser',
      email: 'newuser@example.com',
    });
    
    render(<UserManagement />);
    
    // 等待初始加载
    await waitFor(() => {
      expect(screen.getByText('创建用户')).toBeInTheDocument();
    });
    
    // 点击创建用户按钮
    const createButton = screen.getByText('创建用户');
    fireEvent.click(createButton);
    
    // 应该显示用户表单
    await waitFor(() => {
      expect(screen.getByText('创建用户')).toBeInTheDocument();
    });
    
    // 填写表单
    const usernameInput = screen.getByLabelText('用户名 *');
    const emailInput = screen.getByLabelText('邮箱 *');
    const passwordInput = screen.getByLabelText('密码 *');
    const confirmPasswordInput = screen.getByLabelText('确认密码 *');
    
    fireEvent.change(usernameInput, { target: { value: 'newuser' } });
    fireEvent.change(emailInput, { target: { value: 'newuser@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    
    // 提交表单
    const saveButton = screen.getByText('保存');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockUserService.createUser).toHaveBeenCalledWith(
        expect.objectContaining({
          username: 'newuser',
          email: 'newuser@example.com',
          password: 'password123',
          passwordConfirm: 'password123',
        })
      );
    });
  });

  test('user editing flow', async () => {
    mockUserService.updateUser = vi.fn().mockResolvedValue({
      ...mockUsers[0],
      firstName: 'Updated',
      lastName: 'Name',
    });
    
    render(<UserManagement />);
    
    // 等待初始加载
    await waitFor(() => {
      const editButtons = screen.getAllByText('编辑');
      expect(editButtons.length).toBeGreaterThan(0);
    });
    
    // 点击编辑按钮
    const editButton = screen.getAllByText('编辑')[0];
    fireEvent.click(editButton);
    
    // 应该显示用户表单
    await waitFor(() => {
      expect(screen.getByText('编辑用户')).toBeInTheDocument();
    });
    
    // 修改表单
    const firstNameInput = screen.getByLabelText('名');
    const lastNameInput = screen.getByLabelText('姓');
    
    fireEvent.change(firstNameInput, { target: { value: 'Updated' } });
    fireEvent.change(lastNameInput, { target: { value: 'Name' } });
    
    // 提交表单
    const saveButton = screen.getByText('保存');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockUserService.updateUser).toHaveBeenCalledWith(
        '1',
        expect.objectContaining({
          firstName: 'Updated',
          lastName: 'Name',
        })
      );
    });
  });
});