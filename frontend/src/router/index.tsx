/**
 * 路由配置
 */

import React, { Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { ROUTES } from '@/constants';
import Layout from '@/components/layout/Layout';
import AuthGuard from '@/components/auth/AuthGuard';

// 页面组件懒加载
const LoginPage = React.lazy(() => import('@/pages/Login'));
const DashboardPage = React.lazy(() => import('@/pages/Dashboard'));
const UserManagementPage = React.lazy(() => import('@/pages/UserManagement'));
const MenuManagementPage = React.lazy(() => import('@/pages/MenuManagement'));
const ExchangesPage = React.lazy(() => import('@/pages/Exchanges'));
const TradingPage = React.lazy(() => import('@/pages/Trading'));
const StrategiesPage = React.lazy(() => import('@/pages/Strategies'));
const MarketPage = React.lazy(() => import('@/pages/Market'));
const RiskPage = React.lazy(() => import('@/pages/Risk'));
const SystemPage = React.lazy(() => import('@/pages/System'));
const ProfilePage = React.lazy(() => import('@/pages/Profile'));

// 加载组件
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

// 路由配置
export const router = createBrowserRouter([
  {
    path: ROUTES.LOGIN,
    element: (
      <Suspense fallback={<PageLoading />}>
        <LoginPage />
      </Suspense>
    ),
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <Layout />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to={ROUTES.DASHBOARD} replace />,
      },
      {
        path: ROUTES.DASHBOARD,
        element: (
          <Suspense fallback={<PageLoading />}>
            <DashboardPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.USERS,
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserManagementPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.MENUS,
        element: (
          <Suspense fallback={<PageLoading />}>
            <MenuManagementPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.EXCHANGES,
        element: (
          <Suspense fallback={<PageLoading />}>
            <ExchangesPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.TRADING,
        element: (
          <Suspense fallback={<PageLoading />}>
            <TradingPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.STRATEGIES,
        element: (
          <Suspense fallback={<PageLoading />}>
            <StrategiesPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.MARKET,
        element: (
          <Suspense fallback={<PageLoading />}>
            <MarketPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.RISK,
        element: (
          <Suspense fallback={<PageLoading />}>
            <RiskPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.SYSTEM,
        element: (
          <Suspense fallback={<PageLoading />}>
            <SystemPage />
          </Suspense>
        ),
      },
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
  {
    path: '*',
    element: <Navigate to={ROUTES.DASHBOARD} replace />,
  },
]);