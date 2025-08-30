/**
 * 认证守卫组件
 */

import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '@/store';
import { ROUTES } from '@/constants';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, loading, token } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    // 如果有token但未认证，可以在这里验证token有效性
    if (token && !isAuthenticated) {
      // TODO: 验证token有效性的逻辑
    }
  }, [token, isAuthenticated]);

  // 正在加载中
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '16px',
      }}>
        <Spin size="large" />
        <div>正在验证身份...</div>
      </div>
    );
  }

  // 未认证，重定向到登录页
  if (!isAuthenticated) {
    return (
      <Navigate 
        to={ROUTES.LOGIN} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // 已认证，渲染子组件
  return <>{children}</>;
};

export default AuthGuard;