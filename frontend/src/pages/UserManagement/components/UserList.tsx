/**
 * 用户列表组件
 */
import React from 'react';
import { User, Role } from '../../../types';

interface UserListProps {
  users: User[];
  roles: Role[];
  loading: boolean;
  searchParams: {
    search: string;
    role: string;
    isActive?: boolean;
    isAdmin?: boolean;
    ordering: string;
    page: number;
    pageSize: number;
  };
  onSearch: (params: any) => void;
  onPageChange: (page: number) => void;
  onCreateUser: () => void;
  onEditUser: (user: User) => void;
  onDeleteUser: (userId: string) => void;
  onToggleStatus: (userId: string) => void;
  onUnlockUser: (userId: string) => void;
}

const UserList: React.FC<UserListProps> = ({
  users,
  roles,
  loading,
  searchParams,
  onSearch,
  onPageChange,
  onCreateUser,
  onEditUser,
  onDeleteUser,
  onToggleStatus,
  onUnlockUser,
}) => {
  // 处理搜索输入
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSearch({ search: e.target.value });
  };

  // 处理角色过滤
  const handleRoleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onSearch({ role: e.target.value });
  };

  // 处理状态过滤
  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onSearch({ 
      isActive: value === '' ? undefined : value === 'true' 
    });
  };

  // 处理管理员过滤
  const handleAdminFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onSearch({ 
      isAdmin: value === '' ? undefined : value === 'true' 
    });
  };

  // 处理排序
  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onSearch({ ordering: e.target.value });
  };

  // 获取用户状态
  const getUserStatus = (user: User) => {
    if (user.lockedUntil && new Date(user.lockedUntil) > new Date()) {
      return { type: 'locked', text: '已锁定' };
    }
    if (user.isActive) {
      return { type: 'active', text: '正常' };
    }
    return { type: 'inactive', text: '已禁用' };
  };

  // 获取用户头像
  const getUserAvatar = (user: User) => {
    if (user.avatar) {
      return <img src={user.avatar} alt={user.username} className="user-list__avatar" />;
    }
    
    const initial = user.firstName 
      ? user.firstName.charAt(0).toUpperCase()
      : user.username.charAt(0).toUpperCase();
    
    return (
      <div className="user-list__avatar">
        {initial}
      </div>
    );
  };

  return (
    <div className="user-list">
      {/* 工具栏 */}
      <div className="user-list__toolbar">
        <div className="user-list__toolbar-left">
          {/* 搜索 */}
          <div className="user-list__search">
            <input
              type="text"
              placeholder="搜索用户名、邮箱、姓名..."
              value={searchParams.search}
              onChange={handleSearchChange}
            />
          </div>

          {/* 过滤器 */}
          <div className="user-list__filters">
            <select value={searchParams.role} onChange={handleRoleFilterChange}>
              <option value="">所有角色</option>
              {roles.map(role => (
                <option key={role.id} value={role.name}>
                  {role.name}
                </option>
              ))}
            </select>

            <select 
              value={searchParams.isActive === undefined ? '' : String(searchParams.isActive)} 
              onChange={handleStatusFilterChange}
            >
              <option value="">所有状态</option>
              <option value="true">正常</option>
              <option value="false">已禁用</option>
            </select>

            <select 
              value={searchParams.isAdmin === undefined ? '' : String(searchParams.isAdmin)} 
              onChange={handleAdminFilterChange}
            >
              <option value="">所有用户</option>
              <option value="true">管理员</option>
              <option value="false">普通用户</option>
            </select>

            <select value={searchParams.ordering} onChange={handleSortChange}>
              <option value="-date_joined">创建时间（新到旧）</option>
              <option value="date_joined">创建时间（旧到新）</option>
              <option value="username">用户名（A-Z）</option>
              <option value="-username">用户名（Z-A）</option>
              <option value="-last_login">最后登录</option>
            </select>
          </div>
        </div>

        <div className="user-list__toolbar-right">
          <button className="btn btn-primary" onClick={onCreateUser}>
            创建用户
          </button>
        </div>
      </div>

      {/* 用户表格 */}
      <div className="user-list__content">
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner">加载中...</div>
          </div>
        ) : (
          <table className="user-list__table">
            <thead>
              <tr>
                <th>用户</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>状态</th>
                <th>最后登录</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => {
                const status = getUserStatus(user);
                return (
                  <tr key={user.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {getUserAvatar(user)}
                        <div>
                          <div style={{ fontWeight: 500 }}>
                            {user.firstName && user.lastName 
                              ? `${user.firstName} ${user.lastName}` 
                              : user.username
                            }
                            {user.isTenantAdmin && (
                              <span style={{ 
                                marginLeft: '4px', 
                                fontSize: '12px', 
                                color: '#f5222d',
                                fontWeight: 'normal'
                              }}>
                                (管理员)
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                            @{user.username}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>{user.email}</td>
                    <td>
                      <div className="user-list__roles">
                        {user.roleNames?.map(roleName => (
                          <span key={roleName} className="user-list__roles-tag">
                            {roleName}
                          </span>
                        )) || '-'}
                      </div>
                    </td>
                    <td>
                      <span className={`user-list__status user-list__status--${status.type}`}>
                        <span className="user-list__status-dot"></span>
                        {status.text}
                      </span>
                    </td>
                    <td>
                      {user.lastLoginDisplay || '从未登录'}
                    </td>
                    <td>
                      {new Date(user.dateJoined).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="user-list__actions">
                        <button onClick={() => onEditUser(user)}>
                          编辑
                        </button>
                        
                        {status.type === 'locked' && (
                          <button 
                            className="success"
                            onClick={() => onUnlockUser(user.id)}
                          >
                            解锁
                          </button>
                        )}
                        
                        <button 
                          className={user.isActive ? 'danger' : 'success'}
                          onClick={() => onToggleStatus(user.id)}
                        >
                          {user.isActive ? '禁用' : '启用'}
                        </button>
                        
                        <button 
                          className="danger"
                          onClick={() => onDeleteUser(user.id)}
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {!loading && users.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px', 
            color: '#8c8c8c' 
          }}>
            暂无用户数据
          </div>
        )}
      </div>

      {/* 分页 */}
      {!loading && users.length > 0 && (
        <div className="user-list__pagination">
          <button 
            disabled={searchParams.page <= 1}
            onClick={() => onPageChange(searchParams.page - 1)}
          >
            上一页
          </button>
          
          <span>第 {searchParams.page} 页</span>
          
          <button 
            disabled={users.length < searchParams.pageSize}
            onClick={() => onPageChange(searchParams.page + 1)}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};

export default UserList;