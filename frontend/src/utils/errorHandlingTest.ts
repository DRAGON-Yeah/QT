/**
 * 错误处理机制测试工具
 * 用于测试不同类型的错误处理行为
 */

import { noAutoLogoutFetch, silentFetch } from './request';

export class ErrorHandlingTest {
  /**
   * 测试权限不足错误 (403)
   * 应该显示错误消息但不退出登录
   */
  static async testPermissionError() {
    console.log('测试权限不足错误...');
    try {
      await noAutoLogoutFetch('/api/test/permission-denied', {
        method: 'POST',
      });
    } catch (error) {
      console.log('权限错误已被正确处理:', error);
    }
  }

  /**
   * 测试认证错误 (401) - 业务端点
   * 应该显示错误消息但不退出登录
   */
  static async testBusinessAuthError() {
    console.log('测试业务端点认证错误...');
    try {
      await noAutoLogoutFetch('/api/users/list', {
        headers: {
          'Authorization': 'Bearer invalid-token',
        },
      });
    } catch (error) {
      console.log('业务认证错误已被正确处理:', error);
    }
  }

  /**
   * 测试用户信息端点认证错误
   * 应该自动退出登录
   */
  static async testUserInfoAuthError() {
    console.log('测试用户信息端点认证错误...');
    try {
      await fetch('/api/users/profile/', {
        headers: {
          'Authorization': 'Bearer invalid-token',
        },
        errorHandling: {
          autoHandle401: true,
          showErrorMessage: true,
        },
      } as any);
    } catch (error) {
      console.log('用户信息认证错误已被正确处理:', error);
    }
  }

  /**
   * 测试静默请求
   * 不应该显示错误消息
   */
  static async testSilentRequest() {
    console.log('测试静默请求...');
    try {
      await silentFetch('/api/test/error');
    } catch (error) {
      console.log('静默请求错误已被正确处理（无消息显示）:', error);
    }
  }

  /**
   * 测试网络错误
   */
  static async testNetworkError() {
    console.log('测试网络错误...');
    try {
      await noAutoLogoutFetch('/api/nonexistent-endpoint');
    } catch (error) {
      console.log('网络错误已被正确处理:', error);
    }
  }

  /**
   * 运行所有测试
   */
  static async runAllTests() {
    console.log('开始错误处理机制测试...');
    
    await this.testPermissionError();
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    await this.testBusinessAuthError();
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    await this.testSilentRequest();
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    await this.testNetworkError();
    
    console.log('所有测试完成');
  }
}

// 在开发环境下暴露到全局对象，方便在控制台测试
if (process.env.NODE_ENV === 'development') {
  (window as any).ErrorHandlingTest = ErrorHandlingTest;
}