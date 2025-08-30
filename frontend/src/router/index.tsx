/**
 * QuantTrade 前端路由配置
 * 
 * 本文件定义了整个应用的路由结构，采用React Router v6的配置方式
 * 所有页面组件都使用懒加载以优化首屏加载性能
 * 
 * 路由结构按照菜单层级组织：
 * - 仪表盘：系统概览和快速操作
 * - 账户管理：用户管理、角色权限、交易账户
 * - 交易中心：现货交易、订单管理、持仓管理、交易历史
 * - 策略管理：策略列表、策略回测、策略监控、风险控制
 * - 数据分析：市场行情、收益分析、风险分析、报表中心
 * - 系统设置：菜单管理、系统监控、数据库管理、系统日志、系统配置
 */

import React, { Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { ROUTES } from '@/constants';
import Layout from '@/components/layout/Layout';
import AuthGuard from '@/components/auth/AuthGuard';

// ==================== 页面组件懒加载 ====================

// 基础页面
const LoginPage = React.lazy(() => import('@/pages/Login'));
const DashboardPage = React.lazy(() => import('@/pages/Dashboard'));

// 账户管理相关页面
const UserManagementPage = React.lazy(() => import('@/pages/UserManagement'));
// TODO: 添加角色权限管理页面
// const RoleManagementPage = React.lazy(() => import('@/pages/RoleManagement'));
// TODO: 添加交易账户管理页面  
// const ExchangeAccountPage = React.lazy(() => import('@/pages/ExchangeAccount'));

// 交易中心相关页面
const TradingPage = React.lazy(() => import('@/pages/Trading'));
// TODO: 添加订单管理页面
// const OrderManagementPage = React.lazy(() => import('@/pages/OrderManagement'));
// TODO: 添加持仓管理页面
// const PositionManagementPage = React.lazy(() => import('@/pages/PositionManagement'));
// TODO: 添加交易历史页面
// const TradingHistoryPage = React.lazy(() => import('@/pages/TradingHistory'));

// 策略管理相关页面
const StrategiesPage = React.lazy(() => import('@/pages/Strategies'));
// TODO: 添加策略回测页面
// const BacktestPage = React.lazy(() => import('@/pages/Backtest'));
// TODO: 添加策略监控页面
// const StrategyMonitorPage = React.lazy(() => import('@/pages/StrategyMonitor'));
// TODO: 添加风险控制页面
// const RiskControlPage = React.lazy(() => import('@/pages/RiskControl'));

// 数据分析相关页面
const MarketPage = React.lazy(() => import('@/pages/Market'));
// TODO: 添加收益分析页面
// const ProfitAnalysisPage = React.lazy(() => import('@/pages/ProfitAnalysis'));
// TODO: 添加风险分析页面
// const RiskAnalysisPage = React.lazy(() => import('@/pages/RiskAnalysis'));
// TODO: 添加报表中心页面
// const ReportCenterPage = React.lazy(() => import('@/pages/ReportCenter'));

// 系统设置相关页面
const MenuManagementPage = React.lazy(() => import('@/pages/MenuManagement'));
const SystemPage = React.lazy(() => import('@/pages/System'));
// TODO: 添加系统监控页面
// const SystemMonitorPage = React.lazy(() => import('@/pages/SystemMonitor'));
// TODO: 添加数据库管理页面
// const DatabaseManagementPage = React.lazy(() => import('@/pages/DatabaseManagement'));
// TODO: 添加系统日志页面
// const SystemLogsPage = React.lazy(() => import('@/pages/SystemLogs'));
// TODO: 添加系统配置页面
// const SystemConfigPage = React.lazy(() => import('@/pages/SystemConfig'));

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
  // 登录页面 - 无需认证
  {
    path: ROUTES.LOGIN,
    element: (
      <Suspense fallback={<PageLoading />}>
        <LoginPage />
      </Suspense>
    ),
  },
  
  // 主应用 - 需要认证
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
      
      // 👥 账户管理 - 用户管理
      {
        path: ROUTES.USERS,
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserManagementPage />
          </Suspense>
        ),
      },
      
      // 📈 交易中心 - 现货交易
      {
        path: ROUTES.TRADING,
        element: (
          <Suspense fallback={<PageLoading />}>
            <TradingPage />
          </Suspense>
        ),
      },
      
      // 🧠 策略管理 - 策略列表
      {
        path: ROUTES.STRATEGIES,
        element: (
          <Suspense fallback={<PageLoading />}>
            <StrategiesPage />
          </Suspense>
        ),
      },
      
      // 📊 数据分析 - 市场行情
      {
        path: ROUTES.MARKET,
        element: (
          <Suspense fallback={<PageLoading />}>
            <MarketPage />
          </Suspense>
        ),
      },
      
      // ⚙️ 系统设置 - 菜单管理
      {
        path: ROUTES.MENUS,
        element: (
          <Suspense fallback={<PageLoading />}>
            <MenuManagementPage />
          </Suspense>
        ),
      },
      
      // ⚙️ 系统设置 - 系统监控
      {
        path: ROUTES.SYSTEM,
        element: (
          <Suspense fallback={<PageLoading />}>
            <SystemPage />
          </Suspense>
        ),
      },
      
      // 👤 个人中心
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
  
  // 404处理 - 重定向到仪表盘
  {
    path: '*',
    element: <Navigate to={ROUTES.DASHBOARD} replace />,
  },
]);