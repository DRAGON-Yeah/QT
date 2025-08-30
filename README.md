# QuantTrade 量化交易平台

## 项目概述

QuantTrade 是一个基于 Django（后端）和 React（前端）构建的多租户量化交易平台，旨在为个人量化交易者、机构投资者和量化策略开发者提供完整的数字货币量化交易解决方案。

## 项目结构

```
QuantTrade/
├── backend/                 # Django后端项目
│   ├── config/             # Django配置
│   ├── apps/               # Django应用模块
│   ├── requirements/       # 依赖文件
│   ├── .venv/             # Python虚拟环境
│   └── manage.py          # Django管理脚本
├── frontend/               # React前端项目
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   ├── package.json       # 前端依赖
│   └── node_modules/      # 前端依赖包
├── docs/                   # 项目文档
│   ├── api/               # API文档
│   ├── deployment/        # 部署文档
│   └── user-guide/        # 用户指南
├── scripts/                # 部署和运维脚本
│   ├── deploy/            # 部署脚本
│   ├── backup/            # 备份脚本
│   └── monitoring/        # 监控脚本
├── docker-compose.yml      # Docker编排文件
├── docker-compose.prod.yml # 生产环境Docker编排
└── README.md              # 项目说明
```

## 技术栈

### 后端技术
- **框架**: Django 4.2 + Django REST Framework
- **语言**: Python 3.12
- **数据库**: SQLite (开发) / MySQL (生产)
- **缓存**: Redis
- **任务队列**: Celery + Redis
- **交易所集成**: CCXT

### 前端技术
- **框架**: React 18 + TypeScript
- **状态管理**: React Context / Redux
- **UI组件**: Ant Design
- **图表库**: ECharts / TradingView
- **构建工具**: Vite

### 部署技术
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **进程管理**: Supervisor
- **监控**: Prometheus + Grafana

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Redis
- MySQL (生产环境)

### 后端开发环境设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements/development.txt

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

### 前端开发环境设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Docker 快速启动

```bash
# 启动开发环境
docker-compose up -d

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## 核心功能

### 🏠 仪表盘
- **系统概览**: 关键指标展示和快速操作入口
- **实时监控**: 交易状态、策略运行状态、系统健康度

### 👥 账户管理
- **用户管理**: 用户创建、编辑、状态管理（仅管理员可创建用户）
- **角色权限**: 基于RBAC的细粒度权限控制
- **交易账户**: 交易所API密钥管理和账户配置

### 📈 交易中心
- **现货交易**: 实时交易界面，支持市价单、限价单
- **订单管理**: 当前订单、历史订单、订单状态跟踪
- **持仓管理**: 当前持仓分析和平仓操作
- **交易历史**: 成交记录统计和数据导出

### 🧠 策略管理
- **策略列表**: 策略库管理、策略创建和编辑
- **策略回测**: 历史数据回测、回测报告、参数优化
- **策略监控**: 实时策略监控、性能指标跟踪
- **风险控制**: 风险参数设置、止损止盈、仓位控制

### 📊 数据分析
- **市场行情**: 实时行情数据、K线图表、技术指标
- **收益分析**: 收益曲线、收益统计、基准对比
- **风险分析**: 风险指标计算、回撤分析、风险预警
- **报表中心**: 日报、周报、月报、自定义报表生成

### ⚙️ 系统设置
- **菜单管理**: 动态菜单配置、权限设置、菜单排序
- **系统监控**: 系统状态监控、性能指标、告警管理
- **数据库管理**: 数据备份、恢复、清理和优化
- **系统日志**: 操作日志、错误日志、审计日志查看
- **系统配置**: 系统参数配置、邮件设置、安全配置

## 开发指南

### 文档目录
- [菜单结构设计](docs/menu-structure-redesign.md) - 新的二级菜单结构设计
- [菜单迁移指南](docs/menu-migration-guide.md) - 从旧结构迁移到新结构
- [多租户架构](docs/core-models-architecture.md) - 多租户系统架构设计
- [JWT认证实现](docs/jwt-authentication-implementation.md) - 身份认证系统
- [Docker部署](docs/DOCKER.md) - 容器化部署指南
- [错误处理改进](docs/error-handling-improvement.md) - 错误处理机制

### 开发规范
- [技术标准](docs/technical-standards.md) - 技术选型和开发标准
- [安全指南](docs/security-guidelines.md) - 安全开发最佳实践
- [测试策略](docs/testing-strategy.md) - 测试框架和质量保证
- [UI设计标准](docs/ui-design-standards.md) - 界面设计规范

### 集成指南
- [交易所集成](docs/trading-integration.md) - CCXT框架使用指南
- [部署指南](docs/deployment-guide.md) - 生产环境部署
- [项目概览](docs/project-overview.md) - 项目整体介绍

## 菜单结构

系统采用清晰的二级菜单结构，提供直观的功能导航：

```
QuantTrade 菜单结构
├── 🏠 仪表盘                    # 系统概览和快速操作
├── 👥 账户管理                  # 用户和权限管理
│   ├── 用户管理                # 用户列表和管理
│   ├── 角色权限                # 角色和权限配置
│   └── 交易账户                # 交易所账户管理
├── 📈 交易中心                  # 交易功能集合
│   ├── 现货交易                # 实时交易界面
│   ├── 订单管理                # 订单状态跟踪
│   ├── 持仓管理                # 持仓分析管理
│   └── 交易历史                # 历史交易记录
├── 🧠 策略管理                  # 量化策略相关
│   ├── 策略列表                # 策略库管理
│   ├── 策略回测                # 历史数据回测
│   ├── 策略监控                # 实时策略监控
│   └── 风险控制                # 风险参数设置
├── 📊 数据分析                  # 数据分析工具
│   ├── 市场行情                # 实时行情数据
│   ├── 收益分析                # 收益统计分析
│   ├── 风险分析                # 风险指标分析
│   └── 报表中心                # 报表生成导出
└── ⚙️ 系统设置                  # 系统管理功能
    ├── 菜单管理                # 动态菜单配置
    ├── 系统监控                # 系统状态监控
    ├── 数据库管理              # 数据库运维
    ├── 系统日志                # 日志查看分析
    └── 系统配置                # 系统参数配置
```

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 联系我们

如有问题或建议，请通过以下方式联系我们：
- 邮箱: support@quanttrade.com
- 文档: [项目文档](docs/)