/**
 * QuantTrade 应用根组件
 * 
 * 这是整个前端应用的入口组件，负责：
 * 1. 配置全局状态管理（React Query）
 * 2. 提供主题上下文
 * 3. 配置路由系统
 * 4. 初始化响应式布局监听
 * 
 * 注意：此版本移除了 ErrorBoundary，错误处理现在由各个页面组件自行处理
 */

import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ThemeProvider from '@/components/providers/ThemeProvider';
import { useResponsive } from '@/hooks';
import { router } from '@/router';
import '@/styles/global.scss';

/**
 * 创建 React Query 客户端实例
 * 配置全局查询选项：
 * - retry: 1 - 请求失败时重试1次
 * - refetchOnWindowFocus: false - 窗口获得焦点时不自动重新获取数据
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * 应用根组件
 * 
 * 组件层级结构：
 * App
 * └── QueryClientProvider (提供 React Query 上下文)
 *     └── ThemeProvider (提供主题上下文)
 *         └── RouterProvider (提供路由功能)
 * 
 * @returns {JSX.Element} 应用根组件
 */
const App: React.FC = () => {
  // 初始化响应式布局监听，用于适配不同屏幕尺寸
  useResponsive();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <RouterProvider router={router} />
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;