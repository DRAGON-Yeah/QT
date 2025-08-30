#!/bin/bash
# QuantTrade 开发环境管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 显示帮助信息
show_help() {
    echo "QuantTrade 开发环境管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动开发环境"
    echo "  stop      停止开发环境"
    echo "  restart   重启开发环境"
    echo "  logs      查看日志"
    echo "  shell     进入后端容器shell"
    echo "  migrate   执行数据库迁移"
    echo "  test      运行测试"
    echo "  clean     清理容器和数据卷"
    echo "  build     重新构建镜像"
    echo "  status    查看服务状态"
    echo "  help      显示此帮助信息"
}

# 启动开发环境
start_dev() {
    echo -e "${YELLOW}启动QuantTrade开发环境...${NC}"
    
    # 检查环境变量文件
    if [ ! -f .env ]; then
        echo -e "${YELLOW}创建环境变量文件...${NC}"
        cp .env.example .env
    fi
    
    # 启动服务
    docker-compose up -d
    
    echo -e "${GREEN}开发环境启动完成！${NC}"
    echo ""
    echo "服务地址:"
    echo "  前端: http://localhost:3000"
    echo "  后端API: http://localhost:8000"
    echo "  管理后台: http://localhost:8000/admin/"
    echo "  数据库: localhost:5432"
    echo "  Redis: localhost:6379"
}

# 停止开发环境
stop_dev() {
    echo -e "${YELLOW}停止QuantTrade开发环境...${NC}"
    docker-compose down
    echo -e "${GREEN}开发环境已停止${NC}"
}

# 重启开发环境
restart_dev() {
    echo -e "${YELLOW}重启QuantTrade开发环境...${NC}"
    docker-compose restart
    echo -e "${GREEN}开发环境已重启${NC}"
}

# 查看日志
show_logs() {
    if [ -n "$2" ]; then
        docker-compose logs -f "$2"
    else
        docker-compose logs -f
    fi
}

# 进入后端容器shell
enter_shell() {
    docker-compose exec backend bash
}

# 执行数据库迁移
run_migrate() {
    echo -e "${YELLOW}执行数据库迁移...${NC}"
    docker-compose exec backend python manage.py migrate
    echo -e "${GREEN}数据库迁移完成${NC}"
}

# 运行测试
run_tests() {
    echo -e "${YELLOW}运行测试...${NC}"
    docker-compose exec backend python manage.py test
}

# 清理环境
clean_env() {
    echo -e "${RED}警告: 这将删除所有容器和数据卷！${NC}"
    read -p "确定要继续吗? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}清理环境...${NC}"
        docker-compose down -v --remove-orphans
        docker system prune -f
        echo -e "${GREEN}环境清理完成${NC}"
    fi
}

# 重新构建镜像
rebuild_images() {
    echo -e "${YELLOW}重新构建镜像...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}镜像构建完成${NC}"
}

# 查看服务状态
show_status() {
    echo -e "${BLUE}QuantTrade 服务状态:${NC}"
    docker-compose ps
}

# 主逻辑
case "${1:-help}" in
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    restart)
        restart_dev
        ;;
    logs)
        show_logs "$@"
        ;;
    shell)
        enter_shell
        ;;
    migrate)
        run_migrate
        ;;
    test)
        run_tests
        ;;
    clean)
        clean_env
        ;;
    build)
        rebuild_images
        ;;
    status)
        show_status
        ;;
    help|*)
        show_help
        ;;
esac