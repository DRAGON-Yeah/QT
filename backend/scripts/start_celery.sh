#!/bin/bash
# Celery启动脚本

set -e

# 进入项目目录
cd "$(dirname "$0")/.."

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 设置环境变量
export DJANGO_SETTINGS_MODULE=config.settings.development

echo "启动Celery服务..."

# 启动Celery Worker
echo "启动Celery Worker..."
celery -A config worker --loglevel=info --detach --pidfile=/tmp/celery_worker.pid --logfile=logs/celery_worker.log

# 启动Celery Beat
echo "启动Celery Beat..."
celery -A config beat --loglevel=info --detach --pidfile=/tmp/celery_beat.pid --logfile=logs/celery_beat.log --scheduler django_celery_beat.schedulers:DatabaseScheduler

# 启动Flower (可选的监控工具)
if command -v flower &> /dev/null; then
    echo "启动Flower监控..."
    flower -A config --port=5555 --detach --pidfile=/tmp/flower.pid --logfile=logs/flower.log
fi

echo "Celery服务启动完成！"
echo "Worker PID: $(cat /tmp/celery_worker.pid 2>/dev/null || echo 'N/A')"
echo "Beat PID: $(cat /tmp/celery_beat.pid 2>/dev/null || echo 'N/A')"
echo "Flower PID: $(cat /tmp/flower.pid 2>/dev/null || echo 'N/A')"