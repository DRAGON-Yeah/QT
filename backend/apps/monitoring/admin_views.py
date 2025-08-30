"""
运维管理后台视图
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta
from django.utils import timezone
import json
import subprocess
import os
import logging

from .services import SystemMonitorService, ProcessMonitorService, AlertService
from .celery_services import CeleryMonitorService
from .models import SystemMetrics, ProcessMetrics, Alert, CeleryWorker, CeleryTask
from apps.core.permissions import AdminPermission

logger = logging.getLogger(__name__)


@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(View):
    """管理员仪表盘视图"""
    
    def get(self, request):
        """显示管理员仪表盘"""
        try:
            # 获取系统概览数据
            system_service = SystemMonitorService()
            celery_service = CeleryMonitorService()
            
            # 最新系统指标
            latest_metrics = system_service.get_latest_metrics()
            
            # Celery统计
            workers = celery_service.get_worker_stats()
            tasks = celery_service.get_task_stats(limit=5)
            
            # 最近告警
            recent_alerts = Alert.objects.filter(
                fired_at__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-fired_at')[:10]
            
            context = {
                'system_metrics': latest_metrics,
                'workers': workers,
                'recent_tasks': tasks,
                'recent_alerts': recent_alerts,
                'total_alerts': recent_alerts.count(),
            }
            
            return render(request, 'monitoring/admin_dashboard.html', context)
            
        except Exception as e:
            logger.error(f"管理员仪表盘加载失败: {e}")
            return render(request, 'monitoring/admin_dashboard.html', {
                'error': '仪表盘数据加载失败'
            })


class AdminMonitoringViewSet(viewsets.ViewSet):
    """管理员监控视图集"""
    
    permission_classes = [IsAuthenticated, AdminPermission]
    
    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        """获取仪表盘数据"""
        try:
            # 系统指标
            system_service = SystemMonitorService()
            latest_metrics = system_service.get_latest_metrics()
            
            # 24小时指标摘要
            metrics_summary = system_service.get_metrics_summary(hours=24)
            
            # Celery统计
            celery_service = CeleryMonitorService()
            workers = celery_service.get_worker_stats()
            
            # 告警统计
            alert_stats = {
                'total': Alert.objects.count(),
                'firing': Alert.objects.filter(status='firing').count(),
                'resolved': Alert.objects.filter(status='resolved').count(),
                'acknowledged': Alert.objects.filter(status='acknowledged').count(),
            }
            
            # 最近24小时的系统指标趋势
            historical_metrics = system_service.get_historical_metrics(hours=24)
            
            # 构建趋势数据
            trend_data = []
            for metric in historical_metrics:
                trend_data.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_percent': float(metric.cpu_percent),
                    'memory_percent': float(metric.memory_percent),
                    'disk_percent': float(metric.disk_percent),
                })
            
            return Response({
                'system_metrics': latest_metrics,
                'metrics_summary': metrics_summary,
                'workers': workers,
                'alert_stats': alert_stats,
                'trend_data': trend_data[-50:],  # 最近50个数据点
            })
            
        except Exception as e:
            logger.error(f"获取仪表盘数据失败: {e}")
            return Response({'error': '获取仪表盘数据失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def system_status(self, request):
        """获取系统状态"""
        try:
            import platform
            import psutil
            from django.db import connection
            from django.core.cache import cache
            
            # 系统信息
            system_info = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'boot_time': psutil.boot_time(),
            }
            
            # 服务状态检查
            services_status = {}
            
            # 数据库状态
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                services_status['database'] = {'status': 'healthy', 'message': '数据库连接正常'}
            except Exception as e:
                services_status['database'] = {'status': 'unhealthy', 'message': f'数据库连接失败: {str(e)}'}
            
            # 缓存状态
            try:
                cache.set('health_check', 'ok', 10)
                cache.get('health_check')
                services_status['cache'] = {'status': 'healthy', 'message': '缓存服务正常'}
            except Exception as e:
                services_status['cache'] = {'status': 'unhealthy', 'message': f'缓存服务失败: {str(e)}'}
            
            # Celery状态
            try:
                celery_service = CeleryMonitorService()
                workers = celery_service.get_worker_stats()
                if workers:
                    services_status['celery'] = {'status': 'healthy', 'message': f'发现 {len(workers)} 个Worker'}
                else:
                    services_status['celery'] = {'status': 'warning', 'message': '没有发现活跃的Worker'}
            except Exception as e:
                services_status['celery'] = {'status': 'unhealthy', 'message': f'Celery检查失败: {str(e)}'}
            
            return Response({
                'system_info': system_info,
                'services_status': services_status,
                'timestamp': timezone.now().isoformat(),
            })
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return Response({'error': '获取系统状态失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def restart_service(self, request):
        """重启服务"""
        try:
            service_name = request.data.get('service_name')
            
            if not service_name:
                return Response({'error': '服务名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 这里只是示例，实际生产环境需要更安全的实现
            if service_name == 'celery':
                # 重启Celery Worker
                try:
                    from celery import current_app
                    current_app.control.pool_restart()
                    return Response({'message': 'Celery Worker重启成功'})
                except Exception as e:
                    return Response({'error': f'Celery重启失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elif service_name == 'cache':
                # 清理缓存
                try:
                    from django.core.cache import cache
                    cache.clear()
                    return Response({'message': '缓存清理成功'})
                except Exception as e:
                    return Response({'error': f'缓存清理失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            else:
                return Response({'error': '不支持的服务类型'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"重启服务失败: {e}")
            return Response({'error': '重启服务失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def logs(self, request):
        """获取系统日志"""
        try:
            log_type = request.query_params.get('type', 'django')
            lines = int(request.query_params.get('lines', 100))
            
            log_files = {
                'django': 'logs/django.log',
                'celery': 'logs/celery.log',
                'nginx': '/var/log/nginx/access.log',
                'system': '/var/log/syslog',
            }
            
            log_file = log_files.get(log_type)
            if not log_file:
                return Response({'error': '不支持的日志类型'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 读取日志文件
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_lines = f.readlines()
                        # 返回最后N行
                        recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
                        
                        return Response({
                            'log_type': log_type,
                            'lines': recent_lines,
                            'total_lines': len(log_lines),
                        })
                else:
                    return Response({
                        'log_type': log_type,
                        'lines': [],
                        'message': f'日志文件 {log_file} 不存在',
                    })
                    
            except PermissionError:
                return Response({'error': '没有权限读取日志文件'}, status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                return Response({'error': f'读取日志失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"获取日志失败: {e}")
            return Response({'error': '获取日志失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def execute_command(self, request):
        """执行系统命令（仅限管理员）"""
        try:
            command = request.data.get('command')
            
            if not command:
                return Response({'error': '命令不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 安全检查：只允许特定的安全命令
            allowed_commands = [
                'ps aux',
                'df -h',
                'free -h',
                'uptime',
                'whoami',
                'pwd',
                'ls -la',
                'netstat -tlnp',
                'systemctl status',
            ]
            
            # 检查命令是否在允许列表中
            command_safe = False
            for allowed in allowed_commands:
                if command.startswith(allowed):
                    command_safe = True
                    break
            
            if not command_safe:
                return Response({'error': '不允许执行此命令'}, status=status.HTTP_403_FORBIDDEN)
            
            # 执行命令
            try:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30秒超时
                    check=False
                )
                
                return Response({
                    'command': command,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode,
                })
                
            except subprocess.TimeoutExpired:
                return Response({'error': '命令执行超时'}, status=status.HTTP_408_REQUEST_TIMEOUT)
            except Exception as e:
                return Response({'error': f'命令执行失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return Response({'error': '执行命令失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@staff_member_required
@require_http_methods(["GET"])
def system_logs_view(request):
    """系统日志查看页面"""
    return render(request, 'monitoring/system_logs.html')


@staff_member_required
@require_http_methods(["GET"])
def celery_management_view(request):
    """Celery管理页面"""
    return render(request, 'monitoring/celery_management.html')


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def emergency_action(request):
    """紧急操作接口"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'stop_all_tasks':
            # 停止所有Celery任务
            from celery import current_app
            current_app.control.purge()
            return JsonResponse({'message': '所有任务已停止'})
        
        elif action == 'restart_workers':
            # 重启所有Worker
            from celery import current_app
            current_app.control.pool_restart()
            return JsonResponse({'message': '所有Worker已重启'})
        
        elif action == 'clear_cache':
            # 清理所有缓存
            from django.core.cache import cache
            cache.clear()
            return JsonResponse({'message': '缓存已清理'})
        
        else:
            return JsonResponse({'error': '不支持的操作'}, status=400)
            
    except Exception as e:
        logger.error(f"紧急操作失败: {e}")
        return JsonResponse({'error': '操作失败'}, status=500)