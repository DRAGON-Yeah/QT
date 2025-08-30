/**
 * 认证状态管理
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';
import { STORAGE_KEYS } from '@/constants';

interface AuthState {
  /** 当前用户 */
  user: User | null;
  /** 认证令牌 */
  token: string | null;
  /** 是否已登录 */
  isAuthenticated: boolean;
  /** 是否正在加载 */
  loading: boolean;
  /** 设置用户信息 */
  setUser: (user: User) => void;
  /** 设置令牌 */
  setToken: (token: string) => void;
  /** 登录 */
  login: (user: User, token: string) => void;
  /** 登出 */
  logout: () => void;
  /** 设置加载状态 */
  setLoading: (loading: boolean) => void;
  /** 检查权限 */
  hasPermission: (permission: string) => boolean;
  /** 检查角色 */
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,

      setUser: (user) => {
        set({ user, isAuthenticated: !!user });
      },

      setToken: (token) => {
        set({ token });
      },

      login: (user, token) => {
        set({
          user,
          token,
          isAuthenticated: true,
          loading: false,
        });
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          loading: false,
        });
        // 清除本地存储
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER);
      },

      setLoading: (loading) => {
        set({ loading });
      },

      hasPermission: (permission) => {
        const { user } = get();
        return user?.permissions?.includes(permission) || false;
      },

      hasRole: (role) => {
        const { user } = get();
        return user?.roles?.some((r) => r.name === role) || false;
      },
    }),
    {
      name: STORAGE_KEYS.USER,
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);