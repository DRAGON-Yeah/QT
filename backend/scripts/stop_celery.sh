#!/bin/bash
# Celery停止脚本

set -e

echo "停止Celery服务..."

# 停止Celery Worker
if [ -f "/tmp/celery_worker.pid" ]; then
    echo "停止Celery Worker..."
    kill $(cat /tmp/celery_worker.pid) 2>/dev/null || echo "Worker已停止"
    rm -f /tmp/celery_worker.pid
fi

# 停止Celery Beat
if [ -f "/tmp/celery_beat.pid" ]; then
    echo "停止Celery Beat..."
    kill $(cat /tmp/celery_beat.pid) 2>/dev/null || echo "Beat已停止"
    rm -f /tmp/celery_beat.pid
fi

# 停止Flower
if [ -f "/tmp/flower.pid" ]; then
    echo "停止Flower..."
    kill $(cat /tmp/flower.pid) 2>/dev/null || echo "Flower已停止"
    rm -f /tmp/flower.pid
fi

# 强制杀死所有Celery进程
echo "清理残留进程..."
pkill -f "celery worker" 2>/dev/null || true
pkill -f "celery beat" 2>/dev/null || true
pkill -f "flower" 2>/dev/null || true

echo "Celery服务已停止！"