#!/usr/bin/env python
"""
Celery监控脚本
"""
import os
import sys
import django
from celery import Celery
from celery.events.state import State
from celery.events import EventReceiver
import json
import time

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from config.celery import app as celery_app


class CeleryMonitor:
    def __init__(self):
        self.app = celery_app
        self.state = State()
    
    def get_active_tasks(self):
        """获取活跃任务"""
        inspect = self.app.control.inspect()
        active_tasks = inspect.active()
        return active_tasks or {}
    
    def get_scheduled_tasks(self):
        """获取计划任务"""
        inspect = self.app.control.inspect()
        scheduled_tasks = inspect.scheduled()
        return scheduled_tasks or {}
    
    def get_worker_stats(self):
        """获取Worker统计信息"""
        inspect = self.app.control.inspect()
        stats = inspect.stats()
        return stats or {}
    
    def get_registered_tasks(self):
        """获取已注册的任务"""
        inspect = self.app.control.inspect()
        registered = inspect.registered()
        return registered or {}
    
    def purge_queue(self, queue_name='celery'):
        """清空队列"""
        return self.app.control.purge()
    
    def revoke_task(self, task_id, terminate=False):
        """撤销任务"""
        return self.app.control.revoke(task_id, terminate=terminate)
    
    def get_queue_length(self):
        """获取队列长度"""
        from kombu import Connection
        
        try:
            with Connection(self.app.conf.broker_url) as conn:
                # 这里需要根据具体的消息代理实现
                # Redis的实现会有所不同
                return 0
        except Exception as e:
            print(f"获取队列长度失败: {e}")
            return -1


def print_worker_status():
    """打印Worker状态"""
    monitor = CeleryMonitor()
    
    print("=== Celery Worker 状态 ===")
    
    # 活跃任务
    active_tasks = monitor.get_active_tasks()
    print(f"\n活跃任务数量: {sum(len(tasks) for tasks in active_tasks.values())}")
    for worker, tasks in active_tasks.items():
        print(f"  {worker}: {len(tasks)} 个任务")
        for task in tasks:
            print(f"    - {task['name']} ({task['id'][:8]}...)")
    
    # Worker统计
    stats = monitor.get_worker_stats()
    print(f"\nWorker统计:")
    for worker, stat in stats.items():
        print(f"  {worker}:")
        print(f"    - 总任务数: {stat.get('total', 0)}")
        print(f"    - 进程池大小: {stat.get('pool', {}).get('max-concurrency', 0)}")
    
    # 已注册任务
    registered = monitor.get_registered_tasks()
    print(f"\n已注册任务:")
    for worker, tasks in registered.items():
        print(f"  {worker}: {len(tasks)} 个任务")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python celery_monitor.py [status|purge|revoke]")
        return
    
    command = sys.argv[1]
    monitor = CeleryMonitor()
    
    if command == 'status':
        print_worker_status()
    
    elif command == 'purge':
        result = monitor.purge_queue()
        print(f"清空队列完成，删除了 {result} 个任务")
    
    elif command == 'revoke':
        if len(sys.argv) < 3:
            print("用法: python celery_monitor.py revoke <task_id>")
            return
        
        task_id = sys.argv[2]
        terminate = len(sys.argv) > 3 and sys.argv[3] == '--terminate'
        
        result = monitor.revoke_task(task_id, terminate=terminate)
        print(f"任务 {task_id} 已撤销")
    
    else:
        print("未知命令")


if __name__ == '__main__':
    main()