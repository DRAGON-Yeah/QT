/**
 * 用户管理服务
 */
import { 
  User, Role, Permission, UserProfile, UserRole, LoginLog, 
  UserStatistics, RoleAssignment, ApiResponse, PaginatedResponse 
} from '../types';
import { noAutoLogoutFetch } from '../utils/request';

const API_BASE = '/api/users';

class UserService {
  /**
   * 获取用户列表
   */
  async getUserList(params: {
    search?: string;
    role?: string;
    isActive?: boolean;
    isAdmin?: boolean;
    ordering?: string;
    page?: number;
    pageSize?: number;
  } = {}): Promise<PaginatedResponse<User>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    
    const response = await noAutoLogoutFetch(`${API_BASE}/users/?${searchParams}`);
    
    if (!response.ok) {
      throw new Error('获取用户列表失败');
    }
    
    return response.json();
  }

  /**
   * 获取用户详情
   */
  async getUserDetail(userId: string): Promise<User> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/${userId}/`);
    
    if (!response.ok) {
      throw new Error('获取用户详情失败');
    }
    
    const result: ApiResponse<User> = await response.json();
    return result.data!;
  }

  /**
   * 创建用户
   */
  async createUser(userData: {
    username: string;
    email: string;
    password: string;
    passwordConfirm: string;
    firstName?: string;
    lastName?: string;
    phone?: string;
    isTenantAdmin?: boolean;
    roleIds?: number[];
    profileData?: Partial<UserProfile>;
    language?: string;
    timezoneName?: string;
  }): Promise<User> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '创建用户失败');
    }
    
    const result: ApiResponse<User> = await response.json();
    return result.data!;
  }

  /**
   * 更新用户
   */
  async updateUser(userId: string, userData: Partial<User>): Promise<User> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/${userId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '更新用户失败');
    }
    
    const result: ApiResponse<User> = await response.json();
    return result.data!;
  }

  /**
   * 删除用户
   */
  async deleteUser(userId: string): Promise<void> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/${userId}/`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '删除用户失败');
    }
  }

  /**
   * 切换用户状态
   */
  async toggleUserStatus(userId: string): Promise<{ isActive: boolean }> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/${userId}/toggle_status/`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '切换用户状态失败');
    }
    
    const result: ApiResponse<{ isActive: boolean }> = await response.json();
    return result.data!;
  }

  /**
   * 解锁用户账户
   */
  async unlockUser(userId: string): Promise<void> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/${userId}/unlock_account/`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '解锁用户失败');
    }
  }

  /**
   * 修改用户密码
   */
  async changePassword(userId: string, passwordData: {
    oldPassword?: string;
    newPassword: string;
    newPasswordConfirm: string;
    forceChange?: boolean;
  }): Promise<void> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/${userId}/change_password/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(passwordData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '修改密码失败');
    }
  }

  /**
   * 获取用户统计信息
   */
  async getUserStatistics(): Promise<UserStatistics> {
    const response = await noAutoLogoutFetch(`${API_BASE}/users/statistics/`);
    
    if (!response.ok) {
      throw new Error('获取用户统计失败');
    }
    
    const result: ApiResponse<UserStatistics> = await response.json();
    return result.data!;
  }

  /**
   * 获取角色列表
   */
  async getRoleList(): Promise<Role[]> {
    const response = await noAutoLogoutFetch(`${API_BASE}/roles/`);
    
    if (!response.ok) {
      throw new Error('获取角色列表失败');
    }
    
    const result: ApiResponse<Role[]> = await response.json();
    return result.data!;
  }

  /**
   * 获取角色详情
   */
  async getRoleDetail(roleId: number): Promise<Role> {
    const response = await noAutoLogoutFetch(`${API_BASE}/roles/${roleId}/`);
    
    if (!response.ok) {
      throw new Error('获取角色详情失败');
    }
    
    const result: ApiResponse<Role> = await response.json();
    return result.data!;
  }

  /**
   * 创建角色
   */
  async createRole(roleData: {
    name: string;
    description?: string;
    permissionIds?: number[];
  }): Promise<Role> {
    const response = await noAutoLogoutFetch(`${API_BASE}/roles/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(roleData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '创建角色失败');
    }
    
    const result: ApiResponse<Role> = await response.json();
    return result.data!;
  }

  /**
   * 更新角色
   */
  async updateRole(roleId: number, roleData: Partial<Role>): Promise<Role> {
    const response = await noAutoLogoutFetch(`${API_BASE}/roles/${roleId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(roleData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '更新角色失败');
    }
    
    const result: ApiResponse<Role> = await response.json();
    return result.data!;
  }

  /**
   * 删除角色
   */
  async deleteRole(roleId: number): Promise<void> {
    const response = await noAutoLogoutFetch(`${API_BASE}/roles/${roleId}/`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '删除角色失败');
    }
  }

  /**
   * 获取权限列表
   */
  async getPermissionList(): Promise<Record<string, Permission[]>> {
    const response = await noAutoLogoutFetch(`${API_BASE}/permissions/`);
    
    if (!response.ok) {
      throw new Error('获取权限列表失败');
    }
    
    const result: ApiResponse<Record<string, Permission[]>> = await response.json();
    return result.data!;
  }

  /**
   * 批量分配角色
   */
  async assignRoles(assignment: RoleAssignment): Promise<any> {
    const response = await noAutoLogoutFetch(`${API_BASE}/role-assignment/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(assignment),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '角色分配失败');
    }
    
    const result: ApiResponse = await response.json();
    return result.data;
  }

  /**
   * 获取登录日志
   */
  async getLoginLogs(params: {
    userId?: string;
    result?: 'success' | 'failed' | 'blocked';
    page?: number;
    pageSize?: number;
  } = {}): Promise<PaginatedResponse<LoginLog>> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    
    const url = params.userId 
      ? `${API_BASE}/login-logs/${params.userId}/?${searchParams}`
      : `${API_BASE}/login-logs/?${searchParams}`;
    
    const response = await noAutoLogoutFetch(url);
    
    if (!response.ok) {
      throw new Error('获取登录日志失败');
    }
    
    const result: ApiResponse<PaginatedResponse<LoginLog>> = await response.json();
    return result.data!;
  }
}

export const userService = new UserService();
export default userService;