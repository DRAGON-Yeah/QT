/**
 * 应用全局状态管理
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
// import { Breakpoint } from '@/types';
import { STORAGE_KEYS } from '@/constants';
import { getCurrentBreakpoint } from '@/utils';

interface AppState {
  /** 侧边栏是否折叠 */
  sidebarCollapsed: boolean;
  /** 当前断点 */
  breakpoint: 'mobile' | 'tablet' | 'desktop';
  /** 移动端菜单是否打开 */
  mobileMenuOpen: boolean;
  /** 全局加载状态 */
  globalLoading: boolean;
  /** 页面标题 */
  pageTitle: string;
  /** 面包屑导航 */
  breadcrumbs: Array<{ title: string; path?: string }>;
  /** 设置侧边栏折叠状态 */
  setSidebarCollapsed: (collapsed: boolean) => void;
  /** 切换侧边栏折叠状态 */
  toggleSidebar: () => void;
  /** 设置断点 */
  setBreakpoint: (breakpoint: 'mobile' | 'tablet' | 'desktop') => void;
  /** 设置移动端菜单状态 */
  setMobileMenuOpen: (open: boolean) => void;
  /** 切换移动端菜单 */
  toggleMobileMenu: () => void;
  /** 设置全局加载状态 */
  setGlobalLoading: (loading: boolean) => void;
  /** 设置页面标题 */
  setPageTitle: (title: string) => void;
  /** 设置面包屑导航 */
  setBreadcrumbs: (breadcrumbs: Array<{ title: string; path?: string }>) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      sidebarCollapsed: false,
      breakpoint: getCurrentBreakpoint(),
      mobileMenuOpen: false,
      globalLoading: false,
      pageTitle: 'QuantTrade',
      breadcrumbs: [],

      setSidebarCollapsed: (collapsed) => {
        set({ sidebarCollapsed: collapsed });
      },

      toggleSidebar: () => {
        const { sidebarCollapsed } = get();
        set({ sidebarCollapsed: !sidebarCollapsed });
      },

      setBreakpoint: (breakpoint) => {
        set({ breakpoint });
        // 移动端自动关闭菜单
        if (breakpoint === 'mobile') {
          set({ mobileMenuOpen: false });
        }
      },

      setMobileMenuOpen: (open) => {
        set({ mobileMenuOpen: open });
      },

      toggleMobileMenu: () => {
        const { mobileMenuOpen } = get();
        set({ mobileMenuOpen: !mobileMenuOpen });
      },

      setGlobalLoading: (loading) => {
        set({ globalLoading: loading });
      },

      setPageTitle: (title) => {
        set({ pageTitle: title });
        // 更新浏览器标题
        document.title = `${title} - QuantTrade`;
      },

      setBreadcrumbs: (breadcrumbs) => {
        set({ breadcrumbs });
      },
    }),
    {
      name: STORAGE_KEYS.SIDEBAR_COLLAPSED,
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);