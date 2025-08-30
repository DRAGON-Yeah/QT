/**
 * QuantTrade 前端路由配置
 * 
 * 本文件定义了整个应用的路由结构，采用React Router v6的配置方式
 * 所有页面组件都使用懒加载以优化首屏加载性能
 * 
 * 路由结构按照新的二级菜单层级组织：
 * - 仪表盘：系统概览和快速操作
 * - 账户管理：用户管理、角色权限、交易账户
 * - 交易中心：现货交易、订单管理、持仓管理、交易历史
 * - 策略管理：策略列表、策略回测、策略监控、风险控制
 * - 数据分析：市场行情、收益分析、风险分析、报表中心
 * - 系统设置：菜单管理、系统监控、数据库管理、系统日志、系统配置
 * 
 * @author QuantTrade Team
 * @version 2.0.0
 * @since 2024-01-01
 */

import React, { Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { ROUTES } from '@/constants';
import Layout from '@/components/layout/Layout';
import AuthGuard from '@/components/auth/AuthGuard';

// ==================== 页面组件懒加载 ====================
// 使用React.lazy进行代码分割，提高首屏加载性能

// 基础页面
const LoginPage = React.lazy(() => import('@/pages/Login'));
const DashboardPage = React.lazy(() => import('@/pages/Dashboard'));

// 账户管理相关页面
const UserManagementPage = React.lazy(() => import('@/pages/UserManagement'));

// 交易中心相关页面
const TradingPage = React.lazy(() => import('@/pages/Trading'));

// 策略管理相关页面
const StrategiesPage = React.lazy(() => import('@/pages/Strategies'));

// 数据分析相关页面
const MarketPage = React.lazy(() => import('@/pages/Market'));

// 系统设置相关页面
const MenuManagementPage = React.lazy(() => import('@/pages/MenuManagement'));
const SystemPage = React.lazy(() => import('@/pages/System'));

// 其他页面
const ProfilePage = React.lazy(() => import('@/pages/Profile'));

// ==================== 加载组件 ====================

/**
 * 页面加载中组件
 * 在懒加载页面组件时显示的加载状态
 */
const PageLoading: React.FC = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '200px' 
  }}>
    <Spin size="large" />
  </div>
);

// ==================== 路由配置 ====================

/**
 * 应用主路由配置
 * 
 * 路由结构说明：
 * 1. 登录页面：独立路由，不需要认证
 * 2. 主应用：需要认证，包含所有业务页面
 * 3. 404处理：未匹配路由重定向到仪表盘
 * 
 * 所有业务页面都包装在AuthGuard中进行权限验证
 * 使用Suspense处理懒加载组件的加载状态
 */
