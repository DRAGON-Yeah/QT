#!/bin/bash
# QuantTrade 健康检查脚本

set -e

# 配置
BACKEND_URL="http://localhost:8000"
TIMEOUT=30

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查HTTP服务
check_http() {
    local url="$1"
    local name="$2"
    
    echo -n "检查 $name... "
    
    if curl -f -s --max-time $TIMEOUT "$url" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    echo -n "检查数据库连接... "
    
    if docker-compose exec -T db pg_isready -U quanttrade > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 检查Redis连接
check_redis() {
    echo -n "检查Redis连接... "
    
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 检查Celery Worker
check_celery() {
    echo -n "检查Celery Worker... "
    
    if docker-compose exec -T celery celery -A config inspect ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 主健康检查
main() {
    echo "QuantTrade 系统健康检查"
    echo "========================"
    
    local failed=0
    
    # 检查各个组件
    check_http "$BACKEND_URL/health/" "后端API" || failed=$((failed + 1))
    check_http "$BACKEND_URL/admin/" "管理后台" || failed=$((failed + 1))
    check_database || failed=$((failed + 1))
    check_redis || failed=$((failed + 1))
    check_celery || failed=$((failed + 1))
    
    echo ""
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}所有服务运行正常！${NC}"
        exit 0
    else
        echo -e "${RED}发现 $failed 个服务异常${NC}"
        exit 1
    fi
}

# 运行健康检查
main "$@"