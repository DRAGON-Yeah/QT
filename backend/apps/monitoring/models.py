from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TenantModel
from decimal import Decimal

User = get_user_model()


class SystemMetrics(TenantModel):
    """系统性能指标模型"""
    
    # CPU指标
    cpu_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="CPU使用率(%)")
    cpu_count = models.IntegerField(help_text="CPU核心数")
    load_average_1m = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="1分钟负载平均值")
    load_average_5m = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="5分钟负载平均值")
    load_average_15m = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="15分钟负载平均值")
    
    # 内存指标
    memory_total = models.BigIntegerField(help_text="总内存(bytes)")
    memory_available = models.BigIntegerField(help_text="可用内存(bytes)")
    memory_used = models.BigIntegerField(help_text="已用内存(bytes)")
    memory_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="内存使用率(%)")
    
    # 磁盘指标
    disk_total = models.BigIntegerField(help_text="总磁盘空间(bytes)")
    disk_used = models.BigIntegerField(help_text="已用磁盘空间(bytes)")
    disk_free = models.BigIntegerField(help_text="可用磁盘空间(bytes)")
    disk_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="磁盘使用率(%)")
    
    # 网络指标
    network_bytes_sent = models.BigIntegerField(help_text="网络发送字节数")
    network_bytes_recv = models.BigIntegerField(help_text="网络接收字节数")
    network_packets_sent = models.BigIntegerField(help_text="网络发送包数")
    network_packets_recv = models.BigIntegerField(help_text="网络接收包数")
    
    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True, help_text="采集时间")
    
    class Meta:
        db_table = 'monitoring_system_metrics'
        verbose_name = '系统指标'
        verbose_name_plural = '系统指标'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]


class ProcessMetrics(TenantModel):
    """进程监控指标模型"""
    
    process_name = models.CharField(max_length=100, help_text="进程名称")
    pid = models.IntegerField(help_text="进程ID")
    cpu_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="CPU使用率(%)")
    memory_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="内存使用率(%)")
    memory_rss = models.BigIntegerField(help_text="物理内存使用(bytes)")
    memory_vms = models.BigIntegerField(help_text="虚拟内存使用(bytes)")
    status = models.CharField(max_length=20, help_text="进程状态")
    create_time = models.DateTimeField(help_text="进程创建时间")
    num_threads = models.IntegerField(help_text="线程数")
    
    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True, help_text="采集时间")
    
    class Meta:
        db_table = 'monitoring_process_metrics'
        verbose_name = '进程指标'
        verbose_name_plural = '进程指标'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'process_name', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]


class AlertRule(TenantModel):
    """监控告警规则模型"""
    
    METRIC_CHOICES = [
        ('cpu_percent', 'CPU使用率'),
        ('memory_percent', '内存使用率'),
        ('disk_percent', '磁盘使用率'),
        ('load_average_1m', '1分钟负载'),
        ('load_average_5m', '5分钟负载'),
        ('load_average_15m', '15分钟负载'),
    ]
    
    OPERATOR_CHOICES = [
        ('>', '大于'),
        ('>=', '大于等于'),
        ('<', '小于'),
        ('<=', '小于等于'),
        ('==', '等于'),
        ('!=', '不等于'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('critical', '严重'),
    ]
    
    name = models.CharField(max_length=100, help_text="规则名称")
    description = models.TextField(blank=True, help_text="规则描述")
    metric = models.CharField(max_length=50, choices=METRIC_CHOICES, help_text="监控指标")
    operator = models.CharField(max_length=5, choices=OPERATOR_CHOICES, help_text="比较操作符")
    threshold = models.DecimalField(max_digits=10, decimal_places=2, help_text="阈值")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='warning', help_text="告警级别")
    is_active = models.BooleanField(default=True, help_text="是否启用")
    
    # 告警配置
    notification_enabled = models.BooleanField(default=True, help_text="是否发送通知")
    email_notification = models.BooleanField(default=False, help_text="邮件通知")
    webhook_url = models.URLField(blank=True, help_text="Webhook URL")
    
    class Meta:
        db_table = 'monitoring_alert_rule'
        verbose_name = '告警规则'
        verbose_name_plural = '告警规则'
        unique_together = ['tenant', 'name']


