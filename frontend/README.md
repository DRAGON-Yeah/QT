# QuantTrade 前端项目

基于 React + TypeScript + Vite 构建的现代化量化交易平台前端应用。

## 项目结构

```
src/
├── components/          # 组件库
│   ├── ui/             # 基础UI组件
│   │   ├── Button/     # 按钮组件
│   │   ├── Input/      # 输入框组件
│   │   ├── Card/       # 卡片组件
│   │   └── Table/      # 表格组件
│   ├── layout/         # 布局组件
│   │   ├── Layout.tsx  # 主布局
│   │   ├── Sidebar.tsx # 侧边栏
│   │   └── Header.tsx  # 顶部导航
│   ├── auth/           # 认证组件
│   └── providers/      # 提供者组件
├── pages/              # 页面组件
│   ├── Login/          # 登录页面
│   ├── Dashboard/      # 仪表盘
│   ├── Exchanges/      # 交易所管理
│   ├── Trading/        # 交易执行
│   ├── Strategies/     # 策略管理
│   ├── Market/         # 市场数据
│   ├── Risk/           # 风险控制
│   ├── System/         # 系统管理
│   └── Profile/        # 个人中心
├── store/              # 状态管理
│   ├── auth.ts         # 认证状态
│   ├── theme.ts        # 主题状态
│   └── app.ts          # 应用状态
├── hooks/              # 自定义Hooks
├── utils/              # 工具函数
├── types/              # TypeScript类型定义
├── constants/          # 常量定义
├── styles/             # 全局样式
├── router/             # 路由配置
└── test/               # 测试配置
```

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Ant Design 5
- **状态管理**: Zustand
- **路由**: React Router 6
- **数据请求**: TanStack Query
- **样式**: SCSS + CSS Modules
- **测试**: Vitest + Testing Library

## 核心特性

### 响应式设计
- 支持桌面端 (≥1200px)、平板端 (768px-1199px)、移动端 (<768px)
- 自适应布局和组件

### 主题系统
- 支持亮色/暗色主题切换
- 可自定义主色调、边框圆角、字体大小
- CSS变量动态更新

### 多租户架构
- 基于JWT的用户认证
- 租户数据隔离
- RBAC权限控制

### 基础组件库
- 统一的设计规范
- 完整的TypeScript类型支持
- 响应式适配
- 单元测试覆盖

## 开发指南

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 运行测试
```bash
npm run test
```

### 类型检查
```bash
npm run type-check
```

### 代码规范检查
```bash
npm run lint
```

## 设计规范

### 色彩系统
- 主色调: #1890FF (科技蓝)
- 成功色: #52C41A (绿色)
- 警告色: #FAAD14 (橙色)
- 错误色: #F5222D (红色)
- 上涨色: #52C41A (绿色)
- 下跌色: #F5222D (红色)

### 字体规范
- 主标题: 24px, 字重600
- 次标题: 20px, 字重600
- 小标题: 16px, 字重500
- 正文: 14px, 字重400
- 辅助文字: 12px, 字重400

### 间距规范
- 页面边距: 24px
- 组件间距: 16px
- 元素间距: 8px
- 内容间距: 4px

## 开发规范

### 组件开发
1. 使用函数式组件 + Hooks
2. 完整的TypeScript类型定义
3. 响应式设计适配
4. 单元测试覆盖

### 样式规范
1. 使用SCSS预处理器
2. 遵循BEM命名规范
3. 使用CSS变量支持主题切换
4. 移动端优先的响应式设计

### 状态管理
1. 使用Zustand进行状态管理
2. 按功能模块划分store
3. 支持持久化存储

### 路由管理
1. 使用React Router 6
2. 懒加载页面组件
3. 路由守卫保护

## 任务进度

- [x] 10.1 搭建React前端项目架构和基础组件
- [ ] 10.2 开发登录页面和主界面导航
- [ ] 10.3 开发仪表盘和个人中心页面
- [ ] 10.4 开发交易所账户管理界面
- [ ] 10.5 开发策略管理和回测界面
- [ ] 10.6 开发交易执行和订单管理界面
- [ ] 10.7 开发市场数据分析界面
- [ ] 10.8 开发风险控制和系统管理界面
- [ ] 10.9 实现WebSocket实时数据更新和交互优化