/**
 * 主题状态管理
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ThemeConfig } from '@/types';
import { THEME_CONFIG, STORAGE_KEYS } from '@/constants';

interface ThemeState {
  /** 当前主题配置 */
  theme: ThemeConfig;
  /** 设置主题模式 */
  setMode: (mode: 'light' | 'dark') => void;
  /** 设置主色调 */
  setPrimaryColor: (color: string) => void;
  /** 设置边框圆角 */
  setBorderRadius: (radius: number) => void;
  /** 设置字体大小 */
  setFontSize: (size: number) => void;
  /** 重置主题 */
  resetTheme: () => void;
  /** 切换主题模式 */
  toggleMode: () => void;
}

const defaultTheme: ThemeConfig = {
  primaryColor: THEME_CONFIG.PRIMARY_COLOR,
  mode: 'light',
  borderRadius: 6,
  fontSize: 14,
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: defaultTheme,

      setMode: (mode) => {
        set((state) => ({
          theme: { ...state.theme, mode },
        }));
      },

      setPrimaryColor: (primaryColor) => {
        set((state) => ({
          theme: { ...state.theme, primaryColor },
        }));
      },

      setBorderRadius: (borderRadius) => {
        set((state) => ({
          theme: { ...state.theme, borderRadius },
        }));
      },

      setFontSize: (fontSize) => {
        set((state) => ({
          theme: { ...state.theme, fontSize },
        }));
      },

      resetTheme: () => {
        set({ theme: defaultTheme });
      },

      toggleMode: () => {
        const { theme } = get();
        set({
          theme: {
            ...theme,
            mode: theme.mode === 'light' ? 'dark' : 'light',
          },
        });
      },
    }),
    {
      name: STORAGE_KEYS.THEME,
    }
  )
);