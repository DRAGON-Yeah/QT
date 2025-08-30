#!/bin/bash
# QuantTrade Docker监控脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 显示帮助信息
show_help() {
    echo "QuantTrade Docker监控脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  stats     显示容器资源使用情况"
    echo "  top       显示容器进程信息"
    echo "  inspect   显示容器详细信息"
    echo "  network   显示网络信息"
    echo "  volumes   显示数据卷信息"
    echo "  images    显示镜像信息"
    echo "  cleanup   清理未使用的资源"
    echo "  help      显示此帮助信息"
}

# 显示容器资源使用情况
show_stats() {
    echo -e "${BLUE}QuantTrade 容器资源使用情况:${NC}"
    echo ""
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 显示容器进程信息
show_top() {
    echo -e "${BLUE}QuantTrade 容器进程信息:${NC}"
    echo ""
    
    for container in $(docker-compose ps -q); do
        container_name=$(docker inspect --format='{{.Name}}' $container | sed 's/\///')
        echo -e "${YELLOW}=== $container_name ===${NC}"
        docker top $container
        echo ""
    done
}

# 显示容器详细信息
show_inspect() {
    if [ -z "$2" ]; then
        echo -e "${RED}错误: 请指定容器名称${NC}"
        echo "可用容器:"
        docker-compose ps --services
        exit 1
    fi
    
    echo -e "${BLUE}容器详细信息: $2${NC}"
    docker-compose exec "$2" sh -c '
        echo "=== 系统信息 ==="
        uname -a
        echo ""
        echo "=== 内存使用 ==="
        free -h
        echo ""
        echo "=== 磁盘使用 ==="
        df -h
        echo ""
        echo "=== 网络连接 ==="
        netstat -tuln 2>/dev/null || ss -tuln
        echo ""
        echo "=== 进程列表 ==="
        ps aux
    '
}

# 显示网络信息
show_network() {
    echo -e "${BLUE}QuantTrade 网络信息:${NC}"
    echo ""
    
    echo "=== Docker网络列表 ==="
    docker network ls
    echo ""
    
    echo "=== QuantTrade网络详情 ==="
    docker network inspect quanttrade_network 2>/dev/null || echo "网络不存在"
    echo ""
    
    echo "=== 容器网络连接 ==="
    docker-compose ps --format "table {{.Name}}\t{{.Ports}}"
}

# 显示数据卷信息
show_volumes() {
    echo -e "${BLUE}QuantTrade 数据卷信息:${NC}"
    echo ""
    
    echo "=== 数据卷列表 ==="
    docker volume ls | grep quanttrade
    echo ""
    
    echo "=== 数据卷使用情况 ==="
    for volume in $(docker volume ls -q | grep quanttrade); do
        echo -e "${YELLOW}=== $volume ===${NC}"
        docker volume inspect "$volume" --format '{{.Mountpoint}}: {{.Options}}'
        
        # 显示数据卷大小
        mountpoint=$(docker volume inspect "$volume" --format '{{.Mountpoint}}')
        if [ -d "$mountpoint" ]; then
            size=$(sudo du -sh "$mountpoint" 2>/dev/null | cut -f1 || echo "N/A")
            echo "大小: $size"
        fi
        echo ""
    done
}

# 显示镜像信息
show_images() {
    echo -e "${BLUE}QuantTrade 镜像信息:${NC}"
    echo ""
    
    echo "=== 项目镜像 ==="
    docker images | grep -E "(quanttrade|postgres|redis|nginx)" || echo "未找到相关镜像"
    echo ""
    
    echo "=== 镜像大小统计 ==="
    docker system df
}

# 清理未使用的资源
cleanup_resources() {
    echo -e "${YELLOW}清理Docker未使用的资源...${NC}"
    
    echo "清理未使用的容器..."
    docker container prune -f
    
    echo "清理未使用的镜像..."
    docker image prune -f
    
    echo "清理未使用的网络..."
    docker network prune -f
    
    echo "清理未使用的数据卷..."
    read -p "是否清理未使用的数据卷? 这可能会删除重要数据! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    echo -e "${GREEN}清理完成${NC}"
    
    echo ""
    echo "清理后的系统状态:"
    docker system df
}

# 实时监控
real_time_monitor() {
    echo -e "${BLUE}QuantTrade 实时监控 (按Ctrl+C退出)${NC}"
    echo ""
    
    while true; do
        clear
        echo "=== $(date) ==="
        echo ""
        
        # 显示容器状态
        echo "容器状态:"
        docker-compose ps
        echo ""
        
        # 显示资源使用
        echo "资源使用:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        echo ""
        
        # 显示系统负载
        echo "系统负载:"
        uptime
        echo ""
        
        sleep 5
    done
}

# 主逻辑
case "${1:-help}" in
    stats)
        show_stats
        ;;
    top)
        show_top
        ;;
    inspect)
        show_inspect "$@"
        ;;
    network)
        show_network
        ;;
    volumes)
        show_volumes
        ;;
    images)
        show_images
        ;;
    cleanup)
        cleanup_resources
        ;;
    monitor)
        real_time_monitor
        ;;
    help|*)
        show_help
        ;;
esac