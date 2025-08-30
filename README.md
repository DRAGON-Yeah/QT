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

- **多租户架构**: 每个用户拥有独立的数据空间
- **用户管理**: 基于RBAC的权限管理系统
- **交易所集成**: 支持币安、欧易等主流交易所
- **策略开发**: 完整的策略开发、回测、执行工具链
- **风险控制**: 实时风险监控和预警系统
- **市场数据**: 实时行情数据和技术指标分析
- **系统监控**: 完整的系统监控和运维管理

## 开发指南

- [API文档](docs/api/)
- [部署指南](docs/deployment/)
- [用户指南](docs/user-guide/)

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 联系我们

如有问题或建议，请通过以下方式联系我们：
- 邮箱: support@quanttrade.com
- 文档: [项目文档](docs/)