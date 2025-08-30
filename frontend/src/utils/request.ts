/**
 * HTTP请求工具 - 增强版fetch API
 * 
 * 提供了以下核心功能：
 * 1. 自动添加JWT认证头
 * 2. 智能的401错误处理（避免误退出登录）
 * 3. 统一的错误消息显示和处理
 * 4. 可配置的错误处理策略
 * 5. 网络错误处理和重试机制
 * 
 * @author QuantTrade Team
 * @version 2.0.0
 */
import { message } from 'antd';

/**
 * 错误处理配置接口
 * 
 * 用于控制HTTP请求的错误处理行为，支持细粒度的错误处理策略
 */
interface ErrorHandlingConfig {
  /** 是否自动处理401错误（清除token并跳转登录页） */
  autoHandle401?: boolean;
  /** 是否显示错误消息提示给用户 */
  showErrorMessage?: boolean;
  /** 自定义错误处理回调函数，用于特殊的错误处理逻辑 */
  onError?: (error: Error, response?: Response) => void;
}

/**
 * 全局错误处理配置
 * 
 * 默认配置：
 * - 自动处理401错误：开启
 * - 显示错误消息：开启
 */
let globalErrorConfig: ErrorHandlingConfig = {
  autoHandle401: true,
  showErrorMessage: true,
};

/**
 * 设置全局错误处理配置
 * 
 * 允许在应用启动时或运行时动态调整错误处理策略
 * 
 * @param config 部分错误处理配置，会与现有配置合并
 * 
 * @example
 * ```typescript
 * // 禁用自动401处理
 * setGlobalErrorConfig({ autoHandle401: false });
 * 
 * // 设置全局错误处理回调
 * setGlobalErrorConfig({
 *   onError: (error, response) => {
 *     console.error('全局错误:', error);
 *   }
 * });
 * ```
 */
export const setGlobalErrorConfig = (config: Partial<ErrorHandlingConfig>) => {
  globalErrorConfig = { ...globalErrorConfig, ...config };
};

/**
 * 检查是否为认证相关的API端点
 * 
 * 认证端点包括登录、刷新token、登出等，这些端点的401错误
 * 通常意味着token确实无效，需要强制退出登录
 * 
 * @param url 请求的URL地址
 * @returns 是否为认证相关端点
 */
const isAuthEndpoint = (url: string): boolean => {
  const authEndpoints = ['/api/users/auth/login/', '/api/users/auth/refresh/', '/api/users/auth/logout/'];
  return authEndpoints.some(endpoint => url.includes(endpoint));
};

/**
 * 检查是否应该强制退出登录
 * 
 * 智能判断401错误是否需要强制用户退出登录：
 * 1. 认证端点的401错误 - 需要强制退出
 * 2. 获取用户信息的401错误 - 需要强制退出
 * 3. 其他业务接口的401错误 - 不强制退出（可能是权限不足）
 * 
 * 这样可以避免用户在进行某些操作时因为权限不足而被误退出登录
 * 
 * @param url 请求的URL地址
 * @param status HTTP状态码
 * @returns 是否应该强制退出登录
 */
const shouldForceLogout = (url: string, status: number): boolean => {
  // 如果是认证端点的401错误，说明token确实无效
  if (isAuthEndpoint(url) && status === 401) {
    return true;
  }
  
  // 如果是获取用户信息的401错误，说明token无效
  if (url.includes('/api/users/profile/') && status === 401) {
    return true;
  }
  
  // 其他情况不强制退出（可能只是权限不足）
  return false;
};

/**
 * 保存原始的fetch函数引用
 * 用于在拦截器中调用原始的fetch功能
 */
const originalFetch = window.fetch;

/**
 * 增强版fetch函数 - 全局请求拦截器
 * 
 * 重写了原生的fetch函数，添加了以下功能：
 * 1. 自动添加JWT认证头
 * 2. 统一的错误处理和消息提示
 * 3. 智能的401错误处理策略
 * 4. 网络错误处理
 * 
 * @param input 请求的URL或Request对象
 * @param init 请求配置选项（扩展了errorHandling配置）
 * @returns Promise<Response> 响应对象
 */
