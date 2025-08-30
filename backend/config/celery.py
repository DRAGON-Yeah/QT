"""
Celery配置文件
"""
import os
from celery import Celery
from celery.schedules import crontab

# 设置默认Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('quanttrade')

# 使用字符串配置，这样worker不需要序列化配置对象
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 定期任务配置
app.conf.beat_schedule = {
    # 每分钟收集系统指标
    'collect-system-metrics': {
        'task': 'apps.monitoring.tasks.collect_system_metrics',
        'schedule': crontab(minute='*'),  # 每分钟执行
    },
    # 每5分钟收集进程指标
    'collect-process-metrics': {
        'task': 'apps.monitoring.tasks.collect_process_metrics',
        'schedule': crontab(minute='*/5'),  # 每5分钟执行
    },
    # 每分钟检查告警规则
    'check-alert-rules': {
        'task': 'apps.monitoring.tasks.check_alert_rules',
        'schedule': crontab(minute='*'),  # 每分钟执行
    },
    # 每天凌晨2点清理旧数据
    'cleanup-old-metrics': {
        'task': 'apps.monitoring.tasks.cleanup_old_metrics',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
        'kwargs': {'days_to_keep': 30}
    },
    # 每小时生成监控报告
    'generate-monitoring-report': {
        'task': 'apps.monitoring.tasks.generate_monitoring_report',
        'schedule': crontab(minute=0),  # 每小时执行
    },
    # 每5分钟进行系统健康检查
    'system-health-check': {
        'task': 'apps.monitoring.tasks.system_health_check',
        'schedule': crontab(minute='*/5'),  # 每5分钟执行
    },
    # 每2分钟收集Celery统计信息
    'collect-celery-stats': {
        'task': 'apps.monitoring.tasks.collect_celery_stats',
        'schedule': crontab(minute='*/2'),  # 每2分钟执行
    },
    # 每天凌晨3点清理Celery历史数据
    'cleanup-celery-data': {
        'task': 'apps.monitoring.tasks.cleanup_celery_data',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨3点执行
        'kwargs': {'days_to_keep': 7}
    },
}

# 时区设置
app.conf.timezone = 'Asia/Shanghai'

# 调试任务
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')