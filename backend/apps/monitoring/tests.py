from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, Mock
from .models import SystemMetrics, ProcessMetrics, AlertRule, Alert
from .services import SystemMonitorService, ProcessMonitorService, AlertService, MetricsCleanupService
from apps.users.models import Tenant

User = get_user_model()


class SystemMonitorServiceTest(TestCase):
    """系统监控服务测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            tenant=self.tenant
        )
    
    @patch('psutil.cpu_percent')
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_collect_system_metrics(self, mock_net, mock_disk, mock_memory, mock_cpu_count, mock_cpu_percent):
        """测试收集系统指标"""
        # 模拟psutil返回值
        mock_cpu_percent.return_value = 50.5
        mock_cpu_count.return_value = 4
        
        mock_memory_obj = Mock()
        mock_memory_obj.total = 8589934592  # 8GB
        mock_memory_obj.available = 4294967296  # 4GB
        mock_memory_obj.used = 4294967296  # 4GB
        mock_memory_obj.percent = 50.0
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.total = 1099511627776  # 1TB
        mock_disk_obj.used = 549755813888  # 500GB
        mock_disk_obj.free = 549755813888  # 500GB
        mock_disk.return_value = mock_disk_obj
        
        mock_net_obj = Mock()
        mock_net_obj.bytes_sent = 1000000
        mock_net_obj.bytes_recv = 2000000
        mock_net_obj.packets_sent = 1000
        mock_net_obj.packets_recv = 2000
        mock_net.return_value = mock_net_obj
        
        # 测试收集指标
        service = SystemMonitorService()
        metrics = service.collect_system_metrics()
        
        # 验证结果
        self.assertEqual(metrics['cpu_percent'], Decimal('50.5'))
        self.assertEqual(metrics['cpu_count'], 4)
        self.assertEqual(metrics['memory_total'], 8589934592)
        self.assertEqual(metrics['memory_percent'], Decimal('50.0'))
        self.assertEqual(metrics['disk_total'], 1099511627776)
        self.assertEqual(metrics['network_bytes_sent'], 1000000)
    
    def test_save_system_metrics(self):
        """测试保存系统指标"""
        with patch.object(SystemMonitorService, 'collect_system_metrics') as mock_collect:
            mock_collect.return_value = {
                'cpu_percent': Decimal('50.0'),
                'cpu_count': 4,
                'load_average_1m': None,
                'load_average_5m': None,
                'load_average_15m': None,
                'memory_total': 8589934592,
                'memory_available': 4294967296,
                'memory_used': 4294967296,
                'memory_percent': Decimal('50.0'),
                'disk_total': 1099511627776,
                'disk_used': 549755813888,
                'disk_free': 549755813888,
                'disk_percent': Decimal('50.0'),
                'network_bytes_sent': 1000000,
                'network_bytes_recv': 2000000,
                'network_packets_sent': 1000,
                'network_packets_recv': 2000,
            }
            
            service = SystemMonitorService()
            metrics = service.save_system_metrics(self.tenant)
            
            # 验证数据库记录
            self.assertIsInstance(metrics, SystemMetrics)
            self.assertEqual(metrics.tenant, self.tenant)
            self.assertEqual(metrics.cpu_percent, Decimal('50.0'))
            self.assertEqual(metrics.memory_percent, Decimal('50.0'))
    
    def test_get_historical_metrics(self):
        """测试获取历史指标"""
        # 创建测试数据
        now = timezone.now()
        
        # 创建24小时内的指标
        SystemMetrics.objects.create(
            tenant=self.tenant,
            cpu_percent=Decimal('30.0'),
            cpu_count=4,
            memory_total=8589934592,
            memory_available=4294967296,
            memory_used=4294967296,
            memory_percent=Decimal('50.0'),
            disk_total=1099511627776,
            disk_used=549755813888,
            disk_free=549755813888,
            disk_percent=Decimal('50.0'),
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            network_packets_sent=1000,
            network_packets_recv=2000,
            timestamp=now - timedelta(hours=12)
        )
        
        # 创建24小时外的指标
        SystemMetrics.objects.create(
            tenant=self.tenant,
            cpu_percent=Decimal('40.0'),
            cpu_count=4,
            memory_total=8589934592,
            memory_available=4294967296,
            memory_used=4294967296,
            memory_percent=Decimal('50.0'),
            disk_total=1099511627776,
            disk_used=549755813888,
            disk_free=549755813888,
            disk_percent=Decimal('50.0'),
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            network_packets_sent=1000,
            network_packets_recv=2000,
            timestamp=now - timedelta(hours=36)
        )
        
        service = SystemMonitorService()
        metrics = service.get_historical_metrics(self.tenant, hours=24)
        
        # 应该只返回24小时内的数据
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].cpu_percent, Decimal('30.0'))


class ProcessMonitorServiceTest(TestCase):
    """进程监控服务测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant')
    
    @patch('psutil.process_iter')
    def test_collect_process_metrics(self, mock_process_iter):
        """测试收集进程指标"""
        # 模拟进程信息
        mock_proc = Mock()
        mock_proc.info = {
            'pid': 1234,
            'name': 'python',
            'cpu_percent': 10.5,
            'memory_percent': 5.2,
            'memory_info': Mock(rss=1048576, vms=2097152),
            'status': 'running',
            'create_time': 1640995200.0,  # 2022-01-01 00:00:00
            'num_threads': 4
        }
        mock_process_iter.return_value = [mock_proc]
        
        service = ProcessMonitorService()
        metrics = service.collect_process_metrics(['python'])
        
        # 验证结果
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0]['process_name'], 'python')
        self.assertEqual(metrics[0]['pid'], 1234)
        self.assertEqual(metrics[0]['cpu_percent'], Decimal('10.5'))


