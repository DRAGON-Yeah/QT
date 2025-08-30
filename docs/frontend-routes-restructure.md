# QuantTrade 前端路由结构重构文档

## 变动概述

本次更新对 QuantTrade 前端应用的路由结构进行了全面重构，将原有的扁平化路由结构改为层次化的模块化结构。新的路由设计更符合量化交易平台的业务逻辑，提供了更清晰的功能分组和导航体验。

## 新增功能说明

### 1. 模块化路由结构

新的路由结构按照业务功能进行分组，共分为6个主要模块：

#### 基础路由模块
- `LOGIN: '/login'` - 用户登录页面
- `DASHBOARD: '/dashboard'` - 系统仪表盘

#### 账户管理模块 (`/account`)
- `ACCOUNT: '/account'` - 账户管理主页
- `ACCOUNT_USERS: '/account/users'` - 用户管理页面
- `ACCOUNT_ROLES: '/account/roles'` - 角色权限管理
- `ACCOUNT_EXCHANGES: '/account/exchanges'` - 交易所账户配置

#### 交易中心模块 (`/trading`)
- `TRADING: '/trading'` - 交易中心主页
- `TRADING_SPOT: '/trading/spot'` - 现货交易界面
- `TRADING_ORDERS: '/trading/orders'` - 订单管理页面
- `TRADING_POSITIONS: '/trading/positions'` - 持仓管理页面
- `TRADING_HISTORY: '/trading/history'` - 交易历史记录

#### 策略管理模块 (`/strategy`)
- `STRATEGY: '/strategy'` - 策略管理主页
- `STRATEGY_LIST: '/strategy/list'` - 策略列表页面
- `STRATEGY_BACKTEST: '/strategy/backtest'` - 策略回测页面
- `STRATEGY_MONITOR: '/strategy/monitor'` - 策略监控页面
- `STRATEGY_RISK: '/strategy/risk'` - 策略风险控制

#### 数据分析模块 (`/analysis`)
- `ANALYSIS: '/analysis'` - 数据分析主页
- `ANALYSIS_MARKET: '/analysis/market'` - 市场数据分析
- `ANALYSIS_PERFORMANCE: '/analysis/performance'` - 绩效分析页面
- `ANALYSIS_RISK: '/analysis/risk'` - 风险分析页面
- `ANALYSIS_REPORTS: '/analysis/reports'` - 分析报告页面

#### 系统设置模块 (`/system`)
- `SYSTEM: '/system'` - 系统设置主页
- `SYSTEM_MENUS: '/system/menus'` - 菜单管理页面
- `SYSTEM_MONITOR: '/system/monitor'` - 系统监控页面
- `SYSTEM_DATABASE: '/system/database'` - 数据库管理页面
- `SYSTEM_LOGS: '/system/logs'` - 系统日志页面
- `SYSTEM_CONFIG: '/system/config'` - 系统配置页面

### 2. 向后兼容性支持

为了确保现有功能的平滑过渡，保留了旧路由的映射：

```typescript
// 兼容旧路由（逐步废弃）
USERS: '/account/users',            // 旧用户管理路由
MENUS: '/system/menus',             // 旧菜单管理路由
EXCHANGES: '/account/exchanges',    // 旧交易所管理路由
STRATEGIES: '/strategy/list',       // 旧策略管理路由
MARKET: '/analysis/market',         // 旧市场数据路由
RISK: '/strategy/risk',             // 旧风险管理路由
```

## 修改的功能说明

### 1. 路由常量重构

**修改前：**
```typescript
export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  USERS: '/users',
  MENUS: '/menus',
  EXCHANGES: '/exchanges',
  TRADING: '/trading',
  STRATEGIES: '/strategies',
  MARKET: '/market',
  RISK: '/risk',
  SYSTEM: '/system',
  PROFILE: '/profile',
} as const;
```

