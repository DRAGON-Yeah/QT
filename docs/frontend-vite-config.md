# QuantTrade 前端 Vite 配置文档

## 变动概述

本次更新为 QuantTrade 前端项目创建了完整的 Vite 配置文件 (`frontend/vite.config.ts`)，该配置文件为 React + TypeScript 项目提供了开发服务器、构建优化、路径别名等完整的配置支持。

## 新增功能说明

### 1. 开发服务器配置

#### 网络配置
- **监听地址**: `0.0.0.0` - 允许外部访问，支持 Docker 容器化开发
- **端口**: `3000` - 标准前端开发端口
- **严格端口**: 启用 `strictPort`，确保 Docker 端口映射的一致性

#### 代理配置
配置了三个关键的代理路由：

```typescript
proxy: {
  '/api': {
    target: 'http://backend:8000',  // Django API 代理
    changeOrigin: true,
    secure: false,
  },
  '/admin': {
    target: 'http://backend:8000',  // Django 管理后台代理
    changeOrigin: true,
    secure: false,
  },
  '/ws': {
    target: 'ws://backend:8000',    // WebSocket 实时数据代理
    ws: true,
    changeOrigin: true,
  },
}
```

### 2. 构建优化配置

#### 分包策略
实现了智能的代码分包，优化加载性能：

- **vendor**: React 核心框架包
- **antd**: Ant Design UI 组件库包
- **charts**: ECharts 图表库包

#### 构建选项
- 输出目录: `dist`
- 生产环境不生成 sourcemap（减小包体积）

### 3. 路径别名系统

配置了完整的路径别名，简化模块导入：

| 别名 | 路径 | 用途 |
|------|------|------|
| `@` | `./src` | 根目录别名 |
| `@components` | `./src/components` | 组件目录 |
| `@pages` | `./src/pages` | 页面目录 |
| `@utils` | `./src/utils` | 工具函数 |
| `@services` | `./src/services` | API 服务 |
| `@types` | `./src/types` | TypeScript 类型 |
| `@assets` | `./src/assets` | 静态资源 |

### 4. CSS 预处理器支持

- 支持 SCSS 预处理器
- 自动导入全局变量文件 `@/styles/variables.scss`

### 5. 环境变量配置

- 环境变量前缀: `REACT_APP_`
- 只有以此前缀开头的变量会暴露给客户端

## 代码结构说明

### 配置文件结构

```
frontend/vite.config.ts
├── 插件配置 (plugins)
├── 开发服务器配置 (server)
│   ├── 网络设置
│   └── 代理配置
├── 构建配置 (build)
│   ├── 输出设置
│   └── 分包策略
├── 模块解析 (resolve)
│   └── 路径别名
├── 环境变量 (envPrefix)
└── CSS 配置 (css)
```

### 关键配置项说明

#### 1. 插件系统
```typescript
plugins: [react()]
```
- 使用官方 React 插件
- 提供 JSX 转换和热重载支持

#### 2. 代理机制
开发环境下的请求流程：
```
前端 (localhost:3000) → Vite 代理 → 后端 (backend:8000)
```

#### 3. 分包优化
```typescript
manualChunks: {
  vendor: ['react', 'react-dom'],      // ~150KB
  antd: ['antd', '@ant-design/icons'], // ~800KB
  charts: ['echarts', 'echarts-for-react'], // ~1MB
}
```

## 使用示例

### 1. 路径别名使用

```typescript
// 使用别名前
import Button from '../../../components/common/Button'
import { formatPrice } from '../../../utils/format'

// 使用别名后
import Button from '@components/common/Button'
import { formatPrice } from '@utils/format'
```

### 2. 环境变量使用

```typescript
// .env 文件
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

// 代码中使用
const apiUrl = import.meta.env.REACT_APP_API_BASE_URL
const wsUrl = import.meta.env.REACT_APP_WS_URL
```

### 3. SCSS 变量使用

```scss
// src/styles/variables.scss
$primary-color: #1890ff;
$success-color: #52c41a;

// 组件样式文件中自动可用
.trading-button {
  background-color: $primary-color;
}
```

## 开发环境启动

### 1. 本地开发
```bash
cd frontend
npm install
npm run dev
```

### 2. Docker 开发
```bash
# 项目根目录
docker-compose up -d
```

访问地址：
- 前端应用: http://localhost:3000
- 后端 API: http://localhost:3000/api (代理)
- 管理后台: http://localhost:3000/admin (代理)

## 生产环境构建

### 1. 构建命令
```bash
npm run build
```

### 2. 构建输出
```
dist/
├── index.html
├── assets/
│   ├── vendor.[hash].js     # React 框架包
│   ├── antd.[hash].js       # UI 组件库包
│   ├── charts.[hash].js     # 图表库包
│   └── index.[hash].js      # 应用代码
└── ...
```

## 注意事项

### 1. Docker 环境配置
- 开发服务器必须监听 `0.0.0.0` 才能在容器中正常访问
- 代理目标使用 Docker 服务名 `backend:8000`

### 2. 代理配置限制
- 代理仅在开发环境生效
- 生产环境需要通过 Nginx 配置反向代理

### 3. 路径别名注意事项
- TypeScript 需要在 `tsconfig.json` 中配置相应的路径映射
- IDE 需要正确识别别名才能提供智能提示

### 4. 环境变量安全
- 只有 `REACT_APP_` 前缀的变量会暴露给客户端
- 敏感信息不应放在客户端环境变量中

### 5. 构建优化建议
- 定期检查分包策略，确保包大小合理
- 监控构建产物大小，避免单个包过大
- 考虑使用 CDN 加载大型第三方库

## 相关文件

- `frontend/package.json` - 项目依赖和脚本配置
- `frontend/tsconfig.json` - TypeScript 配置
- `docker-compose.yml` - Docker 开发环境配置
- `nginx/nginx.conf` - 生产环境反向代理配置

## 后续优化建议

1. **性能监控**: 集成 Bundle Analyzer 分析包大小
2. **缓存策略**: 配置更精细的缓存控制
3. **PWA 支持**: 添加 Service Worker 支持
4. **多环境配置**: 支持测试、预发布等多环境配置
5. **热更新优化**: 配置更精确的热更新范围