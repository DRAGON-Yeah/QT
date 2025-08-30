from rest_framework import serializers
from .models import SystemMetrics, ProcessMetrics, AlertRule, Alert, CeleryWorker, CeleryTask, CeleryQueue


class SystemMetricsSerializer(serializers.ModelSerializer):
    """系统指标序列化器"""
    
    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'cpu_percent', 'cpu_count', 'load_average_1m', 'load_average_5m', 'load_average_15m',
            'memory_total', 'memory_available', 'memory_used', 'memory_percent',
            'disk_total', 'disk_used', 'disk_free', 'disk_percent',
            'network_bytes_sent', 'network_bytes_recv', 'network_packets_sent', 'network_packets_recv',
            'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class ProcessMetricsSerializer(serializers.ModelSerializer):
    """进程指标序列化器"""
    
    class Meta:
        model = ProcessMetrics
        fields = [
            'id', 'process_name', 'pid', 'cpu_percent', 'memory_percent',
            'memory_rss', 'memory_vms', 'status', 'create_time', 'num_threads', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class AlertRuleSerializer(serializers.ModelSerializer):
    """告警规则序列化器"""
    
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)
    operator_display = serializers.CharField(source='get_operator_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'metric', 'metric_display', 'operator', 'operator_display',
            'threshold', 'severity', 'severity_display', 'is_active', 'notification_enabled',
            'email_notification', 'webhook_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_threshold(self, value):
        """验证阈值"""
        if value < 0:
            raise serializers.ValidationError("阈值不能为负数")
        return value
    
    def validate_webhook_url(self, value):
        """验证Webhook URL"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Webhook URL必须以http://或https://开头")
        return value


class AlertSerializer(serializers.ModelSerializer):
    """告警序列化器"""
    
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_severity = serializers.CharField(source='rule.severity', read_only=True)
    rule_severity_display = serializers.CharField(source='rule.get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'rule', 'rule_name', 'rule_severity', 'rule_severity_display',
            'status', 'status_display', 'message', 'current_value', 'threshold_value',
            'fired_at', 'resolved_at', 'acknowledged_at', 'acknowledged_by', 'acknowledged_by_username'
        ]
        read_only_fields = [
            'id', 'rule_name', 'rule_severity', 'rule_severity_display', 'status_display',
            'acknowledged_by_username', 'fired_at', 'resolved_at', 'acknowledged_at'
        ]


class MetricsStatisticsSerializer(serializers.Serializer):
    """指标统计序列化器"""
    
    avg_cpu = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    max_cpu = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    min_cpu = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    avg_memory = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    max_memory = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    min_memory = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    avg_disk = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    max_disk = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    min_disk = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)


class AlertStatisticsSerializer(serializers.Serializer):
    """告警统计序列化器"""
    
    status_stats = serializers.DictField()
    severity_stats = serializers.DictField()
    recent_24h_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class SystemInfoSerializer(serializers.Serializer):
    """系统信息序列化器"""
    
    platform = serializers.CharField()
    system = serializers.CharField()
    release = serializers.CharField()
    version = serializers.CharField()
    machine = serializers.CharField()
    processor = serializers.CharField()
    python_version = serializers.CharField()
    cpu_count = serializers.IntegerField()
    memory_total = serializers.IntegerField()
    disk_total = serializers.IntegerField()
    boot_time = serializers.FloatField()


class CeleryWorkerSerializer(serializers.ModelSerializer):
    """Celery Worker序列化器"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CeleryWorker
        fields = [
            'id', 'worker_name', 'hostname', 'status', 'status_display',
            'active_tasks', 'processed_tasks', 'load_average', 'last_heartbeat',
            'cpu_usage', 'memory_usage', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class CeleryTaskSerializer(serializers.ModelSerializer):
    """Celery任务序列化器"""
    
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CeleryTask
        fields = [
            'id', 'task_id', 'task_name', 'state', 'state_display', 'worker_name',
            'args', 'kwargs', 'result', 'traceback', 'eta', 'expires',
            'started_at', 'succeeded_at', 'failed_at', 'retries', 'runtime',
            'duration', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp', 'duration']
    
    def get_duration(self, obj):
        """计算任务执行时长"""
        if obj.started_at and obj.succeeded_at:
            return (obj.succeeded_at - obj.started_at).total_seconds()
        elif obj.started_at and obj.failed_at:
            return (obj.failed_at - obj.started_at).total_seconds()
        return None


class CeleryQueueSerializer(serializers.ModelSerializer):
    """Celery队列序列化器"""
    
    total_tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = CeleryQueue
        fields = [
            'id', 'queue_name', 'pending_tasks', 'active_tasks', 'scheduled_tasks',
            'total_tasks', 'routing_key', 'exchange', 'exchange_type', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp', 'total_tasks']
    
    def get_total_tasks(self, obj):
        """计算队列总任务数"""
        return obj.pending_tasks + obj.active_tasks + obj.scheduled_tasks


class CeleryOverviewSerializer(serializers.Serializer):
    """Celery概览序列化器"""
    
    workers = serializers.DictField()
    tasks = serializers.DictField()
    queues = serializers.DictField()


class CeleryTaskStatisticsSerializer(serializers.Serializer):
    """Celery任务统计序列化器"""
    
    state_stats = serializers.DictField()
    task_name_stats = serializers.DictField()
    recent_24h_count = serializers.IntegerField()
    total_count = serializers.IntegerField()