class AlertServiceTest(TestCase):
    """告警服务测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            tenant=self.tenant
        )
        
        # 创建告警规则
        self.alert_rule = AlertRule.objects.create(
            tenant=self.tenant,
            name='CPU使用率告警',
            description='CPU使用率超过80%时告警',
            metric='cpu_percent',
            operator='>',
            threshold=Decimal('80.0'),
            severity='warning',
            is_active=True
        )
    
    def test_check_alert_rules_trigger(self):
        """测试告警规则触发"""
        # 创建高CPU使用率的系统指标
        SystemMetrics.objects.create(
            tenant=self.tenant,
            cpu_percent=Decimal('85.0'),  # 超过阈值
            cpu_count=4,
            memory_total=8589934592,
            memory_available=4294967296,
            memory_used=4294967296,
            memory_percent=Decimal('50.0'),
            disk_total=1099511627776,
            disk_used=549755813888,
            disk_free=549755813888,
            disk_percent=Decimal('50.0'),
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            network_packets_sent=1000,
            network_packets_recv=2000,
        )
        
        service = AlertService()
        alerts = service.check_alert_rules(self.tenant)
        
        # 应该触发一个告警
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule, self.alert_rule)
        self.assertEqual(alerts[0].status, 'firing')
        self.assertEqual(alerts[0].current_value, Decimal('85.0'))
    
    def test_check_alert_rules_no_trigger(self):
        """测试告警规则不触发"""
        # 创建正常CPU使用率的系统指标
        SystemMetrics.objects.create(
            tenant=self.tenant,
            cpu_percent=Decimal('50.0'),  # 未超过阈值
            cpu_count=4,
            memory_total=8589934592,
            memory_available=4294967296,
            memory_used=4294967296,
            memory_percent=Decimal('50.0'),
            disk_total=1099511627776,
            disk_used=549755813888,
            disk_free=549755813888,
            disk_percent=Decimal('50.0'),
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            network_packets_sent=1000,
            network_packets_recv=2000,
        )
        
        service = AlertService()
        alerts = service.check_alert_rules(self.tenant)
        
        # 不应该触发告警
        self.assertEqual(len(alerts), 0)
    
    def test_acknowledge_alert(self):
        """测试确认告警"""
        # 创建告警
        alert = Alert.objects.create(
            tenant=self.tenant,
            rule=self.alert_rule,
            status='firing',
            message='CPU使用率过高',
            current_value=Decimal('85.0'),
            threshold_value=Decimal('80.0')
        )
        
        service = AlertService()
        acknowledged_alert = service.acknowledge_alert(alert.id, self.user, self.tenant)
        
        # 验证告警已确认
        self.assertEqual(acknowledged_alert.status, 'acknowledged')
        self.assertEqual(acknowledged_alert.acknowledged_by, self.user)
        self.assertIsNotNone(acknowledged_alert.acknowledged_at)


class MetricsCleanupServiceTest(TestCase):
    """指标清理服务测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant')
    
    def test_cleanup_old_metrics(self):
        """测试清理旧指标数据"""
        now = timezone.now()
        
        # 创建新数据（保留）
        SystemMetrics.objects.create(
            tenant=self.tenant,
            cpu_percent=Decimal('30.0'),
            cpu_count=4,
            memory_total=8589934592,
            memory_available=4294967296,
            memory_used=4294967296,
            memory_percent=Decimal('50.0'),
            disk_total=1099511627776,
            disk_used=549755813888,
            disk_free=549755813888,
            disk_percent=Decimal('50.0'),
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            network_packets_sent=1000,
            network_packets_recv=2000,
            timestamp=now - timedelta(days=15)
        )
        
        # 创建旧数据（删除）
        old_metrics = SystemMetrics.objects.create(
            tenant=self.tenant,
            cpu_percent=Decimal('40.0'),
            cpu_count=4,
            memory_total=8589934592,
            memory_available=4294967296,
            memory_used=4294967296,
            memory_percent=Decimal('50.0'),
            disk_total=1099511627776,
            disk_used=549755813888,
            disk_free=549755813888,
            disk_percent=Decimal('50.0'),
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            network_packets_sent=1000,
            network_packets_recv=2000,
            timestamp=now - timedelta(days=35)
        )
        
        service = MetricsCleanupService()
        result = service.cleanup_old_metrics(days_to_keep=30)
        
        # 验证旧数据被删除
        self.assertEqual(result['system_metrics'], 1)
        self.assertFalse(SystemMetrics.objects.filter(id=old_metrics.id).exists())
        
        # 验证新数据保留
        self.assertEqual(SystemMetrics.objects.filter(tenant=self.tenant).count(), 1)


