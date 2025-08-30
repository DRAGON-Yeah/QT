#!/bin/bash
# QuantTrade 生产环境管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置文件
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

# 显示帮助信息
show_help() {
    echo "QuantTrade 生产环境管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  deploy    部署生产环境"
    echo "  start     启动生产环境"
    echo "  stop      停止生产环境"
    echo "  restart   重启生产环境"
    echo "  logs      查看日志"
    echo "  backup    备份数据库"
    echo "  restore   恢复数据库"
    echo "  update    更新应用"
    echo "  scale     扩缩容服务"
    echo "  status    查看服务状态"
    echo "  health    健康检查"
    echo "  help      显示此帮助信息"
}

# 检查生产环境配置
check_prod_config() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}错误: 生产环境配置文件 $ENV_FILE 不存在${NC}"
        echo "请创建生产环境配置文件并填入正确的值"
        exit 1
    fi
    
    # 检查关键配置项
    source "$ENV_FILE"
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here" ]; then
        echo -e "${RED}错误: 请设置正确的 SECRET_KEY${NC}"
        exit 1
    fi
    
    if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "your-database-password" ]; then
        echo -e "${RED}错误: 请设置正确的 DB_PASSWORD${NC}"
        exit 1
    fi
}

# 部署生产环境
deploy_prod() {
    echo -e "${YELLOW}部署QuantTrade生产环境...${NC}"
    
    check_prod_config
    
    # 创建必要的目录
    mkdir -p logs backups nginx/ssl
    
    # 拉取最新镜像
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # 构建镜像
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
    
    # 启动服务
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # 等待服务启动
    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 30
    
    # 执行数据库迁移
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec backend python manage.py migrate --settings=config.settings.production
    
    # 收集静态文件
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec backend python manage.py collectstatic --noinput --settings=config.settings.production
    
    echo -e "${GREEN}生产环境部署完成！${NC}"
}

# 启动生产环境
start_prod() {
    echo -e "${YELLOW}启动QuantTrade生产环境...${NC}"
    check_prod_config
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    echo -e "${GREEN}生产环境启动完成${NC}"
}

# 停止生产环境
stop_prod() {
    echo -e "${YELLOW}停止QuantTrade生产环境...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    echo -e "${GREEN}生产环境已停止${NC}"
}

# 重启生产环境
restart_prod() {
    echo -e "${YELLOW}重启QuantTrade生产环境...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
    echo -e "${GREEN}生产环境已重启${NC}"
}

# 查看日志
show_logs() {
    if [ -n "$2" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "$2"
    else
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
    fi
}

# 备份数据库
backup_database() {
    echo -e "${YELLOW}备份数据库...${NC}"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="backups/quanttrade_backup_$TIMESTAMP.sql"
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec db pg_dump -U quanttrade quanttrade > "$BACKUP_FILE"
    
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    
    echo -e "${GREEN}数据库备份完成: ${BACKUP_FILE}.gz${NC}"
    
    # 清理7天前的备份
    find backups/ -name "quanttrade_backup_*.sql.gz" -mtime +7 -delete
}

# 恢复数据库
restore_database() {
    if [ -z "$2" ]; then
        echo -e "${RED}错误: 请指定备份文件${NC}"
        echo "用法: $0 restore <backup_file>"
        exit 1
    fi
    
    BACKUP_FILE="$2"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}错误: 备份文件不存在: $BACKUP_FILE${NC}"
        exit 1
    fi
    
    echo -e "${RED}警告: 这将覆盖当前数据库！${NC}"
    read -p "确定要继续吗? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}恢复数据库...${NC}"
        
        # 如果是压缩文件，先解压
        if [[ "$BACKUP_FILE" == *.gz ]]; then
            gunzip -c "$BACKUP_FILE" | docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -U quanttrade quanttrade
        else
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db psql -U quanttrade quanttrade < "$BACKUP_FILE"
        fi
        
        echo -e "${GREEN}数据库恢复完成${NC}"
    fi
}

# 更新应用
update_app() {
    echo -e "${YELLOW}更新QuantTrade应用...${NC}"
    
    # 备份数据库
    backup_database
    
    # 拉取最新代码
    git pull origin main
    
    # 重新构建镜像
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    
    # 滚动更新
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # 执行迁移
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec backend python manage.py migrate --settings=config.settings.production
    
    echo -e "${GREEN}应用更新完成${NC}"
}

# 扩缩容服务
scale_service() {
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo -e "${RED}错误: 请指定服务名和副本数${NC}"
        echo "用法: $0 scale <service> <replicas>"
        echo "可用服务: backend, celery"
        exit 1
    fi
    
    SERVICE="$2"
    REPLICAS="$3"
    
    echo -e "${YELLOW}扩缩容服务 $SERVICE 到 $REPLICAS 个副本...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --scale "$SERVICE=$REPLICAS"
    echo -e "${GREEN}服务扩缩容完成${NC}"
}

# 查看服务状态
show_status() {
    echo -e "${BLUE}QuantTrade 生产环境状态:${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
}

# 健康检查
health_check() {
    echo -e "${BLUE}QuantTrade 健康检查:${NC}"
    
    # 检查服务状态
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    # 检查应用健康状态
    echo ""
    echo "应用健康检查:"
    if curl -f -s http://localhost/health/ > /dev/null; then
        echo -e "${GREEN}✓ 应用健康${NC}"
    else
        echo -e "${RED}✗ 应用异常${NC}"
    fi
    
    # 检查数据库连接
    echo "数据库连接检查:"
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec db pg_isready -U quanttrade > /dev/null; then
        echo -e "${GREEN}✓ 数据库连接正常${NC}"
    else
        echo -e "${RED}✗ 数据库连接异常${NC}"
    fi
    
    # 检查Redis连接
    echo "Redis连接检查:"
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec redis redis-cli ping > /dev/null; then
        echo -e "${GREEN}✓ Redis连接正常${NC}"
    else
        echo -e "${RED}✗ Redis连接异常${NC}"
    fi
}

# 主逻辑
case "${1:-help}" in
    deploy)
        deploy_prod
        ;;
    start)
        start_prod
        ;;
    stop)
        stop_prod
        ;;
    restart)
        restart_prod
        ;;
    logs)
        show_logs "$@"
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database "$@"
        ;;
    update)
        update_app
        ;;
    scale)
        scale_service "$@"
        ;;
    status)
        show_status
        ;;
    health)
        health_check
        ;;
    help|*)
        show_help
        ;;
esac