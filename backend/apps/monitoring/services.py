import psutil
import platform
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Avg, Max, Min
from .models import SystemMetrics, ProcessMetrics, AlertRule, Alert
from apps.core.utils import get_current_tenant
import logging

logger = logging.getLogger(__name__)


class SystemMonitorService:
    """系统监控服务"""
    
    def __init__(self):
        self.cache_timeout = 60  # 缓存1分钟
    
    def collect_system_metrics(self) -> Dict:
        """收集系统性能指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 负载平均值（仅Unix系统）
            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                try:
                    load_avg = psutil.getloadavg()
                except (OSError, AttributeError):
                    load_avg = None
            
            # 内存指标
            memory = psutil.virtual_memory()
            
            # 磁盘指标
            disk = psutil.disk_usage('/')
            
            # 网络指标
            network = psutil.net_io_counters()
            
            metrics = {
                'cpu_percent': Decimal(str(cpu_percent)),
                'cpu_count': cpu_count,
                'load_average_1m': Decimal(str(load_avg[0])) if load_avg else None,
                'load_average_5m': Decimal(str(load_avg[1])) if load_avg else None,
                'load_average_15m': Decimal(str(load_avg[2])) if load_avg else None,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'memory_percent': Decimal(str(memory.percent)),
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_free': disk.free,
                'disk_percent': Decimal(str(disk.used / disk.total * 100)),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'network_packets_sent': network.packets_sent,
                'network_packets_recv': network.packets_recv,
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            raise
    
    def save_system_metrics(self, tenant=None) -> SystemMetrics:
        """保存系统指标到数据库"""
        if not tenant:
            tenant = get_current_tenant()
        
        metrics_data = self.collect_system_metrics()
        metrics_data['tenant'] = tenant
        
        metrics = SystemMetrics.objects.create(**metrics_data)
        
        # 缓存最新指标
        cache.set(f'system_metrics_{tenant.id}', metrics_data, self.cache_timeout)
        
        return metrics
    
    def get_latest_metrics(self, tenant=None) -> Optional[Dict]:
        """获取最新的系统指标"""
        if not tenant:
            tenant = get_current_tenant()
        
        # 先从缓存获取
        cached_metrics = cache.get(f'system_metrics_{tenant.id}')
        if cached_metrics:
            return cached_metrics
        
        # 从数据库获取
        latest_metrics = SystemMetrics.objects.filter(tenant=tenant).first()
        if latest_metrics:
            metrics_data = {
                'cpu_percent': latest_metrics.cpu_percent,
                'cpu_count': latest_metrics.cpu_count,
                'load_average_1m': latest_metrics.load_average_1m,
                'load_average_5m': latest_metrics.load_average_5m,
                'load_average_15m': latest_metrics.load_average_15m,
                'memory_total': latest_metrics.memory_total,
                'memory_available': latest_metrics.memory_available,
                'memory_used': latest_metrics.memory_used,
                'memory_percent': latest_metrics.memory_percent,
                'disk_total': latest_metrics.disk_total,
                'disk_used': latest_metrics.disk_used,
                'disk_free': latest_metrics.disk_free,
                'disk_percent': latest_metrics.disk_percent,
                'network_bytes_sent': latest_metrics.network_bytes_sent,
                'network_bytes_recv': latest_metrics.network_bytes_recv,
                'network_packets_sent': latest_metrics.network_packets_sent,
                'network_packets_recv': latest_metrics.network_packets_recv,
                'timestamp': latest_metrics.timestamp,
            }
            cache.set(f'system_metrics_{tenant.id}', metrics_data, self.cache_timeout)
            return metrics_data
        
        return None
    
    def get_historical_metrics(self, tenant=None, hours=24) -> List[SystemMetrics]:
        """获取历史指标数据"""
        if not tenant:
            tenant = get_current_tenant()
        
        start_time = timezone.now() - timedelta(hours=hours)
        return SystemMetrics.objects.filter(
            tenant=tenant,
            timestamp__gte=start_time
        ).order_by('timestamp')
    
    def get_metrics_summary(self, tenant=None, hours=24) -> Dict:
        """获取指标统计摘要"""
        if not tenant:
            tenant = get_current_tenant()
        
        start_time = timezone.now() - timedelta(hours=hours)
        metrics = SystemMetrics.objects.filter(
            tenant=tenant,
            timestamp__gte=start_time
        )
        
        if not metrics.exists():
            return {}
        
        summary = metrics.aggregate(
            avg_cpu=Avg('cpu_percent'),
            max_cpu=Max('cpu_percent'),
            min_cpu=Min('cpu_percent'),
            avg_memory=Avg('memory_percent'),
            max_memory=Max('memory_percent'),
            min_memory=Min('memory_percent'),
            avg_disk=Avg('disk_percent'),
            max_disk=Max('disk_percent'),
            min_disk=Min('disk_percent'),
        )
        
        return summary


class ProcessMonitorService:
    """进程监控服务"""
    
    def collect_process_metrics(self, process_names: List[str] = None) -> List[Dict]:
        """收集进程指标"""
        if not process_names:
            # 默认监控的进程
            process_names = ['python', 'celery', 'redis-server', 'postgres', 'nginx']
        
        process_metrics = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                       'memory_info', 'status', 'create_time', 'num_threads']):
            try:
                if any(name in proc.info['name'].lower() for name in process_names):
                    metrics = {
                        'process_name': proc.info['name'],
                        'pid': proc.info['pid'],
                        'cpu_percent': Decimal(str(proc.info['cpu_percent'] or 0)),
                        'memory_percent': Decimal(str(proc.info['memory_percent'] or 0)),
                        'memory_rss': proc.info['memory_info'].rss if proc.info['memory_info'] else 0,
                        'memory_vms': proc.info['memory_info'].vms if proc.info['memory_info'] else 0,
                        'status': proc.info['status'],
                        'create_time': datetime.fromtimestamp(proc.info['create_time']),
                        'num_threads': proc.info['num_threads'] or 0,
                    }
                    process_metrics.append(metrics)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return process_metrics
    
    def save_process_metrics(self, tenant=None, process_names: List[str] = None) -> List[ProcessMetrics]:
        """保存进程指标到数据库"""
        if not tenant:
            tenant = get_current_tenant()
        
        metrics_list = self.collect_process_metrics(process_names)
        saved_metrics = []
        
        for metrics_data in metrics_list:
            metrics_data['tenant'] = tenant
            metrics = ProcessMetrics.objects.create(**metrics_data)
            saved_metrics.append(metrics)
        
        return saved_metrics


class AlertService:
    """告警服务"""
    
    def check_alert_rules(self, tenant=None) -> List[Alert]:
        """检查告警规则"""
        if not tenant:
            tenant = get_current_tenant()
        
        # 获取最新系统指标
        monitor_service = SystemMonitorService()
        latest_metrics = monitor_service.get_latest_metrics(tenant)
        
        if not latest_metrics:
            return []
        
        # 获取活跃的告警规则
        active_rules = AlertRule.objects.filter(tenant=tenant, is_active=True)
        triggered_alerts = []
        
        for rule in active_rules:
            current_value = latest_metrics.get(rule.metric)
            if current_value is None:
                continue
            
            # 检查是否触发告警
            if self._evaluate_condition(current_value, rule.operator, rule.threshold):
                # 检查是否已有未解决的告警
                existing_alert = Alert.objects.filter(
                    tenant=tenant,
                    rule=rule,
                    status='firing'
                ).first()
                
                if not existing_alert:
                    # 创建新告警
                    alert = Alert.objects.create(
                        tenant=tenant,
                        rule=rule,
                        message=f"{rule.name}: {rule.metric} 当前值 {current_value} {rule.operator} 阈值 {rule.threshold}",
                        current_value=current_value,
                        threshold_value=rule.threshold,
                        status='firing'
                    )
                    triggered_alerts.append(alert)
                    
                    # 发送通知
                    if rule.notification_enabled:
                        self._send_alert_notification(alert)
            else:
                # 检查是否需要解决告警
                existing_alerts = Alert.objects.filter(
                    tenant=tenant,
                    rule=rule,
                    status='firing'
                )
                for alert in existing_alerts:
                    alert.status = 'resolved'
                    alert.resolved_at = timezone.now()
                    alert.save()
        
        return triggered_alerts
    
    def _evaluate_condition(self, current_value: Decimal, operator: str, threshold: Decimal) -> bool:
        """评估告警条件"""
        if operator == '>':
            return current_value > threshold
        elif operator == '>=':
            return current_value >= threshold
        elif operator == '<':
            return current_value < threshold
        elif operator == '<=':
            return current_value <= threshold
        elif operator == '==':
            return current_value == threshold
        elif operator == '!=':
            return current_value != threshold
        return False
    
    def _send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        try:
            # 这里可以集成邮件、短信、Webhook等通知方式
            logger.warning(f"告警触发: {alert.message}")
            
            # 如果配置了Webhook，发送到Webhook
            if alert.rule.webhook_url:
                # TODO: 实现Webhook通知
                pass
            
            # 如果启用了邮件通知
            if alert.rule.email_notification:
                # TODO: 实现邮件通知
                pass
                
        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")
    
    def acknowledge_alert(self, alert_id: int, user, tenant=None):
        """确认告警"""
        if not tenant:
            tenant = get_current_tenant()
        
        try:
            alert = Alert.objects.get(id=alert_id, tenant=tenant)
            alert.status = 'acknowledged'
            alert.acknowledged_at = timezone.now()
            alert.acknowledged_by = user
            alert.save()
            return alert
        except Alert.DoesNotExist:
            raise ValueError("告警不存在")


class MetricsCleanupService:
    """指标数据清理服务"""
    
    def cleanup_old_metrics(self, days_to_keep: int = 30):
        """清理旧的指标数据"""
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # 清理系统指标
        deleted_system = SystemMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
        
        # 清理进程指标
        deleted_process = ProcessMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
        
        # 清理已解决的告警
        deleted_alerts = Alert.objects.filter(
            status='resolved',
            resolved_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"清理完成: 系统指标 {deleted_system[0]} 条, "
                   f"进程指标 {deleted_process[0]} 条, "
                   f"告警记录 {deleted_alerts[0]} 条")
        
        return {
            'system_metrics': deleted_system[0],
            'process_metrics': deleted_process[0],
            'alerts': deleted_alerts[0]
        }