# 错误处理机制改进文档

## 问题描述

原有系统存在的问题：
1. 用户登录后，任何API请求返回401错误都会自动退出到登录页面
2. 权限不足等非认证错误也会导致强制退出登录
3. 缺乏对不同类型错误的智能处理
4. 用户体验不佳，无法区分真正的认证失效和临时的权限问题

## 解决方案概述

### 1. 智能错误处理机制

通过改进请求拦截器，实现：
- 根据请求URL和错误状态码智能判断是否需要强制退出登录
- 可配置的错误处理行为
- 分级错误处理策略

### 2. 错误处理配置

```typescript
interface ErrorHandlingConfig {
  autoHandle401?: boolean;    // 是否自动处理401错误
  showErrorMessage?: boolean; // 是否显示错误消息
  onError?: (error: Error, response?: Response) => void;
}
```

### 3. 特殊请求函数

- `silentFetch`: 静默请求，不显示错误消息
- `noAutoLogoutFetch`: 不自动退出登录的请求

## 核心改进

### 请求拦截器 (request.ts)
- 智能判断是否应该强制退出登录
- 支持自定义错误处理配置
- 区分认证端点和业务端点

### 认证服务 (authService.ts)
- 登录请求：不自动处理401
- 获取用户信息：失败时自动退出登录
- 业务权限检查：不会导致退出登录

### 业务服务
- 使用 `noAutoLogoutFetch` 进行API调用
- 权限不足时显示错误消息但不退出登录

### 错误处理Hook
- 统一的错误处理逻辑
- 智能错误分类和消息显示
- 可配置的处理行为

## 使用示例

```typescript
// 在组件中使用
const { handleError, handleAsyncError } = useErrorHandler();

// 处理异步操作
await handleAsyncError(async () => {
  const data = await apiService.getData();
  setData(data);
}, {
  customMessage: '加载数据失败',
  showMessage: true,
});
```

## 错误处理策略

### 认证错误 (401)
- 登录端点：由组件处理
- 用户信息端点：自动退出登录
- 业务端点：显示错误消息，不退出登录

### 权限错误 (403)
- 显示权限不足消息
- 不退出登录

### 网络错误
- 显示网络连接失败消息
- 不退出登录

## 优势

1. 更好的用户体验
2. 智能错误处理
3. 可配置性强
4. 一致的错误处理逻辑
5. 易于维护和扩展