class Alert(TenantModel):
    """告警记录模型"""
    
    STATUS_CHOICES = [
        ('firing', '触发中'),
        ('resolved', '已解决'),
        ('acknowledged', '已确认'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, help_text="告警规则")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='firing', help_text="告警状态")
    message = models.TextField(help_text="告警消息")
    current_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="当前值")
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="阈值")
    
    # 时间信息
    fired_at = models.DateTimeField(auto_now_add=True, help_text="触发时间")
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="解决时间")
    acknowledged_at = models.DateTimeField(null=True, blank=True, help_text="确认时间")
    acknowledged_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, help_text="确认人")
    
    class Meta:
        db_table = 'monitoring_alert'
        verbose_name = '告警记录'
        verbose_name_plural = '告警记录'
        ordering = ['-fired_at']
        indexes = [
            models.Index(fields=['tenant', 'status', 'fired_at']),
            models.Index(fields=['fired_at']),
        ]


class CeleryWorker(TenantModel):
    """Celery Worker监控模型"""
    
    STATUS_CHOICES = [
        ('online', '在线'),
        ('offline', '离线'),
        ('unknown', '未知'),
    ]
    
    worker_name = models.CharField(max_length=100, help_text="Worker名称")
    hostname = models.CharField(max_length=100, help_text="主机名")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown', help_text="状态")
    active_tasks = models.IntegerField(default=0, help_text="活跃任务数")
    processed_tasks = models.BigIntegerField(default=0, help_text="已处理任务数")
    load_average = models.JSONField(default=list, help_text="负载平均值")
    last_heartbeat = models.DateTimeField(null=True, blank=True, help_text="最后心跳时间")
    
    # 资源使用情况
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="CPU使用率")
    memory_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="内存使用率")
    
    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True, help_text="记录时间")
    
    class Meta:
        db_table = 'monitoring_celery_worker'
        verbose_name = 'Celery Worker'
        verbose_name_plural = 'Celery Workers'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'worker_name', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]


class CeleryTask(TenantModel):
    """Celery任务监控模型"""
    
    STATE_CHOICES = [
        ('PENDING', '等待中'),
        ('STARTED', '已开始'),
        ('SUCCESS', '成功'),
        ('FAILURE', '失败'),
        ('RETRY', '重试中'),
        ('REVOKED', '已撤销'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True, help_text="任务ID")
    task_name = models.CharField(max_length=255, help_text="任务名称")
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='PENDING', help_text="任务状态")
    worker_name = models.CharField(max_length=100, blank=True, help_text="执行Worker")
    
    # 任务参数和结果
    args = models.JSONField(default=list, help_text="任务参数")
    kwargs = models.JSONField(default=dict, help_text="任务关键字参数")
    result = models.JSONField(null=True, blank=True, help_text="任务结果")
    traceback = models.TextField(blank=True, help_text="错误堆栈")
    
    # 时间信息
    eta = models.DateTimeField(null=True, blank=True, help_text="预计执行时间")
    expires = models.DateTimeField(null=True, blank=True, help_text="过期时间")
    started_at = models.DateTimeField(null=True, blank=True, help_text="开始时间")
    succeeded_at = models.DateTimeField(null=True, blank=True, help_text="成功时间")
    failed_at = models.DateTimeField(null=True, blank=True, help_text="失败时间")
    
    # 执行信息
    retries = models.IntegerField(default=0, help_text="重试次数")
    runtime = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="执行时长(秒)")
    
    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True, help_text="创建时间")
    
    class Meta:
        db_table = 'monitoring_celery_task'
        verbose_name = 'Celery任务'
        verbose_name_plural = 'Celery任务'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'task_name', 'state']),
            models.Index(fields=['state', 'timestamp']),
            models.Index(fields=['worker_name', 'timestamp']),
        ]


class CeleryQueue(TenantModel):
    """Celery队列监控模型"""
    
    queue_name = models.CharField(max_length=100, help_text="队列名称")
    
    # 队列统计
    pending_tasks = models.IntegerField(default=0, help_text="等待任务数")
    active_tasks = models.IntegerField(default=0, help_text="活跃任务数")
    scheduled_tasks = models.IntegerField(default=0, help_text="计划任务数")
    
    # 队列配置
    routing_key = models.CharField(max_length=255, blank=True, help_text="路由键")
    exchange = models.CharField(max_length=255, blank=True, help_text="交换机")
    exchange_type = models.CharField(max_length=50, blank=True, help_text="交换机类型")
    
    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True, help_text="记录时间")
    
    class Meta:
        db_table = 'monitoring_celery_queue'
        verbose_name = 'Celery队列'
        verbose_name_plural = 'Celery队列'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'queue_name', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]