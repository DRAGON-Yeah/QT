from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .services import SystemMonitorService, ProcessMonitorService, AlertService, MetricsCleanupService
from .celery_services import CeleryMonitorService
from apps.users.models import Tenant
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def collect_system_metrics(self):
    """收集系统指标任务"""
    try:
        service = SystemMonitorService()
        
        # 为每个租户收集指标
        for tenant in Tenant.objects.filter(is_active=True):
            try:
                metrics = service.save_system_metrics(tenant)
                logger.info(f"为租户 {tenant.name} 收集系统指标成功")
            except Exception as e:
                logger.error(f"为租户 {tenant.name} 收集系统指标失败: {e}")
        
        return "系统指标收集完成"
        
    except Exception as e:
        logger.error(f"收集系统指标任务失败: {e}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True)
def collect_process_metrics(self):
    """收集进程指标任务"""
    try:
        service = ProcessMonitorService()
        
        # 监控的进程列表
        process_names = ['python', 'celery', 'redis-server', 'postgres', 'nginx', 'gunicorn']
        
        # 为每个租户收集进程指标
        for tenant in Tenant.objects.filter(is_active=True):
            try:
                metrics = service.save_process_metrics(tenant, process_names)
                logger.info(f"为租户 {tenant.name} 收集进程指标成功，共 {len(metrics)} 个进程")
            except Exception as e:
                logger.error(f"为租户 {tenant.name} 收集进程指标失败: {e}")
        
        return "进程指标收集完成"
        
    except Exception as e:
        logger.error(f"收集进程指标任务失败: {e}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True)
def check_alert_rules(self):
    """检查告警规则任务"""
    try:
        service = AlertService()
        total_alerts = 0
        
        # 为每个租户检查告警规则
        for tenant in Tenant.objects.filter(is_active=True):
            try:
                alerts = service.check_alert_rules(tenant)
                total_alerts += len(alerts)
                
                if alerts:
                    logger.warning(f"租户 {tenant.name} 触发 {len(alerts)} 个告警")
                
            except Exception as e:
                logger.error(f"为租户 {tenant.name} 检查告警规则失败: {e}")
        
        return f"告警规则检查完成，共触发 {total_alerts} 个告警"
        
    except Exception as e:
        logger.error(f"检查告警规则任务失败: {e}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True)
def cleanup_old_metrics(self, days_to_keep=30):
    """清理旧指标数据任务"""
    try:
        service = MetricsCleanupService()
        result = service.cleanup_old_metrics(days_to_keep)
        
        logger.info(f"清理旧指标数据完成: {result}")
        return f"清理完成: {result}"
        
    except Exception as e:
        logger.error(f"清理旧指标数据任务失败: {e}")
        raise self.retry(countdown=300, max_retries=3)


@shared_task(bind=True)
def generate_monitoring_report(self):
    """生成监控报告任务"""
    try:
        from .models import SystemMetrics, Alert
        
        # 获取过去24小时的统计数据
        last_24h = timezone.now() - timedelta(hours=24)
        
        report_data = {}
        
        for tenant in Tenant.objects.filter(is_active=True):
            # 系统指标统计
            metrics = SystemMetrics.objects.filter(
                tenant=tenant,
                timestamp__gte=last_24h
            )
            
            if metrics.exists():
                from django.db import models
                avg_cpu = metrics.aggregate(avg_cpu=models.Avg('cpu_percent'))['avg_cpu']
                avg_memory = metrics.aggregate(avg_memory=models.Avg('memory_percent'))['avg_memory']
                avg_disk = metrics.aggregate(avg_disk=models.Avg('disk_percent'))['avg_disk']
                
                # 告警统计
                alerts_count = Alert.objects.filter(
                    tenant=tenant,
                    fired_at__gte=last_24h
                ).count()
                
                report_data[tenant.name] = {
                    'avg_cpu': float(avg_cpu) if avg_cpu else 0,
                    'avg_memory': float(avg_memory) if avg_memory else 0,
                    'avg_disk': float(avg_disk) if avg_disk else 0,
                    'alerts_count': alerts_count,
                    'metrics_count': metrics.count()
                }
        
        logger.info(f"监控报告生成完成: {report_data}")
        return report_data
        
    except Exception as e:
        logger.error(f"生成监控报告任务失败: {e}")
        raise self.retry(countdown=300, max_retries=3)


@shared_task(bind=True)
def system_health_check(self):
    """系统健康检查任务"""
    try:
        from django.db import connection
        from django.core.cache import cache
        import psutil
        
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        # 数据库检查
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'healthy'
        except Exception as e:
            health_status['checks']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # 缓存检查
        try:
            cache.set('health_check_task', 'ok', 10)
            cache.get('health_check_task')
            health_status['checks']['cache'] = 'healthy'
        except Exception as e:
            health_status['checks']['cache'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # 系统资源检查
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            # 检查资源使用率是否过高
            if cpu_percent > 90:
                health_status['checks']['cpu'] = f'high_usage: {cpu_percent}%'
                health_status['status'] = 'warning'
            else:
                health_status['checks']['cpu'] = 'healthy'
            
            if memory_percent > 90:
                health_status['checks']['memory'] = f'high_usage: {memory_percent}%'
                health_status['status'] = 'warning'
            else:
                health_status['checks']['memory'] = 'healthy'
            
            if disk_percent > 90:
                health_status['checks']['disk'] = f'high_usage: {disk_percent}%'
                health_status['status'] = 'warning'
            else:
                health_status['checks']['disk'] = 'healthy'
                
        except Exception as e:
            health_status['checks']['system_resources'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # 记录健康检查结果
        if health_status['status'] != 'healthy':
            logger.warning(f"系统健康检查发现问题: {health_status}")
        else:
            logger.info("系统健康检查正常")
        
        return health_status
        
    except Exception as e:
        logger.error(f"系统健康检查任务失败: {e}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True)
def collect_celery_stats(self):
    """收集Celery统计信息任务"""
    try:
        service = CeleryMonitorService()
        
        # 为每个租户收集Celery统计信息
        for tenant in Tenant.objects.filter(is_active=True):
            try:
                # 收集Worker统计
                workers = service.save_worker_stats(tenant)
                
                # 收集队列统计
                queues = service.save_queue_stats(tenant)
                
                logger.info(f"为租户 {tenant.name} 收集Celery统计成功: "
                           f"Workers {len(workers)}, Queues {len(queues)}")
                
            except Exception as e:
                logger.error(f"为租户 {tenant.name} 收集Celery统计失败: {e}")
        
        return "Celery统计收集完成"
        
    except Exception as e:
        logger.error(f"收集Celery统计任务失败: {e}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True)
def cleanup_celery_data(self, days_to_keep=7):
    """清理Celery历史数据任务"""
    try:
        from .models import CeleryWorker, CeleryTask, CeleryQueue
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # 清理Worker历史数据
        deleted_workers = CeleryWorker.objects.filter(timestamp__lt=cutoff_date).delete()
        
        # 清理已完成的任务数据
        deleted_tasks = CeleryTask.objects.filter(
            timestamp__lt=cutoff_date,
            state__in=['SUCCESS', 'FAILURE', 'REVOKED']
        ).delete()
        
        # 清理队列历史数据
        deleted_queues = CeleryQueue.objects.filter(timestamp__lt=cutoff_date).delete()
        
        logger.info(f"Celery数据清理完成: Workers {deleted_workers[0]} 条, "
                   f"Tasks {deleted_tasks[0]} 条, Queues {deleted_queues[0]} 条")
        
        return {
            'workers': deleted_workers[0],
            'tasks': deleted_tasks[0],
            'queues': deleted_queues[0]
        }
        
    except Exception as e:
        logger.error(f"清理Celery数据任务失败: {e}")
        raise self.retry(countdown=300, max_retries=3)