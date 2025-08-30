/**
 * 主题提供者组件
 */

import React, { useEffect } from 'react';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useThemeStore } from '@/store';

interface ThemeProviderProps {
  children: React.ReactNode;
}

const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const { theme: themeConfig } = useThemeStore();

  // 应用主题到CSS变量
  useEffect(() => {
    const root = document.documentElement;
    
    // 设置CSS变量
    root.style.setProperty('--primary-color', themeConfig.primaryColor);
    root.style.setProperty('--border-radius', `${themeConfig.borderRadius}px`);
    root.style.setProperty('--font-size', `${themeConfig.fontSize}px`);
    
    // 设置主题模式类名
    root.className = themeConfig.mode === 'dark' ? 'dark-theme' : 'light-theme';
  }, [themeConfig]);

  // Ant Design 主题配置
  const antdTheme = {
    token: {
      colorPrimary: themeConfig.primaryColor,
      borderRadius: themeConfig.borderRadius,
      fontSize: themeConfig.fontSize,
    },
    algorithm: themeConfig.mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
  };

  return (
    <ConfigProvider
      locale={zhCN}
      theme={antdTheme}
    >
      {children}
    </ConfigProvider>
  );
};

export default ThemeProvider;