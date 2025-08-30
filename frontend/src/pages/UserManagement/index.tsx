/**
 * 用户管理页面
 */
import React, { useState, useEffect } from 'react';
import { User, Role, UserStatistics } from '../../types';
import { userService } from '../../services/userService';
import UserList from './components/UserList';
import UserForm from './components/UserForm';
import RoleManagement from './components/RoleManagement';
import UserStatisticsCard from './components/UserStatisticsCard';
import './style.scss';

interface UserManagementProps {}

const UserManagement: React.FC<UserManagementProps> = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'roles'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  
  // 搜索和过滤状态
  const [searchParams, setSearchParams] = useState({
    search: '',
    role: '',
    isActive: undefined as boolean | undefined,
    isAdmin: undefined as boolean | undefined,
    ordering: '-date_joined',
    page: 1,
    pageSize: 20,
  });

  // 加载数据
  useEffect(() => {
    loadData();
  }, [searchParams]);

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
      // TODO: 显示错误提示
    } finally {
      setLoading(false);
    }
  };

  // 处理搜索
  const handleSearch = (params: Partial<typeof searchParams>) => {
    setSearchParams(prev => ({
      ...prev,
      ...params,
      page: 1, // 重置到第一页
    }));
  };

  // 处理分页
  const handlePageChange = (page: number) => {
    setSearchParams(prev => ({ ...prev, page }));
  };

  // 创建用户
  const handleCreateUser = () => {
    setEditingUser(null);
    setShowUserForm(true);
  };

  // 编辑用户
  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setShowUserForm(true);
  };

  // 删除用户
  const handleDeleteUser = async (userId: string) => {
    if (!confirm('确定要删除此用户吗？')) {
      return;
    }

    try {
      await userService.deleteUser(userId);
      loadData(); // 重新加载数据
      // TODO: 显示成功提示
    } catch (error) {
      console.error('删除用户失败:', error);
      // TODO: 显示错误提示
    }
  };

  // 切换用户状态
  const handleToggleUserStatus = async (userId: string) => {
    try {
      await userService.toggleUserStatus(userId);
      loadData(); // 重新加载数据
      // TODO: 显示成功提示
    } catch (error) {
      console.error('切换用户状态失败:', error);
      // TODO: 显示错误提示
    }
  };

  // 解锁用户
  const handleUnlockUser = async (userId: string) => {
    try {
      await userService.unlockUser(userId);
      loadData(); // 重新加载数据
      // TODO: 显示成功提示
    } catch (error) {
      console.error('解锁用户失败:', error);
      // TODO: 显示错误提示
    }
  };

  // 保存用户
  const handleSaveUser = async (userData: any) => {
    try {
      if (editingUser) {
        await userService.updateUser(editingUser.id, userData);
      } else {
        await userService.createUser(userData);
      }
      
      setShowUserForm(false);
      setEditingUser(null);
      loadData(); // 重新加载数据
      // TODO: 显示成功提示
    } catch (error) {
      console.error('保存用户失败:', error);
      // TODO: 显示错误提示
      throw error; // 让表单组件处理错误
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

      {/* 统计卡片 */}
      {statistics && (
        <UserStatisticsCard statistics={statistics} />
      )}

      {/* 用户管理标签页 */}
      {activeTab === 'users' && (
        <div className="user-management__content">
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
        </div>
      )}

      {/* 角色管理标签页 */}
      {activeTab === 'roles' && (
        <div className="user-management__content">
          <RoleManagement
            roles={roles}
            onRoleChange={loadData}
          />
        </div>
      )}

      {/* 用户表单弹窗 */}
      {showUserForm && (
        <UserForm
          user={editingUser}
          roles={roles}
          onSave={handleSaveUser}
          onCancel={() => {
            setShowUserForm(false);
            setEditingUser(null);
          }}
        />
      )}
    </div>
  );
};

export default UserManagement;