/**
 * 认证守卫组件
 */

import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '@/store';
import { ROUTES } from '@/constants';
import { authService } from '@/services/authService';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, loading, token, setLoading, login, logout } = useAuthStore();
  const [initializing, setInitializing] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const initializeAuth = async () => {
      // 如果已经认证，直接返回
      if (isAuthenticated) {
        setInitializing(false);
        return;
      }

      // 如果有token但未认证，验证token有效性
      if (token && !isAuthenticated) {
        setLoading(true);
        try {
          const user = await authService.getCurrentUser();
          login(user, token);
        } catch (error) {
          console.warn('Token验证失败:', error);
          // 不自动清除token，让用户手动重新登录
          // logout();
        } finally {
          setLoading(false);
        }
      }
      
      setInitializing(false);
    };

    initializeAuth();
  }, [token, isAuthenticated, login, logout, setLoading]);

  // 正在初始化或加载中
  if (initializing || loading) {
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