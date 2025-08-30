#!/bin/bash
# QuantTrade 项目初始化脚本

set -e

echo "🚀 开始初始化 QuantTrade 项目..."

# 检查必要的工具
echo "📋 检查系统环境..."

# 检查 Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 未安装，请先安装 Python 3.12"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✅ 系统环境检查通过"

# 复制环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件并填入实际配置值"
fi

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p logs
mkdir -p backups
mkdir -p nginx/ssl

# 设置后端环境
echo "🐍 设置后端环境..."
cd backend

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    python3.12 -m venv .venv
fi

# 激活虚拟环境并安装依赖
source .venv/bin/activate
pip install --upgrade pip

if [ -f "requirements/development.txt" ]; then
    pip install -r requirements/development.txt
else
    echo "⚠️  后端依赖文件不存在，请先完成后端项目搭建"
fi

cd ..

# 设置前端环境
echo "⚛️  设置前端环境..."
cd frontend

if [ -f "package.json" ]; then
    npm install
else
    echo "⚠️  前端项目不存在，请先完成前端项目搭建"
fi

cd ..

echo "✅ QuantTrade 项目初始化完成！"
echo ""
echo "📖 下一步操作："
echo "1. 编辑 .env 文件配置环境变量"
echo "2. 运行 'docker-compose up -d' 启动开发环境"
echo "3. 访问 http://localhost:3000 查看前端"
echo "4. 访问 http://localhost:8000 查看后端API"