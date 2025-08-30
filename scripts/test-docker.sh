#!/bin/bash
# QuantTrade Docker配置测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}QuantTrade Docker配置测试${NC}"
echo "================================"

# 检查Docker和Docker Compose
echo -e "${YELLOW}检查Docker环境...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker未安装${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker已安装: $(docker --version)${NC}"
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose未安装${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker Compose已安装: $(docker-compose --version)${NC}"
fi

# 检查Docker服务状态
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker服务未运行${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker服务正常运行${NC}"
fi

# 验证Docker Compose配置文件
echo ""
echo -e "${YELLOW}验证Docker Compose配置文件...${NC}"

if docker-compose config &> /dev/null; then
    echo -e "${GREEN}✓ docker-compose.yml 配置有效${NC}"
else
    echo -e "${RED}✗ docker-compose.yml 配置无效${NC}"
    docker-compose config
    exit 1
fi

if docker-compose -f docker-compose.prod.yml config &> /dev/null; then
    echo -e "${GREEN}✓ docker-compose.prod.yml 配置有效${NC}"
else
    echo -e "${RED}✗ docker-compose.prod.yml 配置无效${NC}"
    docker-compose -f docker-compose.prod.yml config
    exit 1
fi

# 检查Dockerfile文件
echo ""
echo -e "${YELLOW}检查Dockerfile文件...${NC}"

dockerfiles=(
    "backend/Dockerfile.dev"
    "backend/Dockerfile.prod"
    "frontend/Dockerfile.dev"
    "frontend/Dockerfile.prod"
)

for dockerfile in "${dockerfiles[@]}"; do
    if [ -f "$dockerfile" ]; then
        echo -e "${GREEN}✓ $dockerfile 存在${NC}"
    else
        echo -e "${RED}✗ $dockerfile 不存在${NC}"
        exit 1
    fi
done

# 检查环境变量文件
echo ""
echo -e "${YELLOW}检查环境变量文件...${NC}"

if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓ .env.example 存在${NC}"
else
    echo -e "${RED}✗ .env.example 不存在${NC}"
fi

if [ -f ".env.prod.example" ]; then
    echo -e "${GREEN}✓ .env.prod.example 存在${NC}"
else
    echo -e "${RED}✗ .env.prod.example 不存在${NC}"
fi

if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env 存在${NC}"
else
    echo -e "${YELLOW}! .env 不存在，将从示例文件创建${NC}"
    cp .env.example .env
fi

# 检查必要的目录
echo ""
echo -e "${YELLOW}检查必要的目录...${NC}"

directories=(
    "logs"
    "backups"
    "nginx/ssl"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir 目录存在${NC}"
    else
        echo -e "${YELLOW}! $dir 目录不存在，正在创建...${NC}"
        mkdir -p "$dir"
        echo -e "${GREEN}✓ $dir 目录已创建${NC}"
    fi
done

# 测试镜像构建
echo ""
echo -e "${YELLOW}测试镜像构建...${NC}"

echo "构建后端开发镜像..."
if docker build -f backend/Dockerfile.dev -t quanttrade-backend-dev backend/ &> /dev/null; then
    echo -e "${GREEN}✓ 后端开发镜像构建成功${NC}"
else
    echo -e "${RED}✗ 后端开发镜像构建失败${NC}"
    exit 1
fi

echo "构建前端开发镜像..."
if docker build -f frontend/Dockerfile.dev -t quanttrade-frontend-dev frontend/ &> /dev/null; then
    echo -e "${GREEN}✓ 前端开发镜像构建成功${NC}"
else
    echo -e "${RED}✗ 前端开发镜像构建失败${NC}"
    exit 1
fi

# 清理测试镜像
echo ""
echo -e "${YELLOW}清理测试镜像...${NC}"
docker rmi quanttrade-backend-dev quanttrade-frontend-dev &> /dev/null || true
echo -e "${GREEN}✓ 测试镜像已清理${NC}"

# 检查网络配置
echo ""
echo -e "${YELLOW}检查网络配置...${NC}"

# 创建测试网络
if docker network create quanttrade_test_network &> /dev/null; then
    echo -e "${GREEN}✓ 网络创建测试成功${NC}"
    docker network rm quanttrade_test_network &> /dev/null
else
    echo -e "${YELLOW}! 网络可能已存在${NC}"
fi

# 检查端口可用性
echo ""
echo -e "${YELLOW}检查端口可用性...${NC}"

ports=(3000 8000 5432 6379)

for port in "${ports[@]}"; do
    if netstat -tuln 2>/dev/null | grep ":$port " &> /dev/null; then
        echo -e "${YELLOW}! 端口 $port 已被占用${NC}"
    else
        echo -e "${GREEN}✓ 端口 $port 可用${NC}"
    fi
done

# 生成SSL证书（如果不存在）
echo ""
echo -e "${YELLOW}检查SSL证书...${NC}"

if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo -e "${YELLOW}生成自签名SSL证书...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=QuantTrade/CN=localhost" &> /dev/null
    
    chmod 600 nginx/ssl/key.pem
    chmod 644 nginx/ssl/cert.pem
    echo -e "${GREEN}✓ SSL证书已生成${NC}"
else
    echo -e "${GREEN}✓ SSL证书已存在${NC}"
fi

# 最终报告
echo ""
echo -e "${BLUE}测试完成！${NC}"
echo "================================"
echo -e "${GREEN}✓ Docker环境配置正确${NC}"
echo ""
echo "下一步操作："
echo "1. 启动开发环境: make dev-up"
echo "2. 查看服务状态: make status"
echo "3. 查看日志: make dev-logs"
echo "4. 进入后端容器: make dev-shell"
echo ""
echo "更多命令请运行: make help"