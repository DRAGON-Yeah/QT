# Sidebar 图标修复

## 问题描述
前端 Sidebar 组件中使用了不存在的 Ant Design 图标，导致以下错误：
```
Uncaught SyntaxError: The requested module '/node_modules/.vite/deps/@ant-design_icons.js?v=d1a7018f' does not provide an export named 'BrainOutlined'
```

## 问题原因
在 `frontend/src/components/layout/Sidebar.tsx` 中导入和使用了以下不存在的图标：
- `BrainOutlined` - 在 @ant-design/icons v5.2.0 中不存在
- `ShieldOutlined` - 在 @ant-design/icons v5.2.0 中不存在  
- `BriefcaseOutlined` - 在 @ant-design/icons v5.2.0 中不存在

## 修复方案
将不存在的图标替换为可用的图标：

### 修复前
```tsx
import {
  // ...
  BrainOutlined,    // ❌ 不存在
  ShieldOutlined,   // ❌ 不存在
  BriefcaseOutlined, // ❌ 不存在
  // ...
} from '@ant-design/icons';

// 使用不存在的图标
{
  key: 'strategy',
  icon: <BrainOutlined />,  // ❌ 导致错误
  label: '策略管理',
}
```

### 修复后
```tsx
import {
  // ...
  FundOutlined,     // ✅ 存在，适合策略管理
  SafetyOutlined,   // ✅ 存在，适合安全相关功能
  FolderOutlined,   // ✅ 存在，适合文件夹/持仓管理
  // ...
} from '@ant-design/icons';

// 使用正确的图标
{
  key: 'strategy',
  icon: <FundOutlined />,  // ✅ 正确
  label: '策略管理',
}
```

## 图标映射
| 功能 | 原图标 | 新图标 | 说明 |
|------|--------|--------|------|
| 策略管理 | BrainOutlined | FundOutlined | 基金图标更适合策略管理概念 |
| 角色权限 | ShieldOutlined | SafetyOutlined | 安全图标适合权限管理 |
| 持仓管理 | BriefcaseOutlined | FolderOutlined | 文件夹图标适合持仓管理 |

## 验证步骤
1. 清理 Vite 缓存：`rm -rf frontend/node_modules/.vite`
2. 重启开发服务器：`npm run dev`
3. 检查浏览器控制台无图标相关错误
4. 验证侧边栏菜单正常显示

## 预防措施
1. 在使用 Ant Design 图标前，先查看官方文档确认图标是否存在
2. 使用 TypeScript 的类型检查来避免导入不存在的图标
3. 定期更新依赖包并检查 breaking changes

## 相关文件
- `frontend/src/components/layout/Sidebar.tsx` - 主要修复文件
- `frontend/package.json` - 依赖版本信息
- `frontend/vite.config.ts` - Vite 配置

## 修复时间
2024-08-30