**修改后：**
```typescript
export const ROUTES = {
  // 基础路由
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  
  // 账户管理模块
  ACCOUNT: '/account',
  ACCOUNT_USERS: '/account/users',
  ACCOUNT_ROLES: '/account/roles', 
  ACCOUNT_EXCHANGES: '/account/exchanges',
  
  // 交易中心模块
  TRADING: '/trading',
  TRADING_SPOT: '/trading/spot',
  TRADING_ORDERS: '/trading/orders',
  TRADING_POSITIONS: '/trading/positions',
  TRADING_HISTORY: '/trading/history',
  
  // ... 其他模块
} as const;
```

### 2. 路由层次化设计

新的路由结构采用了层次化设计，每个主要功能模块都有自己的根路径和子路径：

- **一级路径**：表示功能模块（如 `/account`、`/trading`、`/strategy`）
- **二级路径**：表示具体功能页面（如 `/account/users`、`/trading/orders`）

这种设计使得：
- URL 结构更加清晰和语义化
- 便于实现面包屑导航
- 支持模块级别的权限控制
- 便于后续功能扩展

## 代码结构说明

### 1. 常量定义结构

```typescript
/**
 * 路由路径常量 - 重新设计的菜单结构
 * 
 * 新的路由结构按功能模块进行分组，提供更清晰的导航层次
 */
export const ROUTES = {
  // 每个模块都有详细的中文注释说明
  // 使用 TypeScript 的 const assertion 确保类型安全
} as const;
```

### 2. 模块分组逻辑

路由按照以下逻辑进行分组：

1. **基础路由**：系统核心功能，如登录、仪表盘
2. **业务模块**：按照量化交易平台的业务流程分组
   - 账户管理：用户和权限相关
   - 交易中心：交易执行相关
   - 策略管理：策略开发和管理
   - 数据分析：数据分析和报告
   - 系统设置：系统管理和配置

### 3. 命名规范

- **模块路径**：使用单数形式，如 `/account`、`/strategy`
- **功能路径**：使用复数形式，如 `/users`、`/orders`
- **常量命名**：使用大写字母和下划线，如 `ACCOUNT_USERS`

## 使用示例

### 1. 在 React Router 中使用

```typescript
import { ROUTES } from '@/constants';
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Routes>
      {/* 基础路由 */}
      <Route path={ROUTES.LOGIN} element={<LoginPage />} />
      <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
      
      {/* 账户管理模块 */}
      <Route path={ROUTES.ACCOUNT} element={<AccountLayout />}>
        <Route path={ROUTES.ACCOUNT_USERS} element={<UserManagement />} />
        <Route path={ROUTES.ACCOUNT_ROLES} element={<RoleManagement />} />
        <Route path={ROUTES.ACCOUNT_EXCHANGES} element={<ExchangeManagement />} />
      </Route>
      
      {/* 交易中心模块 */}
      <Route path={ROUTES.TRADING} element={<TradingLayout />}>
        <Route path={ROUTES.TRADING_SPOT} element={<SpotTrading />} />
        <Route path={ROUTES.TRADING_ORDERS} element={<OrderManagement />} />
        <Route path={ROUTES.TRADING_POSITIONS} element={<PositionManagement />} />
        <Route path={ROUTES.TRADING_HISTORY} element={<TradingHistory />} />
      </Route>
    </Routes>
  );
}
```

### 2. 在导航组件中使用

```typescript
import { ROUTES } from '@/constants';

const navigationItems = [
  {
    key: 'account',
    label: '账户管理',
    path: ROUTES.ACCOUNT,
    children: [
      { key: 'users', label: '用户管理', path: ROUTES.ACCOUNT_USERS },
      { key: 'roles', label: '角色管理', path: ROUTES.ACCOUNT_ROLES },
      { key: 'exchanges', label: '交易所管理', path: ROUTES.ACCOUNT_EXCHANGES },
    ]
  },
  {
    key: 'trading',
    label: '交易中心',
    path: ROUTES.TRADING,
    children: [
      { key: 'spot', label: '现货交易', path: ROUTES.TRADING_SPOT },
      { key: 'orders', label: '订单管理', path: ROUTES.TRADING_ORDERS },
      { key: 'positions', label: '持仓管理', path: ROUTES.TRADING_POSITIONS },
      { key: 'history', label: '交易历史', path: ROUTES.TRADING_HISTORY },
    ]
  }
];
```

