# QuantTrade Python虚拟环境配置指南

## 概述
QuantTrade项目使用Python 3.12和虚拟环境(.venv)来管理依赖包，确保开发环境的隔离性和一致性。

## 环境要求
- **Python版本**：3.12.x (推荐3.12.0+)
- **操作系统**：Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **包管理器**：pip (Python内置)

## 虚拟环境配置步骤

### 1. 检查Python版本
```bash
# 检查Python版本
python3 --version
# 或
python --version

# 确保版本为3.12.x
```

### 2. 创建虚拟环境
```bash
# 进入项目根目录
cd QuantTrade

# 创建虚拟环境
python3.12 -m venv .venv

# 验证虚拟环境创建成功
ls -la .venv/
```

### 3. 激活虚拟环境
```bash
# Unix/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 验证激活成功 (命令提示符前应显示(.venv))
which python
# 或
where python
```

### 4. 升级pip
```bash
# 确保虚拟环境已激活
pip install --upgrade pip
```

### 5. 安装依赖包
```bash
# 安装生产环境依赖
pip install -r requirements.txt

# 或安装开发环境依赖
pip install -r requirements-dev.txt
```

### 6. 验证安装
```bash
# 查看已安装的包
pip list

# 测试Django安装
python -c "import django; print(django.get_version())"
```

## 虚拟环境管理

### 激活虚拟环境
```bash
# 每次开发前都需要激活
source .venv/bin/activate  # Unix/macOS
# 或
.venv\Scripts\activate     # Windows
```

### 退出虚拟环境
```bash
deactivate
```

### 查看虚拟环境信息
```bash
# 查看Python路径
which python

# 查看已安装的包
pip list

# 查看包依赖关系
pip show django
```

### 更新依赖包
```bash
# 更新所有包到最新版本
pip install --upgrade -r requirements.txt

# 更新特定包
pip install --upgrade django
```

### 导出依赖列表
```bash
# 导出当前环境的所有包
pip freeze > requirements-current.txt

# 导出特定包的依赖
pip show django
```

## 开发工具配置

### VS Code配置
1. 打开项目文件夹
2. 按`Ctrl+Shift+P` (Windows/Linux) 或 `Cmd+Shift+P` (macOS)
3. 输入"Python: Select Interpreter"
4. 选择`.venv/bin/python`路径

### PyCharm配置
1. 打开项目设置 (File > Settings)
2. 选择Project > Python Interpreter
3. 点击齿轮图标 > Add
4. 选择"Existing Environment"
5. 选择`.venv/bin/python`路径

### Jupyter Notebook配置
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装ipykernel
pip install ipykernel

# 注册虚拟环境到Jupyter
python -m ipykernel install --user --name=quanttrade --display-name="QuantTrade Python 3.12"
```

## 常见问题解决

### 虚拟环境激活失败
```bash
# 检查虚拟环境是否存在
ls -la .venv/

# 重新创建虚拟环境
rm -rf .venv
python3.12 -m venv .venv
```

### 依赖包安装失败
```bash
# 升级pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 版本冲突
```bash
# 查看冲突的包
pip check

# 卸载冲突的包
pip uninstall package-name

# 重新安装
pip install package-name==version
```

### 权限问题
```bash
# Unix/macOS: 使用sudo
sudo python3.12 -m venv .venv

# Windows: 以管理员身份运行命令提示符
```

## 最佳实践

### 1. 环境隔离
- 每个项目使用独立的虚拟环境
- 不要在生产环境中使用开发依赖
- 定期清理未使用的包

### 2. 依赖管理
- 使用requirements.txt管理生产依赖
- 使用requirements-dev.txt管理开发依赖
- 定期更新依赖包版本

### 3. 版本控制
- 将.venv/添加到.gitignore
- 提交requirements.txt和requirements-dev.txt
- 记录Python版本要求

### 4. 团队协作
- 统一Python版本要求
- 使用相同的虚拟环境名称(.venv)
- 共享依赖包版本要求

## 生产环境部署

### Docker部署
```dockerfile
# 在Dockerfile中使用虚拟环境
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN python -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

COPY . .
CMD [".venv/bin/python", "manage.py", "runserver"]
```

### 服务器部署
```bash
# 在服务器上创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 使用gunicorn启动
.venv/bin/gunicorn --bind 0.0.0.0:8000 wsgi:application
```

## 总结
通过使用Python虚拟环境(.venv)，QuantTrade项目能够：
- 🚀 确保开发环境的一致性
- 🛡️ 避免依赖包版本冲突
- 🔄 支持多项目并行开发
- 📦 简化依赖包管理
- 🐳 支持容器化部署

遵循本指南配置虚拟环境，将确保开发过程的顺利进行和项目的成功部署。
