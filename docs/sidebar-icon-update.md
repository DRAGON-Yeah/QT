# 侧边栏图标更新说明

## 更新概述

为了与新的菜单结构保持一致，我们更新了侧边栏组件中的图标配置，确保图标语义更加准确，视觉效果更加统一。

## 图标更新详情

### 🔧 修复的图标导入

#### 更新前的问题
- 缺少 BrainOutlined（策略管理需要）
- 使用 BankOutlined 表示策略管理（语义不准确）
- 使用 SafetyOutlined 表示多个不同概念
- 缺少 ExclamationTriangleOutlined（风险警告）
- 使用 ControlOutlined 表示系统配置（不够直观）

#### 更新后的配置
```typescript
import {
  DashboardOutlined,
  UserOutlined,
  LineChartOutlined,
  BrainOutlined,        // ✅ 策略管理 - 更符合"智能"概念
  BarChartOutlined,
  SettingOutlined,
  TeamOutlined,
  ShieldOutlined,       // ✅ 权限和风险控制 - 更符合"保护"概念
  WalletOutlined,
  GoldOutlined,
  UnorderedListOutlined,
  BriefcaseOutlined,    // ✅ 持仓管理 - 更符合"资产管理"概念
  HistoryOutlined,
  AppstoreOutlined,
  ExperimentOutlined,
  EyeOutlined,
  AreaChartOutlined,
  PieChartOutlined,
  ExclamationTriangleOutlined, // ✅ 风险分析 - 更符合"警告"概念
  FileTextOutlined,
  MenuOutlined,
  DesktopOutlined,
  DatabaseOutlined,
  FileOutlined,
  SlidersOutlined,      // ✅ 系统配置 - 更符合"设置"概念
} from '@ant-design/icons';
```