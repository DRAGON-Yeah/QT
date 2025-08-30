"""
系统监控视图
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import SystemMetrics, ProcessMetrics, AlertRule, Alert
from .services import SystemMonitorService, ProcessMonitorService, AlertService, MetricsCleanupService
from .celery_services import CeleryMonitorService
from .serializers import (
    SystemMetricsSerializer, ProcessMetricsSerializer, 
    AlertRuleSerializer, AlertSerializer, CeleryWorkerSerializer,
    CeleryTaskSerializer, CeleryQueueSerializer
)
from apps.core.permissions import TenantPermission
import time
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    系统健康检查
    """
    status = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'checks': {}
    }
    
    # 数据库检查
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'healthy'
    except Exception as e:
        status['checks']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # 缓存检查
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        status['checks']['cache'] = 'healthy'
    except Exception as e:
        status['checks']['cache'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    return JsonResponse(status)


class SystemMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """系统指标视图集"""
    
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        return SystemMetrics.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """获取最新系统指标"""
        try:
            service = SystemMonitorService()
            metrics = service.get_latest_metrics(request.user.tenant)
            
            if metrics:
                return Response(metrics)
            else:
                return Response({'message': '暂无系统指标数据'}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"获取最新系统指标失败: {e}")
            return Response({'error': '获取系统指标失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取系统指标摘要"""
        try:
            hours = int(request.query_params.get('hours', 24))
            service = SystemMonitorService()
            summary = service.get_metrics_summary(request.user.tenant, hours)
            
            return Response(summary)
            
        except Exception as e:
            logger.error(f"获取系统指标摘要失败: {e}")
            return Response({'error': '获取指标摘要失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def historical(self, request):
        """获取历史指标数据"""
        try:
            hours = int(request.query_params.get('hours', 24))
            service = SystemMonitorService()
            metrics = service.get_historical_metrics(request.user.tenant, hours)
            
            serializer = self.get_serializer(metrics, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"获取历史指标失败: {e}")
            return Response({'error': '获取历史指标失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def collect(self, request):
        """手动收集系统指标"""
        try:
            service = SystemMonitorService()
            metrics = service.save_system_metrics(request.user.tenant)
            
            serializer = self.get_serializer(metrics)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return Response({'error': '收集系统指标失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """进程指标视图集"""
    
    serializer_class = ProcessMetricsSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        return ProcessMetrics.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=False, methods=['post'])
    def collect(self, request):
        """收集进程指标"""
        try:
            process_names = request.data.get('process_names', None)
            service = ProcessMonitorService()
            metrics = service.save_process_metrics(request.user.tenant, process_names)
            
            serializer = self.get_serializer(metrics, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"收集进程指标失败: {e}")
            return Response({'error': '收集进程指标失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlertRuleViewSet(viewsets.ModelViewSet):
    """告警规则视图集"""
    
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        return AlertRule.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """切换规则激活状态"""
        try:
            rule = self.get_object()
            rule.is_active = not rule.is_active
            rule.save()
            
            serializer = self.get_serializer(rule)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"切换告警规则状态失败: {e}")
            return Response({'error': '操作失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    """告警视图集"""
    
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        queryset = Alert.objects.filter(tenant=self.request.user.tenant)
        
        # 状态过滤
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 严重级别过滤
        severity = self.request.query_params.get('severity', None)
        if severity:
            queryset = queryset.filter(rule__severity=severity)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def check_rules(self, request):
        """检查告警规则"""
        try:
            service = AlertService()
            alerts = service.check_alert_rules(request.user.tenant)
            
            serializer = self.get_serializer(alerts, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"检查告警规则失败: {e}")
            return Response({'error': '检查告警规则失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """确认告警"""
        try:
            service = AlertService()
            alert = service.acknowledge_alert(pk, request.user, request.user.tenant)
            
            serializer = self.get_serializer(alert)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"确认告警失败: {e}")
            return Response({'error': '确认告警失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取告警统计"""
        try:
            queryset = self.get_queryset()
            
            # 按状态统计
            status_stats = {}
            for choice in Alert.STATUS_CHOICES:
                status_stats[choice[0]] = queryset.filter(status=choice[0]).count()
            
            # 按严重级别统计
            severity_stats = {}
            for choice in AlertRule.SEVERITY_CHOICES:
                severity_stats[choice[0]] = queryset.filter(rule__severity=choice[0]).count()
            
            # 最近24小时告警数量
            last_24h = timezone.now() - timedelta(hours=24)
            recent_count = queryset.filter(fired_at__gte=last_24h).count()
            
            return Response({
                'status_stats': status_stats,
                'severity_stats': severity_stats,
                'recent_24h_count': recent_count,
                'total_count': queryset.count()
            })
            
        except Exception as e:
            logger.error(f"获取告警统计失败: {e}")
            return Response({'error': '获取告警统计失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MonitoringManagementViewSet(viewsets.ViewSet):
    """监控管理视图集"""
    
    permission_classes = [IsAuthenticated, TenantPermission]
    
    @action(detail=False, methods=['post'])
    def cleanup_metrics(self, request):
        """清理旧指标数据"""
        try:
            days_to_keep = int(request.data.get('days_to_keep', 30))
            service = MetricsCleanupService()
            result = service.cleanup_old_metrics(days_to_keep)
            
            return Response({
                'message': '清理完成',
                'deleted_counts': result
            })
            
        except Exception as e:
            logger.error(f"清理指标数据失败: {e}")
            return Response({'error': '清理失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def system_info(self, request):
        """获取系统信息"""
        try:
            import platform
            import psutil
            
            system_info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'boot_time': psutil.boot_time(),
            }
            
            return Response(system_info)
            
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return Response({'error': '获取系统信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CeleryWorkerViewSet(viewsets.ReadOnlyModelViewSet):
    """Celery Worker视图集"""
    
    serializer_class = CeleryWorkerSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        return CeleryWorker.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取Worker统计信息"""
        try:
            service = CeleryMonitorService()
            stats = service.get_worker_stats()
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"获取Worker统计信息失败: {e}")
            return Response({'error': '获取Worker统计信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def collect(self, request):
        """收集Worker统计信息"""
        try:
            service = CeleryMonitorService()
            workers = service.save_worker_stats(request.user.tenant)
            
            serializer = self.get_serializer(workers, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"收集Worker统计信息失败: {e}")
            return Response({'error': '收集Worker统计信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def restart_pool(self, request, pk=None):
        """重启Worker进程池"""
        try:
            worker = self.get_object()
            service = CeleryMonitorService()
            success = service.restart_worker_pool(worker.worker_name)
            
            if success:
                return Response({'message': 'Worker进程池重启成功'})
            else:
                return Response({'error': 'Worker进程池重启失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"重启Worker进程池失败: {e}")
            return Response({'error': '重启Worker进程池失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CeleryTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """Celery任务视图集"""
    
    serializer_class = CeleryTaskSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        queryset = CeleryTask.objects.filter(tenant=self.request.user.tenant)
        
        # 状态过滤
        state = self.request.query_params.get('state', None)
        if state:
            queryset = queryset.filter(state=state)
        
        # 任务名称过滤
        task_name = self.request.query_params.get('task_name', None)
        if task_name:
            queryset = queryset.filter(task_name__icontains=task_name)
        
        # Worker过滤
        worker_name = self.request.query_params.get('worker_name', None)
        if worker_name:
            queryset = queryset.filter(worker_name=worker_name)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取任务统计信息"""
        try:
            service = CeleryMonitorService()
            stats = service.get_task_stats()
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"获取任务统计信息失败: {e}")
            return Response({'error': '获取任务统计信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """获取失败的任务"""
        try:
            hours = int(request.query_params.get('hours', 24))
            service = CeleryMonitorService()
            failed_tasks = service.get_failed_tasks(hours)
            
            serializer = self.get_serializer(failed_tasks, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"获取失败任务失败: {e}")
            return Response({'error': '获取失败任务失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试任务"""
        try:
            task = self.get_object()
            service = CeleryMonitorService()
            success = service.retry_failed_task(task.task_id)
            
            if success:
                return Response({'message': '任务重试成功'})
            else:
                return Response({'error': '任务重试失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"重试任务失败: {e}")
            return Response({'error': '重试任务失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """撤销任务"""
        try:
            task = self.get_object()
            terminate = request.data.get('terminate', False)
            
            service = CeleryMonitorService()
            success = service.revoke_task(task.task_id, terminate)
            
            if success:
                return Response({'message': '任务撤销成功'})
            else:
                return Response({'error': '任务撤销失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"撤销任务失败: {e}")
            return Response({'error': '撤销任务失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取任务统计"""
        try:
            queryset = self.get_queryset()
            
            # 按状态统计
            state_stats = {}
            for choice in CeleryTask.STATE_CHOICES:
                state_stats[choice[0]] = queryset.filter(state=choice[0]).count()
            
            # 按任务名称统计
            task_name_stats = {}
            task_names = queryset.values_list('task_name', flat=True).distinct()
            for task_name in task_names:
                task_name_stats[task_name] = queryset.filter(task_name=task_name).count()
            
            # 最近24小时任务数量
            last_24h = timezone.now() - timedelta(hours=24)
            recent_count = queryset.filter(timestamp__gte=last_24h).count()
            
            return Response({
                'state_stats': state_stats,
                'task_name_stats': task_name_stats,
                'recent_24h_count': recent_count,
                'total_count': queryset.count()
            })
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return Response({'error': '获取任务统计失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CeleryQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """Celery队列视图集"""
    
    serializer_class = CeleryQueueSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        return CeleryQueue.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取队列统计信息"""
        try:
            service = CeleryMonitorService()
            stats = service.get_queue_stats()
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"获取队列统计信息失败: {e}")
            return Response({'error': '获取队列统计信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def collect(self, request):
        """收集队列统计信息"""
        try:
            service = CeleryMonitorService()
            queues = service.save_queue_stats(request.user.tenant)
            
            serializer = self.get_serializer(queues, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"收集队列统计信息失败: {e}")
            return Response({'error': '收集队列统计信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def purge(self, request, pk=None):
        """清空队列"""
        try:
            queue = self.get_object()
            service = CeleryMonitorService()
            purged_count = service.purge_queue(queue.queue_name)
            
            return Response({
                'message': f'队列清空成功，清理了 {purged_count} 个任务',
                'purged_count': purged_count
            })
            
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return Response({'error': '清空队列失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CeleryManagementViewSet(viewsets.ViewSet):
    """Celery管理视图集"""
    
    permission_classes = [IsAuthenticated, TenantPermission]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """获取Celery概览信息"""
        try:
            service = CeleryMonitorService()
            
            # 获取各种统计信息
            workers = service.get_worker_stats()
            tasks = service.get_task_stats(limit=10)
            queues = service.get_queue_stats()
            
            # 统计概览
            overview = {
                'workers': {
                    'total': len(workers),
                    'online': len([w for w in workers if w['status'] == 'online']),
                    'active_tasks': sum(w['active_tasks'] for w in workers),
                },
                'tasks': {
                    'total': len(tasks),
                    'pending': len([t for t in tasks if t['state'] == 'PENDING']),
                    'started': len([t for t in tasks if t['state'] == 'STARTED']),
                },
                'queues': {
                    'total': len(queues),
                    'pending_tasks': sum(q['pending_tasks'] for q in queues),
                    'active_tasks': sum(q['active_tasks'] for q in queues),
                }
            }
            
            return Response({
                'overview': overview,
                'workers': workers,
                'recent_tasks': tasks,
                'queues': queues
            })
            
        except Exception as e:
            logger.error(f"获取Celery概览信息失败: {e}")
            return Response({'error': '获取Celery概览信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """广播命令到所有Worker"""
        try:
            command = request.data.get('command')
            arguments = request.data.get('arguments', {})
            
            if not command:
                return Response({'error': '命令不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 执行广播命令
            from celery import current_app
            control = current_app.control
            
            if command == 'ping':
                result = control.ping()
            elif command == 'stats':
                result = control.inspect().stats()
            elif command == 'active':
                result = control.inspect().active()
            elif command == 'scheduled':
                result = control.inspect().scheduled()
            elif command == 'reserved':
                result = control.inspect().reserved()
            else:
                return Response({'error': '不支持的命令'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'command': command,
                'result': result
            })
            
        except Exception as e:
            logger.error(f"广播命令失败: {e}")
            return Response({'error': '广播命令失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)