export const router = createBrowserRouter([
  // ==================== 登录页面 - 无需认证 ====================
  {
    path: ROUTES.LOGIN,
    element: (
      <Suspense fallback={<PageLoading />}>
        <LoginPage />
      </Suspense>
    ),
  },
  
  // ==================== 主应用 - 需要认证 ====================
  {
    path: '/',
    element: (
      <AuthGuard>
        <Layout />
      </AuthGuard>
    ),
    children: [
      // 根路径重定向到仪表盘
      {
        index: true,
        element: <Navigate to={ROUTES.DASHBOARD} replace />,
      },
      
      // 🏠 仪表盘 - 系统概览和快速操作
      {
        path: ROUTES.DASHBOARD,
        element: (
          <Suspense fallback={<PageLoading />}>
            <DashboardPage />
          </Suspense>
        ),
      },
      
      // ==================== 👥 账户管理模块 ====================
      
      // 用户管理 - 用户列表、创建、编辑、删除
      {
        path: '/account/users',
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserManagementPage />
          </Suspense>
        ),
      },
      
      // 角色权限 - 角色管理、权限分配
      {
        path: '/account/roles',
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserManagementPage />
          </Suspense>
        ),
      },
      
      // 交易账户 - 交易所API密钥管理
      {
        path: '/account/exchanges',
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserManagementPage />
          </Suspense>
        ),
      },
      
      // ==================== 📈 交易中心模块 ====================
      
      // 现货交易 - 实时交易界面
      {
        path: '/trading/spot',
        element: (
          <Suspense fallback={<PageLoading />}>
            <TradingPage />
          </Suspense>
        ),
      },
      
      // 订单管理 - 当前订单、历史订单
      {
        path: '/trading/orders',
        element: (
          <Suspense fallback={<PageLoading />}>
            <TradingPage />
          </Suspense>
        ),
      },
      
      // 持仓管理 - 当前持仓分析
      {
        path: '/trading/positions',
        element: (
          <Suspense fallback={<PageLoading />}>
            <TradingPage />
          </Suspense>
        ),
      },
      
      // 交易历史 - 成交记录统计
      {
        path: '/trading/history',
        element: (
          <Suspense fallback={<PageLoading />}>
            <TradingPage />
          </Suspense>
        ),
      },
      
      // ==================== 🧠 策略管理模块 ====================
      
      // 策略列表 - 策略库管理
      {
        path: '/strategy/list',
        element: (
          <Suspense fallback={<PageLoading />}>
            <StrategiesPage />
          </Suspense>
        ),
      },
      
      // 策略回测 - 历史数据回测
      {
        path: '/strategy/backtest',
        element: (
          <Suspense fallback={<PageLoading />}>
            <StrategiesPage />
          </Suspense>
        ),
      },
      
      // 策略监控 - 实时策略监控
      {
        path: '/strategy/monitor',
        element: (
          <Suspense fallback={<PageLoading />}>
            <StrategiesPage />
          </Suspense>
        ),
      },
      
      // 风险控制 - 风险参数设置
      {
        path: '/strategy/risk',
        element: (
          <Suspense fallback={<PageLoading />}>
            <StrategiesPage />
          </Suspense>
        ),
      },
      
      // ==================== 📊 数据分析模块 ====================
      
      // 市场行情 - 实时行情数据
      {
        path: '/analysis/market',
        element: (
          <Suspense fallback={<PageLoading />}>
            <MarketPage />
          </Suspense>
        ),
      },
      
      // 收益分析 - 收益统计分析
      {
        path: '/analysis/performance',
        element: (
          <Suspense fallback={<PageLoading />}>
            <MarketPage />
          </Suspense>
        ),
      },
      
      // 风险分析 - 风险指标分析
      {
        path: '/analysis/risk',
        element: (
          <Suspense fallback={<PageLoading />}>
            <MarketPage />
          </Suspense>
        ),
      },
      
      // 报表中心 - 报表生成导出
      {
        path: '/analysis/reports',
        element: (
          <Suspense fallback={<PageLoading />}>
            <MarketPage />
          </Suspense>
        ),
      },
      
      // ==================== ⚙️ 系统设置模块 ====================
      
      // 菜单管理 - 动态菜单配置
      {
        path: '/system/menus',
        element: (
          <Suspense fallback={<PageLoading />}>
            <MenuManagementPage />
          </Suspense>
        ),
      },
      
      // 系统监控 - 系统状态监控
      {
        path: '/system/monitor',
        element: (
          <Suspense fallback={<PageLoading />}>
            <SystemPage />
          </Suspense>
        ),
      },
      
      // 数据库管理 - 数据库运维
      {
        path: '/system/database',
        element: (
          <Suspense fallback={<PageLoading />}>
            <SystemPage />
          </Suspense>
        ),
      },
      
      // 系统日志 - 日志查看分析
      {
        path: '/system/logs',
        element: (
          <Suspense fallback={<PageLoading />}>
            <SystemPage />
          </Suspense>
        ),
      },
      
      // 系统配置 - 系统参数配置
      {
        path: '/system/config',
        element: (
          <Suspense fallback={<PageLoading />}>
            <SystemPage />
          </Suspense>
        ),
      },
      
      // ==================== 兼容性路由 ====================
      // 为了保持向后兼容，将旧路由重定向到新路由
      {
        path: '/users',
        element: <Navigate to="/account/users" replace />,
      },
      {
        path: '/menus',
        element: <Navigate to="/system/menus" replace />,
      },
      {
        path: '/trading',
        element: <Navigate to="/trading/spot" replace />,
      },
      {
        path: '/strategies',
        element: <Navigate to="/strategy/list" replace />,
      },
      {
        path: '/market',
        element: <Navigate to="/analysis/market" replace />,
      },
      {
        path: '/system',
        element: <Navigate to="/system/monitor" replace />,
      },
      {
        path: '/exchanges',
        element: <Navigate to="/account/exchanges" replace />,
      },
      {
        path: '/risk',
        element: <Navigate to="/strategy/risk" replace />,
      },
      
      // ==================== 其他页面 ====================
      
      // 👤 个人中心 - 用户个人信息管理
      {
        path: ROUTES.PROFILE,
        element: (
          <Suspense fallback={<PageLoading />}>
            <ProfilePage />
          </Suspense>
        ),
      },
    ],
  },
  
  // ==================== 404处理 ====================
  // 未匹配的路由重定向到仪表盘
  {
    path: '*',
    element: <Navigate to={ROUTES.DASHBOARD} replace />,
  },
]);