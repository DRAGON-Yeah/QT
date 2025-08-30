import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from celery import current_app
from celery.events.state import State
# from celery.events.monitor import Events  # 暂时注释掉，因为版本兼容性问题
from .models import CeleryWorker, CeleryTask, CeleryQueue
from apps.core.utils import get_current_tenant
import logging

logger = logging.getLogger(__name__)


class CeleryMonitorService:
    """Celery监控服务"""
    
    def __init__(self):
        self.app = current_app
        self.cache_timeout = 60  # 缓存1分钟
    
    def get_worker_stats(self) -> List[Dict]:
        """获取Worker统计信息"""
        try:
            # 获取活跃的workers
            inspect = self.app.control.inspect()
            
            # 获取worker状态
            stats = inspect.stats()
            active_queues = inspect.active_queues()
            active_tasks = inspect.active()
            
            workers_info = []
            
            if stats:
                for worker_name, worker_stats in stats.items():
                    # 获取worker的活跃任务
                    worker_active_tasks = active_tasks.get(worker_name, []) if active_tasks else []
                    
                    # 获取worker的队列信息
                    worker_queues = active_queues.get(worker_name, []) if active_queues else []
                    
                    worker_info = {
                        'worker_name': worker_name,
                        'hostname': worker_stats.get('hostname', ''),
                        'status': 'online',
                        'active_tasks': len(worker_active_tasks),
                        'processed_tasks': worker_stats.get('total', {}).get('tasks.total', 0),
                        'load_average': worker_stats.get('rusage', {}).get('utime', 0),
                        'last_heartbeat': timezone.now(),
                        'queues': [q['name'] for q in worker_queues],
                        'pool_processes': worker_stats.get('pool', {}).get('processes', []),
                    }
                    
                    workers_info.append(worker_info)
            
            return workers_info
            
        except Exception as e:
            logger.error(f"获取Worker统计信息失败: {e}")
            return []
    
    def save_worker_stats(self, tenant=None) -> List[CeleryWorker]:
        """保存Worker统计信息"""
        if not tenant:
            tenant = get_current_tenant()
        
        workers_info = self.get_worker_stats()
        saved_workers = []
        
        for worker_info in workers_info:
            worker = CeleryWorker.objects.create(
                tenant=tenant,
                worker_name=worker_info['worker_name'],
                hostname=worker_info['hostname'],
                status=worker_info['status'],
                active_tasks=worker_info['active_tasks'],
                processed_tasks=worker_info['processed_tasks'],
                load_average=worker_info.get('load_average', []),
                last_heartbeat=worker_info['last_heartbeat'],
            )
            saved_workers.append(worker)
        
        return saved_workers
    
    def get_task_stats(self, limit: int = 100) -> List[Dict]:
        """获取任务统计信息"""
        try:
            # 获取活跃任务
            inspect = self.app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            tasks_info = []
            
            # 处理活跃任务
            if active_tasks:
                for worker_name, tasks in active_tasks.items():
                    for task in tasks:
                        task_info = {
                            'task_id': task['id'],
                            'task_name': task['name'],
                            'state': 'STARTED',
                            'worker_name': worker_name,
                            'args': task.get('args', []),
                            'kwargs': task.get('kwargs', {}),
                            'started_at': datetime.fromtimestamp(task['time_start']) if task.get('time_start') else None,
                        }
                        tasks_info.append(task_info)
            
            # 处理计划任务
            if scheduled_tasks:
                for worker_name, tasks in scheduled_tasks.items():
                    for task in tasks:
                        task_info = {
                            'task_id': task['request']['id'],
                            'task_name': task['request']['task'],
                            'state': 'PENDING',
                            'worker_name': worker_name,
                            'args': task['request'].get('args', []),
                            'kwargs': task['request'].get('kwargs', {}),
                            'eta': datetime.fromtimestamp(task['eta']) if task.get('eta') else None,
                        }
                        tasks_info.append(task_info)
            
            return tasks_info[:limit]
            
        except Exception as e:
            logger.error(f"获取任务统计信息失败: {e}")
            return []
    
    def get_queue_stats(self) -> List[Dict]:
        """获取队列统计信息"""
        try:
            # 获取队列信息
            inspect = self.app.control.inspect()
            active_queues = inspect.active_queues()
            
            queues_info = []
            queue_stats = {}
            
            # 统计每个队列的任务数
            if active_queues:
                for worker_name, queues in active_queues.items():
                    for queue in queues:
                        queue_name = queue['name']
                        if queue_name not in queue_stats:
                            queue_stats[queue_name] = {
                                'queue_name': queue_name,
                                'routing_key': queue.get('routing_key', ''),
                                'exchange': queue.get('exchange', {}).get('name', ''),
                                'exchange_type': queue.get('exchange', {}).get('type', ''),
                                'pending_tasks': 0,
                                'active_tasks': 0,
                                'workers': []
                            }
                        queue_stats[queue_name]['workers'].append(worker_name)
            
            # 获取任务统计
            tasks_info = self.get_task_stats()
            for task in tasks_info:
                # 这里简化处理，实际应该根据任务的路由规则确定队列
                queue_name = 'celery'  # 默认队列
                if queue_name in queue_stats:
                    if task['state'] == 'STARTED':
                        queue_stats[queue_name]['active_tasks'] += 1
                    else:
                        queue_stats[queue_name]['pending_tasks'] += 1
            
            return list(queue_stats.values())
            
        except Exception as e:
            logger.error(f"获取队列统计信息失败: {e}")
            return []
    
    def save_queue_stats(self, tenant=None) -> List[CeleryQueue]:
        """保存队列统计信息"""
        if not tenant:
            tenant = get_current_tenant()
        
        queues_info = self.get_queue_stats()
        saved_queues = []
        
        for queue_info in queues_info:
            queue = CeleryQueue.objects.create(
                tenant=tenant,
                queue_name=queue_info['queue_name'],
                pending_tasks=queue_info['pending_tasks'],
                active_tasks=queue_info['active_tasks'],
                scheduled_tasks=0,  # 暂时设为0
                routing_key=queue_info['routing_key'],
                exchange=queue_info['exchange'],
                exchange_type=queue_info['exchange_type'],
            )
            saved_queues.append(queue)
        
        return saved_queues
    
    def get_task_history(self, task_name: str = None, limit: int = 50) -> List[CeleryTask]:
        """获取任务历史"""
        queryset = CeleryTask.objects.all()
        
        if task_name:
            queryset = queryset.filter(task_name=task_name)
        
        return queryset.order_by('-timestamp')[:limit]
    
    def get_failed_tasks(self, hours: int = 24) -> List[CeleryTask]:
        """获取失败的任务"""
        start_time = timezone.now() - timedelta(hours=hours)
        return CeleryTask.objects.filter(
            state='FAILURE',
            timestamp__gte=start_time
        ).order_by('-timestamp')
    
    def retry_failed_task(self, task_id: str) -> bool:
        """重试失败的任务"""
        try:
            # 获取任务信息
            task = CeleryTask.objects.get(task_id=task_id, state='FAILURE')
            
            # 重新提交任务
            from celery import signature
            sig = signature(task.task_name, args=task.args, kwargs=task.kwargs)
            result = sig.apply_async()
            
            # 更新任务状态
            task.retries += 1
            task.save()
            
            logger.info(f"任务 {task_id} 重试成功，新任务ID: {result.id}")
            return True
            
        except CeleryTask.DoesNotExist:
            logger.error(f"任务 {task_id} 不存在")
            return False
        except Exception as e:
            logger.error(f"重试任务 {task_id} 失败: {e}")
            return False
    
    def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
        """撤销任务"""
        try:
            self.app.control.revoke(task_id, terminate=terminate)
            
            # 更新数据库中的任务状态
            try:
                task = CeleryTask.objects.get(task_id=task_id)
                task.state = 'REVOKED'
                task.save()
            except CeleryTask.DoesNotExist:
                pass
            
            logger.info(f"任务 {task_id} 撤销成功")
            return True
            
        except Exception as e:
            logger.error(f"撤销任务 {task_id} 失败: {e}")
            return False
    
    def purge_queue(self, queue_name: str) -> int:
        """清空队列"""
        try:
            result = self.app.control.purge()
            
            # result是一个字典，键是worker名称，值是清理的任务数
            total_purged = sum(result.values()) if result else 0
            
            logger.info(f"队列 {queue_name} 清空完成，清理了 {total_purged} 个任务")
            return total_purged
            
        except Exception as e:
            logger.error(f"清空队列 {queue_name} 失败: {e}")
            return 0
    
    def get_worker_pool_info(self, worker_name: str) -> Dict:
        """获取Worker进程池信息"""
        try:
            inspect = self.app.control.inspect([worker_name])
            stats = inspect.stats()
            
            if stats and worker_name in stats:
                worker_stats = stats[worker_name]
                pool_info = worker_stats.get('pool', {})
                
                return {
                    'processes': pool_info.get('processes', []),
                    'max_concurrency': pool_info.get('max-concurrency', 0),
                    'max_memory_per_child': pool_info.get('max-memory-per-child', 0),
                    'timeouts': pool_info.get('timeouts', {}),
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取Worker {worker_name} 进程池信息失败: {e}")
            return {}
    
    def restart_worker_pool(self, worker_name: str) -> bool:
        """重启Worker进程池"""
        try:
            self.app.control.pool_restart([worker_name])
            logger.info(f"Worker {worker_name} 进程池重启成功")
            return True
            
        except Exception as e:
            logger.error(f"重启Worker {worker_name} 进程池失败: {e}")
            return False


class CeleryEventMonitor:
    """Celery事件监控器"""
    
    def __init__(self):
        self.state = State()
        self.should_stop = False
    
    def start_monitoring(self):
        """开始监控Celery事件"""
        try:
            # 暂时简化实现，后续可以根据需要添加事件监控
            logger.info("Celery事件监控启动")
            # TODO: 实现基于Celery版本的事件监控
                
        except Exception as e:
            logger.error(f"Celery事件监控失败: {e}")
    
    def on_task_sent(self, event):
        """任务发送事件"""
        self.state.event(event)
        # 这里可以记录任务发送事件
        logger.debug(f"任务发送: {event['uuid']}")
    
    def on_task_received(self, event):
        """任务接收事件"""
        self.state.event(event)
        logger.debug(f"任务接收: {event['uuid']}")
    
    def on_task_started(self, event):
        """任务开始事件"""
        self.state.event(event)
        
        # 更新或创建任务记录
        task_id = event['uuid']
        try:
            task, created = CeleryTask.objects.get_or_create(
                task_id=task_id,
                defaults={
                    'task_name': event.get('name', ''),
                    'state': 'STARTED',
                    'worker_name': event.get('hostname', ''),
                    'started_at': datetime.fromtimestamp(event['timestamp']),
                }
            )
            
            if not created:
                task.state = 'STARTED'
                task.started_at = datetime.fromtimestamp(event['timestamp'])
                task.save()
                
        except Exception as e:
            logger.error(f"处理任务开始事件失败: {e}")
    
    def on_task_succeeded(self, event):
        """任务成功事件"""
        self.state.event(event)
        
        task_id = event['uuid']
        try:
            task = CeleryTask.objects.get(task_id=task_id)
            task.state = 'SUCCESS'
            task.succeeded_at = datetime.fromtimestamp(event['timestamp'])
            task.result = event.get('result')
            task.runtime = Decimal(str(event.get('runtime', 0)))
            task.save()
            
        except CeleryTask.DoesNotExist:
            logger.warning(f"任务 {task_id} 不存在于数据库中")
        except Exception as e:
            logger.error(f"处理任务成功事件失败: {e}")
    
    def on_task_failed(self, event):
        """任务失败事件"""
        self.state.event(event)
        
        task_id = event['uuid']
        try:
            task = CeleryTask.objects.get(task_id=task_id)
            task.state = 'FAILURE'
            task.failed_at = datetime.fromtimestamp(event['timestamp'])
            task.traceback = event.get('traceback', '')
            task.save()
            
        except CeleryTask.DoesNotExist:
            logger.warning(f"任务 {task_id} 不存在于数据库中")
        except Exception as e:
            logger.error(f"处理任务失败事件失败: {e}")
    
    def on_task_retried(self, event):
        """任务重试事件"""
        self.state.event(event)
        
        task_id = event['uuid']
        try:
            task = CeleryTask.objects.get(task_id=task_id)
            task.state = 'RETRY'
            task.retries += 1
            task.save()
            
        except CeleryTask.DoesNotExist:
            logger.warning(f"任务 {task_id} 不存在于数据库中")
        except Exception as e:
            logger.error(f"处理任务重试事件失败: {e}")
    
    def on_task_revoked(self, event):
        """任务撤销事件"""
        self.state.event(event)
        
        task_id = event['uuid']
        try:
            task = CeleryTask.objects.get(task_id=task_id)
            task.state = 'REVOKED'
            task.save()
            
        except CeleryTask.DoesNotExist:
            logger.warning(f"任务 {task_id} 不存在于数据库中")
        except Exception as e:
            logger.error(f"处理任务撤销事件失败: {e}")
    
    def on_worker_online(self, event):
        """Worker上线事件"""
        logger.info(f"Worker上线: {event['hostname']}")
    
    def on_worker_offline(self, event):
        """Worker下线事件"""
        logger.info(f"Worker下线: {event['hostname']}")
    
    def on_worker_heartbeat(self, event):
        """Worker心跳事件"""
        # 更新Worker状态
        worker_name = event['hostname']
        try:
            # 这里可以更新Worker的心跳时间
            pass
        except Exception as e:
            logger.error(f"处理Worker心跳事件失败: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        self.should_stop = True