window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  // 获取本地存储的JWT token
  const token = localStorage.getItem('quanttrade_token');
  
  // 提取请求配置中的错误处理选项
  const requestConfig = init as RequestInit & { errorHandling?: ErrorHandlingConfig };
  const errorHandling = { ...globalErrorConfig, ...requestConfig?.errorHandling };
  
  // 准备请求配置，设置默认的Content-Type
  const config: RequestInit = {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  };

  // 移除自定义的errorHandling属性，避免传递给原生fetch
  delete (config as any).errorHandling;

  // 如果有token且是API请求，自动添加Authorization头
  if (token && typeof input === 'string' && input.startsWith('/api')) {
    config.headers = {
      ...config.headers,
      'Authorization': `Bearer ${token}`,
    };
  }

  try {
    // 发送HTTP请求
    const response = await originalFetch(input, config);
    const url = typeof input === 'string' ? input : input.toString();
    
    // 处理401认证失败错误
    if (response.status === 401) {
      // 尝试解析错误响应体，获取详细错误信息
      const errorData = await response.json().catch(() => ({ message: '认证失败' }));
      const error = new Error(errorData.message || '认证失败');
      
      // 智能判断是否需要强制退出登录
      if (errorHandling.autoHandle401 && shouldForceLogout(url, response.status)) {
        // 清除本地存储的认证信息
        localStorage.removeItem('quanttrade_token');
        localStorage.removeItem('quanttrade_user');
        
        // 重定向到登录页面（避免在登录页重复跳转）
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        
        // 显示登录过期提示
        if (errorHandling.showErrorMessage) {
          message.error('登录已过期，请重新登录');
        }
      } else {
        // 不强制退出，只显示权限相关的错误消息
        if (errorHandling.showErrorMessage) {
          message.error(errorData.message || '权限不足或操作被拒绝');
        }
      }
      
      // 调用自定义错误处理回调
      if (errorHandling.onError) {
        errorHandling.onError(error, response);
      }
      
      throw error;
    }
    
    // 处理403权限不足错误
    if (response.status === 403) {
      const errorData = await response.json().catch(() => ({ message: '权限不足' }));
      const error = new Error(errorData.message || '权限不足');
      
      if (errorHandling.showErrorMessage) {
        message.error(errorData.message || '权限不足，无法执行此操作');
      }
      
      if (errorHandling.onError) {
        errorHandling.onError(error, response);
      }
      
      throw error;
    }
    
    // 处理其他HTTP错误状态码（4xx, 5xx）
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.message || `请求失败: ${response.status}`);
      
      if (errorHandling.showErrorMessage) {
        message.error(errorData.message || `请求失败: ${response.status}`);
      }
      
      if (errorHandling.onError) {
        errorHandling.onError(error, response);
      }
      
      throw error;
    }
    
    // 请求成功，返回响应对象
    return response;
  } catch (error) {
    // 处理网络连接错误（如断网、超时等）
    if (error instanceof TypeError && error.message.includes('fetch')) {
      const networkError = new Error('网络连接失败，请检查网络设置');
      
      if (errorHandling.showErrorMessage) {
        message.error('网络连接失败，请检查网络设置');
      }
      
      if (errorHandling.onError) {
        errorHandling.onError(networkError);
      }
      
      throw networkError;
    }
    
    // 重新抛出其他类型的错误
    throw error;
  }
};

/**
 * 创建带有自定义错误处理配置的fetch函数
 * 
 * 允许为特定的请求创建具有不同错误处理策略的fetch函数
 * 
 * @param errorHandling 错误处理配置
 * @returns 配置了特定错误处理策略的fetch函数
 * 
 * @example
 * ```typescript
 * // 创建一个不显示错误消息的fetch函数
 * const quietFetch = createFetch({
 *   showErrorMessage: false,
 *   onError: (error) => console.log('静默处理错误:', error)
 * });
 * 
 * // 使用自定义fetch函数
 * const response = await quietFetch('/api/data');
 * ```
 */
export const createFetch = (errorHandling: ErrorHandlingConfig) => {
  return (input: RequestInfo | URL, init?: RequestInit) => {
    return window.fetch(input, {
      ...init,
      errorHandling,
    } as any);
  };
};

/**
 * 静默请求函数
 * 
 * 不显示任何错误消息，也不自动处理401错误
 * 适用于后台数据同步、轮询等不需要用户感知的请求
 * 
 * @example
 * ```typescript
 * // 静默获取数据，不打扰用户
 * try {
 *   const response = await silentFetch('/api/background-sync');
 *   const data = await response.json();
 * } catch (error) {
 *   // 自行处理错误，不会显示消息提示
 *   console.error('后台同步失败:', error);
 * }
 * ```
 */
export const silentFetch = createFetch({
  autoHandle401: false,
  showErrorMessage: false,
});

/**
 * 不自动登出的请求函数
 * 
 * 显示错误消息但不自动处理401错误（不会强制退出登录）
 * 适用于可能因权限不足而失败但不应该退出登录的操作
 * 
 * @example
 * ```typescript
 * // 尝试访问可能没有权限的资源
 * try {
 *   const response = await noAutoLogoutFetch('/api/admin/sensitive-data');
 *   const data = await response.json();
 * } catch (error) {
 *   // 会显示"权限不足"消息，但不会退出登录
 *   console.error('权限不足:', error);
 * }
 * ```
 */
export const noAutoLogoutFetch = createFetch({
  autoHandle401: false,
  showErrorMessage: true,
});

// 导出增强后的fetch函数作为默认导出
export default window.fetch;