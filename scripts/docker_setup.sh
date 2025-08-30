#!/bin/bash
# Docker环境设置脚本

set -e

echo "🐳 设置Docker环境..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p backups
mkdir -p nginx/ssl

# 生成自签名SSL证书（仅用于开发）
if [ ! -f "nginx/ssl/cert.pem" ]; then
    echo "🔐 生成自签名SSL证书..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=QuantTrade/CN=localhost"
    echo "✅ SSL证书生成完成"
fi

# 创建环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -base64 32)
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    DB_PASSWORD=$(openssl rand -base64 16)
    REDIS_PASSWORD=$(openssl rand -base64 16)
    
    # 更新.env文件
    sed -i.bak "s/your-secret-key-here/$SECRET_KEY/" .env
    sed -i.bak "s/your-encryption-key-here/$ENCRYPTION_KEY/" .env
    sed -i.bak "s/your-database-password/$DB_PASSWORD/" .env
    sed -i.bak "s/your-redis-password/$REDIS_PASSWORD/" .env
    
    rm .env.bak
    echo "✅ 环境变量文件创建完成"
fi

# 构建Docker镜像
echo "🔨 构建Docker镜像..."
docker-compose build

echo "✅ Docker环境设置完成！"
echo ""
echo "📖 下一步操作："
echo "1. 编辑 .env 文件配置具体参数"
echo "2. 运行 'docker-compose up -d' 启动服务"
echo "3. 运行 'docker-compose exec backend python manage.py migrate' 初始化数据库"
echo "4. 运行 'docker-compose exec backend python scripts/init_db.py' 创建初始数据"