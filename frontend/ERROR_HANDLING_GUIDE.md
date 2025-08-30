# QuantTrade 前端错误处理指南

## 概述

QuantTrade 前端应用采用分层错误处理机制，在移除全局 ErrorBoundary 后，错误处理变得更加灵活和精确。系统会智能地区分不同类型的错误，只有在真正的认证失效时才会退出登录。

## 核心特性

### 1. 智能错误分类
- **认证错误**：token过期、无效token → 自动退出登录
- **权限不足**：403错误 → 显示错误消息，保持登录状态
- **业务错误**：其他API错误 → 显示错误消息，保持登录状态
- **网络错误**：连接失败 → 显示网络错误消息

### 2. 可配置的错误处理
每个请求都可以自定义错误处理行为：

### 3. 页面级错误边界
- 提供清晰的错误消息
- 区分系统错误和用户操作错误
- 提供解决建议

## 最佳实践

### 1. 选择合适的请求方式
- **业务API**：使用 `noAutoLogoutFetch`
- **后台检查**：使用 `silentFetch`
- **认证相关**：使用普通 `fetch` 并配置 `autoHandle401: true`

### 2. 错误消息处理
- 为用户操作提供清晰的错误消息
- 区分系统错误和用户错误
- 提供解决建议

### 3. 用户体验
- 不要因为权限问题强制退出用户
- 提供重试机制
- 保持应用状态的一致性

## 向后兼容

- 现有代码无需修改即可享受新的错误处理机制
- 逐步迁移到新的错误处理方式
- 保持API接口不变
## 使用方法

### 1. 在组件中使用错误处理Hook

```typescript
import { useErrorHandler } from '@/hooks';

const MyComponent = () => {
  const { handleError, handleAsyncError } = useErrorHandler();

  // 处理异步操作
  const loadData = async () => {
    try {
      const data = await apiService.getData();
      setData(data);
    } catch (error) {
      handleError(error, {
        customMessage: '加载数据失败，请稍后重试',
        showMessage: true,
      });
    }
  };

  // 处理单个错误
  const handleAction = () => {
    try {
      await apiService.performAction();
    } catch (error) {
      handleError(error, {
        customMessage: '操作失败',
        showMessage: true
      });
    }
  };
};
```

### 2. 直接使用服务接口

```typescript
import { userService } from '@/services/userService';

// 服务已经使用了 noAutoLogoutFetch
// 权限不足时不会显示错误消息但不退出登录
const users = await userService.getUsers();
```

### 3. 特殊请求函数

```typescript
import { noAutoLogoutFetch, silentFetch } from '@/utils/auth';

// 不会自动退出登录的请求
const data = await noAutoLogoutFetch('/api/users');

// 静默请求，不显示错误消息
const result = await silentFetch('/api/check');
```

## 自定义错误处理

每个请求都可以自定义错误处理行为：

```typescript
// 自定义错误处理
const response = await fetch('/api/data', {
  errorHandling: {
    autoHandle401: false,   // 不自动处理401错误
    showErrorMessage: true, // 显示错误消息
    onError: (error) => {
      console.log('自定义处理:', error);
      // 自定义错误处理
    }
  }
} as any);
```## 错误处理策略

### 认证错误 (401)

| 端点类型 | 处理策略 | 说明 |
|---------|---------|------|
| `/api/auth/login/` | 不自动处理 | 由登录组件处理 |
| `/api/users/` | 自动退出登录 | token确实无效 |
| `/api/auth/refresh/` | 自动退出登录 | 刷新失败 |
| `/api/users/profile/` | 自动退出登录 | 用户信息获取失败 |
| 其他业务API | 显示错误消息 | 可能是临时权限问题 |

### 权限错误 (403)
- 显示"权限不足，无法执行此操作"
- 不退出登录
- 用户可以继续使用其他功能

### 网络错误
- 显示"网络连接失败，请检查网络设置"
- 不退出登录
- 建议用户检查网络

## 页面级错误边界

在移除全局 ErrorBoundary 后，建议在关键页面使用页面级错误边界：

```typescript
import ErrorBoundary from '@/components/error/ErrorBoundary';

const TradingPage: React.FC = () => {
  return (
    <ErrorBoundary>
      <TradingContent />
    </ErrorBoundary>
  );
};
```

## 开发和测试

### 开发环境测试
在浏览器控制台中运行：

```javascript
// 测试权限错误（不会退出登录）
ErrorHandlingTest.testPermissionError();

// 测试业务认证错误（不会退出登录）
ErrorHandlingTest.testBusinessAuthError();

// 测试静默请求（不显示错误消息）
ErrorHandlingTest.testSilentRequest();

// 运行所有测试
ErrorHandlingTest.runAllTests();
```## 故障排除

### 问题：用户仍然被意外退出登录
**解决方案**：
1. 检查是否使用了 `noAutoLogoutFetch`
2. 确认错误处理配置正确
3. 查看控制台错误日志

### 问题：错误消息不显示
**解决方案**：
1. 检查 `showErrorMessage` 配置
2. 确认没有使用 `silentFetch`
3. 检查错误处理Hook的使用

### 问题：权限错误仍然退出登录
**解决方案**：
1. 确认使用了 `noAutoLogoutFetch`
2. 检查请求URL是否在错误状态码处理逻辑白名单中
3. 验证错误处理中间件配置

## 迁移指南

### 从全局 ErrorBoundary 迁移

1. **移除全局依赖**：应用根组件不再包含 ErrorBoundary
2. **添加页面级处理**：在需要的页面添加 ErrorBoundary
3. **使用错误处理 Hook**：在组件中使用 `useErrorHandler`
4. **配置请求选项**：为API请求配置适当的错误处理选项

### 最佳实践建议

1. **关键页面使用错误边界**：交易、用户管理等重要页面
2. **统一错误消息风格**：保持错误提示的一致性
3. **提供恢复选项**：为用户提供重试或返回的选择
4. **监控错误发生**：集成错误监控服务（如 Sentry）

## 相关文件

- `frontend/src/App.tsx` - 应用根组件（已移除 ErrorBoundary）
- `frontend/src/components/error/ErrorBoundary.tsx` - 错误边界组件
- `frontend/src/hooks/useErrorHandler.ts` - 错误处理 Hook
- `frontend/src/utils/request.ts` - 请求工具函数