class MonitoringModelsTest(TestCase):
    """监控模型测试"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Test Tenant')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            tenant=self.tenant
        )
    
    def test_system_metrics_creation(self):
        """测试系统指标模型创建"""
        metrics = SystemMetrics.objects.create(
            tenant=self.tenant,
            cpu_percent=Decimal('50.0'),
            cpu_count=4,
            memory_total=8589934592,
            memory_available=4294967296,
            memory_used=4294967296,
            memory_percent=Decimal('50.0'),
            disk_total=1099511627776,
            disk_used=549755813888,
            disk_free=549755813888,
            disk_percent=Decimal('50.0'),
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            network_packets_sent=1000,
            network_packets_recv=2000,
        )
        
        self.assertEqual(metrics.tenant, self.tenant)
        self.assertEqual(metrics.cpu_percent, Decimal('50.0'))
        self.assertIsNotNone(metrics.timestamp)
    
    def test_alert_rule_creation(self):
        """测试告警规则模型创建"""
        rule = AlertRule.objects.create(
            tenant=self.tenant,
            name='测试规则',
            description='测试描述',
            metric='cpu_percent',
            operator='>',
            threshold=Decimal('80.0'),
            severity='warning'
        )
        
        self.assertEqual(rule.tenant, self.tenant)
        self.assertEqual(rule.name, '测试规则')
        self.assertTrue(rule.is_active)
        self.assertTrue(rule.notification_enabled)
    
    def test_alert_creation(self):
        """测试告警模型创建"""
        rule = AlertRule.objects.create(
            tenant=self.tenant,
            name='测试规则',
            metric='cpu_percent',
            operator='>',
            threshold=Decimal('80.0'),
            severity='warning'
        )
        
        alert = Alert.objects.create(
            tenant=self.tenant,
            rule=rule,
            message='测试告警',
            current_value=Decimal('85.0'),
            threshold_value=Decimal('80.0')
        )
        
        self.assertEqual(alert.tenant, self.tenant)
        self.assertEqual(alert.rule, rule)
        self.assertEqual(alert.status, 'firing')
        self.assertIsNotNone(alert.fired_at)