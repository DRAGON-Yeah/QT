/**
 * 错误处理Hook
 */

import { useCallback } from 'react';
import { message } from 'antd';
import { useAuthStore } from '@/store';

interface ErrorHandlerOptions {
  /** 是否显示错误消息 */
  showMessage?: boolean;
  /** 自定义错误消息 */
  customMessage?: string;
  /** 是否在权限错误时自动退出登录 */
  logoutOnAuthError?: boolean;
}

export const useErrorHandler = () => {
  const { logout } = useAuthStore();

  const handleError = useCallback((
    error: Error | unknown,
    options: ErrorHandlerOptions = {}
  ) => {
    const {
      showMessage = true,
      customMessage,
      logoutOnAuthError = false,
    } = options;

    let errorMessage = '操作失败';
    let shouldLogout = false;

    if (error instanceof Error) {
      errorMessage = error.message;
      
      // 检查是否为认证错误
      if (error.message.includes('认证失败') || 
          error.message.includes('登录已过期') ||
          error.message.includes('Token已过期')) {
        shouldLogout = logoutOnAuthError;
        errorMessage = '登录已过期，请重新登录';
      }
      
      // 检查是否为权限错误
      if (error.message.includes('权限不足') || 
          error.message.includes('无权限') ||
          error.message.includes('403')) {
        errorMessage = '权限不足，无法执行此操作';
      }
      
      // 检查是否为网络错误
      if (error.message.includes('网络') || 
          error.message.includes('fetch')) {
        errorMessage = '网络连接失败，请检查网络设置';
      }
    } else if (typeof error === 'string') {
      errorMessage = error;
    }

    // 使用自定义消息
    if (customMessage) {
      errorMessage = customMessage;
    }

    // 显示错误消息
    if (showMessage) {
      message.error(errorMessage);
    }

    // 如果需要退出登录
    if (shouldLogout) {
      setTimeout(() => {
        logout();
        window.location.href = '/login';
      }, 1500);
    }

    // 记录错误到控制台
    console.error('Error handled:', error);

    return {
      message: errorMessage,
      shouldLogout,
    };
  }, [logout]);

  const handleAsyncError = useCallback(async (
    asyncFn: () => Promise<any>,
    options: ErrorHandlerOptions = {}
  ) => {
    try {
      return await asyncFn();
    } catch (error) {
      handleError(error, options);
      throw error; // 重新抛出错误，让调用者决定如何处理
    }
  }, [handleError]);

  return {
    handleError,
    handleAsyncError,
  };
};

export default useErrorHandler;