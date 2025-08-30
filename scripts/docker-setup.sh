#!/bin/bash
# QuantTrade Docker环境设置脚本

set -e

echo "开始设置QuantTrade Docker环境..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p logs
mkdir -p backups
mkdir -p nginx/ssl

# 检查环境变量文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}创建环境变量文件...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}请编辑 .env 文件并填入实际的配置值${NC}"
fi

# 创建Docker网络
echo -e "${YELLOW}创建Docker网络...${NC}"
docker network create quanttrade_network 2>/dev/null || echo "网络已存在"

# 生成自签名SSL证书（仅用于开发环境）
if [ ! -f nginx/ssl/cert.pem ]; then
    echo -e "${YELLOW}生成自签名SSL证书（仅用于开发）...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=QuantTrade/CN=localhost"
fi

# 设置文件权限
echo -e "${YELLOW}设置文件权限...${NC}"
chmod +x scripts/*.sh
chmod 600 nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem

echo -e "${GREEN}Docker环境设置完成！${NC}"
echo ""
echo "使用以下命令启动服务："
echo "  开发环境: docker-compose up -d"
echo "  生产环境: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "首次启动后，请运行数据库迁移："
echo "  docker-compose exec backend python manage.py migrate"
echo "  docker-compose exec backend python manage.py createsuperuser"