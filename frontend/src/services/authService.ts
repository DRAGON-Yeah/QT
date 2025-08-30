/**
 * 认证服务
 */
import { User, ApiResponse } from '../types';
import { silentFetch, noAutoLogoutFetch } from '../utils/request';

const API_BASE = '/api/users/auth';

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

class AuthService {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${API_BASE}/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      errorHandling: {
        autoHandle401: false, // 登录页面不自动处理401
        showErrorMessage: false, // 登录错误由组件自己处理
      },
    } as any);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '登录失败');
    }

    const result: ApiResponse<LoginResponse> = await response.json();
    return result.data!;
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    const token = localStorage.getItem('quanttrade_token');

    if (token) {
      try {
        await silentFetch(`${API_BASE}/logout/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      } catch (error) {
        console.warn('登出请求失败:', error);
      }
    }

    // 清除本地存储
    localStorage.removeItem('quanttrade_token');
    localStorage.removeItem('quanttrade_user');
  }

  /**
   * 刷新令牌
   */
  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await fetch(`${API_BASE}/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
      errorHandling: {
        autoHandle401: true, // 刷新token失败时应该退出登录
        showErrorMessage: false, // 刷新token错误静默处理
      },
    } as any);

    if (!response.ok) {
      throw new Error('刷新令牌失败');
    }

    const result: ApiResponse<{ access_token: string }> = await response.json();
    return result.data!;
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem('quanttrade_token');

    if (!token) {
      throw new Error('未找到认证令牌');
    }

    const response = await fetch(`${API_BASE}/../profile/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      errorHandling: {
        autoHandle401: true, // 获取用户信息失败时应该退出登录
        showErrorMessage: false, // 用户信息错误静默处理
      },
    } as any);

    if (!response.ok) {
      throw new Error('获取用户信息失败');
    }

    const result: ApiResponse<User> = await response.json();
    return result.data!;
  }

  /**
   * 验证token有效性
   */
  async validateToken(): Promise<boolean> {
    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 检查用户权限（不会导致退出登录）
   */
  async checkPermission(permission: string): Promise<boolean> {
    try {
      const response = await noAutoLogoutFetch(`/api/users/permissions/check/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ permission }),
      });

      if (!response.ok) {
        return false;
      }

      const result = await response.json();
      return result.data?.hasPermission || false;
    } catch (error) {
      console.warn('权限检查失败:', error);
      return false;
    }
  }
}

export const authService = new AuthService();
export default authService;