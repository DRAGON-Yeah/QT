/**
 * 用户管理页面
 */
import React, { useState, useEffect } from 'react';
import { Spin, message } from 'antd';
import { User, Role, UserStatistics } from '../../types';
import { userService } from '../../services/userService';
import UserList from './components/UserList';
import './style.scss';

interface UserManagementProps { }

const UserManagement: React.FC<UserManagementProps> = () => {
  // 页面状态管理
  const [activeTab, setActiveTab] = useState<'users' | 'roles'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  // 搜索和过滤参数状态
  const [searchParams, setSearchParams] = useState({
    search: '', // 搜索关键词
    role: '', // 角色过滤
    isActive: undefined as boolean | undefined, // 激活状态过滤
    isAdmin: undefined as boolean | undefined, // 管理员状态过滤
    ordering: '-date_joined', // 排序方式
    page: 1, // 当前页码
    pageSize: 20, // 每页数量
  });

  // 监听搜索参数变化，自动重新加载数据
  useEffect(() => {
    loadData();
  }, [searchParams]);

  /**
   * 加载页面数据
   */
  const loadData = async () => {
    setLoading(true);
    try {
      const [userResponse, rolesData, statsData] = await Promise.all([
        userService.getUserList(searchParams),
        userService.getRoleList(),
        userService.getUserStatistics(),
      ]);

      setUsers(userResponse.results);
      setRoles(rolesData);
      setStatistics(statsData);
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载用户数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理搜索参数变更
   * @param params 新的搜索参数
   */
  const handleSearch = (params: Partial<typeof searchParams>) => {
    setSearchParams(prev => ({
      ...prev,
      ...params,
      page: 1, // 搜索时重置到第一页
    }));
  };

  /**
   * 处理分页变更
   * @param page 目标页码
   */
  const handlePageChange = (page: number) => {
    setSearchParams(prev => ({ ...prev, page }));
  };

  /**
   * 创建新用户
   * 清空编辑状态并显示用户表单
   */
  const handleCreateUser = () => {
    setEditingUser(null);
    setShowUserForm(true);
  };

  /**
   * 编辑用户
   * @param user 要编辑的用户对象
   */
  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setShowUserForm(true);
  };

  /**
   * 删除用户
   */
  const handleDeleteUser = async (userId: string) => {
    if (!confirm('确定要删除此用户吗？')) {
      return;
    }

    try {
      await userService.deleteUser(userId);
      message.success('删除用户成功');
      loadData();
    } catch (error) {
      console.error('删除用户失败:', error);
      message.error('删除用户失败，请稍后重试');
    }
  };

  /**
   * 切换用户激活状态
   */
  const handleToggleUserStatus = async (userId: string) => {
    try {
      await userService.toggleUserStatus(userId);
      message.success('切换用户状态成功');
      loadData();
    } catch (error) {
      console.error('切换用户状态失败:', error);
      message.error('切换用户状态失败，请稍后重试');
    }
  };

  /**
   * 解锁被锁定的用户
   */
  const handleUnlockUser = async (userId: string) => {
    try {
      await userService.unlockUser(userId);
      message.success('解锁用户成功');
      loadData();
    } catch (error) {
      console.error('解锁用户失败:', error);
      message.error('解锁用户失败，请稍后重试');
    }
  };

  /**
   * 保存用户信息
   */
  const handleSaveUser = async (userData: any) => {
    try {
      if (editingUser) {
        await userService.updateUser(editingUser.id, userData);
        message.success('更新用户成功');
      } else {
        await userService.createUser(userData);
        message.success('创建用户成功');
      }

      setShowUserForm(false);
      setEditingUser(null);
      loadData();
    } catch (error) {
      console.error('保存用户失败:', error);
      message.error(editingUser ? '更新用户失败' : '创建用户失败');
      throw error;
    }
  };

  return (
    <div className="user-management">
      <div className="user-management__header">
        <h1>用户管理</h1>
        <div className="user-management__tabs">
          <button
            className={`tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            用户管理
          </button>
          <button
            className={`tab ${activeTab === 'roles' ? 'active' : ''}`}
            onClick={() => setActiveTab('roles')}
          >
            角色管理
          </button>
        </div>
      </div>

      {/* 统计信息 */}
      {statistics && (
        <div className="user-statistics">
          <div>总用户数: {statistics.totalUsers}</div>
          <div>活跃用户: {statistics.activeUsers}</div>
          <div>管理员: {statistics.adminUsers}</div>
          <div>锁定用户: {statistics.lockedUsers}</div>
        </div>
      )}

      {/* 用户管理标签页 */}
      {activeTab === 'users' && (
        <div className="user-management__content">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
              <div>加载中...</div>
            </div>
          ) : (
            <UserList
              users={users}
              roles={roles}
              loading={loading}
              searchParams={searchParams}
              onSearch={handleSearch}
              onPageChange={handlePageChange}
              onCreateUser={handleCreateUser}
              onEditUser={handleEditUser}
              onDeleteUser={handleDeleteUser}
              onToggleStatus={handleToggleUserStatus}
              onUnlockUser={handleUnlockUser}
            />
          )}
        </div>
      )}

      {/* 角色管理标签页 */}
      {activeTab === 'roles' && (
        <div className="user-management__content">
          <div>角色管理功能开发中...</div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;