# QuantTrade Django 管理工具文档 (manage.py)

## 变动概述

本次变动创建了 QuantTrade 量化交易平台的核心 Django 管理工具文件 `manage.py`。这是 Django 项目的标准入口文件，用于执行各种项目管理任务。

## 新增功能说明

### 1. Django 项目管理入口
- **文件路径**: `manage.py`
- **功能**: 提供 Django 项目的命令行管理接口
- **配置**: 默认使用开发环境配置 (`config.settings.development`)

### 2. 主要功能特性

#### 环境配置管理
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
```
- 自动设置开发环境为默认配置
- 支持通过环境变量覆盖配置模块
- 确保开发过程中使用正确的配置文件

#### 错误处理机制
```python
except ImportError as exc:
    raise ImportError(
        "无法导入 Django。请确保 Django 已正确安装并且在 PYTHONPATH 环境变量中可用。"
        "您是否忘记激活虚拟环境？"
    ) from exc
```
- 提供友好的中文错误提示
- 帮助开发者快速定位环境配置问题
- 引导用户检查虚拟环境和 Django 安装状态

## 代码结构说明

### 文件组织
```
manage.py
├── 导入模块 (os, sys)
├── main() 函数
│   ├── 环境配置设置
│   ├── Django 导入和异常处理
│   └── 命令行执行
└── 脚本入口点
```

### 核心函数分析

#### `main()` 函数
- **作用**: Django 管理任务的主入口函数
- **职责**: 
  - 配置环境变量
  - 导入 Django 管理工具
  - 执行命令行参数
- **异常处理**: 捕获 ImportError 并提供详细错误信息

## 使用示例

### 基本命令使用

#### 1. 启动开发服务器
```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动开发服务器
python manage.py runserver

# 指定端口启动
python manage.py runserver 8080

# 指定 IP 和端口
python manage.py runserver 0.0.0.0:8000
```

#### 2. 数据库管理
```bash
# 创建数据库迁移文件
python manage.py makemigrations

# 执行数据库迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations

# 回滚迁移
python manage.py migrate app_name 0001
```

#### 3. 用户管理
```bash
# 创建超级用户
python manage.py createsuperuser

# 修改用户密码
python manage.py changepassword username
```

#### 4. 静态文件管理
```bash
# 收集静态文件
python manage.py collectstatic

# 查找静态文件
python manage.py findstatic filename.css
```

#### 5. 测试相关
```bash
# 运行所有测试
python manage.py test

# 运行特定应用的测试
python manage.py test apps.trading

# 运行特定测试类
python manage.py test apps.trading.tests.TestOrderModel
```

#### 6. 数据管理
```bash
# 导出数据
python manage.py dumpdata > data.json

# 导入数据
python manage.py loaddata data.json

# 清空数据库
python manage.py flush
```

### 环境配置示例

#### 开发环境使用
```bash
# 默认使用开发环境配置
python manage.py runserver
```

#### 生产环境使用
```bash
# 设置生产环境配置
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py runserver

# 或者直接指定
python manage.py runserver --settings=config.settings.production
```

#### 测试环境使用
```bash
# 使用测试环境配置
python manage.py test --settings=config.settings.test
```

## 注意事项

### 1. 虚拟环境要求
- **必须激活**: 使用前必须激活 Python 虚拟环境 (`.venv`)
- **Python 版本**: 确保使用 Python 3.12.x
- **依赖安装**: 确保已安装 `requirements.txt` 中的所有依赖

### 2. 配置文件结构
```
config/
├── __init__.py
├── settings/
│   ├── __init__.py
│   ├── base.py          # 基础配置
│   ├── development.py   # 开发环境配置 (默认)
│   ├── production.py    # 生产环境配置
│   └── test.py         # 测试环境配置
├── urls.py
└── wsgi.py
```

### 3. 环境变量配置
```bash
# .env 文件示例
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
```

### 4. 常见问题解决

#### Django 导入错误
```bash
# 错误信息: "Couldn't import Django"
# 解决方案:
source .venv/bin/activate  # 激活虚拟环境
pip install -r requirements.txt  # 安装依赖
```

#### 配置模块未找到
```bash
# 错误信息: "No module named 'config.settings.development'"
# 解决方案:
# 1. 确保 config 目录存在
# 2. 确保 __init__.py 文件存在
# 3. 检查配置文件路径
```

#### 数据库连接错误
```bash
# 解决方案:
python manage.py migrate  # 创建数据库表
# 或检查数据库配置
```

### 5. 安全注意事项
- **生产环境**: 不要在生产环境中使用开发配置
- **密钥管理**: 确保 SECRET_KEY 在生产环境中安全存储
- **调试模式**: 生产环境必须设置 `DEBUG=False`
- **允许主机**: 正确配置 `ALLOWED_HOSTS`

### 6. 性能优化建议
- **静态文件**: 生产环境使用 `collectstatic` 收集静态文件
- **数据库**: 定期执行数据库优化和备份
- **缓存**: 配置 Redis 缓存提高性能
- **日志**: 合理配置日志级别和轮转

## 相关文件

- `config/settings/development.py` - 开发环境配置
- `config/settings/production.py` - 生产环境配置  
- `config/settings/test.py` - 测试环境配置
- `requirements.txt` - Python 依赖包列表
- `.env` - 环境变量配置文件

## 下一步操作

1. **创建配置文件结构**: 建立 `config/settings/` 目录和相关配置文件
2. **安装依赖包**: 创建并安装 `requirements.txt` 中的依赖
3. **数据库配置**: 配置数据库连接和执行初始迁移
4. **创建应用**: 使用 `python manage.py startapp` 创建 Django 应用
5. **配置 URL 路由**: 设置项目的 URL 配置

这个 `manage.py` 文件是 QuantTrade 项目的重要基础，为后续的开发工作提供了标准的 Django 管理接口。