### 3. 在权限控制中使用

```typescript
import { ROUTES } from '@/constants';

// 基于路由的权限控制
const routePermissions = {
  [ROUTES.ACCOUNT_USERS]: ['user.view', 'user.manage'],
  [ROUTES.ACCOUNT_ROLES]: ['role.view', 'role.manage'],
  [ROUTES.TRADING_ORDERS]: ['trading.view', 'trading.manage'],
  [ROUTES.STRATEGY_LIST]: ['strategy.view'],
  [ROUTES.STRATEGY_BACKTEST]: ['strategy.backtest'],
};

function checkRoutePermission(route: string, userPermissions: string[]) {
  const requiredPermissions = routePermissions[route] || [];
  return requiredPermissions.some(permission => 
    userPermissions.includes(permission)
  );
}
```

### 4. 面包屑导航实现

```typescript
import { ROUTES } from '@/constants';

const breadcrumbConfig = {
  [ROUTES.ACCOUNT]: [{ label: '账户管理' }],
  [ROUTES.ACCOUNT_USERS]: [
    { label: '账户管理', path: ROUTES.ACCOUNT },
    { label: '用户管理' }
  ],
  [ROUTES.TRADING]: [{ label: '交易中心' }],
  [ROUTES.TRADING_ORDERS]: [
    { label: '交易中心', path: ROUTES.TRADING },
    { label: '订单管理' }
  ],
};

function generateBreadcrumb(currentRoute: string) {
  return breadcrumbConfig[currentRoute] || [];
}
```

## 注意事项

### 1. 迁移注意事项

- **渐进式迁移**：旧路由仍然可用，但建议逐步迁移到新路由
- **重定向处理**：需要在路由配置中添加重定向规则，将旧路由重定向到新路由
- **链接更新**：需要更新所有硬编码的路由链接

### 2. 开发注意事项

- **类型安全**：使用 TypeScript 的 `const assertion` 确保路由常量的类型安全
- **一致性**：所有路由引用都应该使用常量，避免硬编码
- **文档同步**：路由变更时需要同步更新相关文档

### 3. 性能注意事项

- **代码分割**：可以基于新的模块结构实现更精细的代码分割
- **懒加载**：每个模块可以独立进行懒加载，提升首屏加载性能
- **缓存策略**：可以基于模块路径实现更精确的缓存策略

### 4. SEO 和可访问性

- **语义化 URL**：新的路由结构更加语义化，有利于 SEO
- **面包屑导航**：层次化结构便于实现面包屑导航，提升用户体验
- **深度链接**：支持更好的深度链接和书签功能

### 5. 后续扩展建议

- **动态路由**：考虑支持动态路由参数，如 `/trading/orders/:orderId`
- **路由守卫**：基于新的路由结构实现更精细的路由守卫
- **国际化**：路由路径可以考虑支持国际化
- **版本控制**：为 API 路由添加版本控制支持

## 相关文件

- `frontend/src/constants/index.ts` - 路由常量定义
- `frontend/src/router/` - 路由配置文件（需要更新）
- `frontend/src/components/layout/Sidebar.tsx` - 侧边栏导航组件（需要更新）
- `frontend/src/components/layout/Header.tsx` - 头部导航组件（需要更新）

## 后续任务

1. **更新路由配置**：在 React Router 配置中应用新的路由结构
2. **更新导航组件**：修改侧边栏和头部导航组件以使用新的路由结构
3. **添加重定向规则**：为旧路由添加重定向到新路由的规则
4. **更新测试用例**：修改相关的测试用例以适应新的路由结构
5. **文档更新**：更新用户手册和开发文档中的路由相关内容