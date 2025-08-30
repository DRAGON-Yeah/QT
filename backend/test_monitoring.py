#!/usr/bin/env python3
"""
简单的监控功能测试脚本
"""
import os
import sys
import django
from pathlib import Path

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 简化的Django设置，用于测试
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'apps.core',
            'apps.users',
            'apps.monitoring',
        ],
        SECRET_KEY='test-key',
        USE_TZ=True,
        TIME_ZONE='Asia/Shanghai',
    )

django.setup()

# 现在可以导入Django模型和服务
from apps.monitoring.services import SystemMonitorService
import psutil

def test_system_monitor_service():
    """测试系统监控服务"""
    print("测试系统监控服务...")
    
    try:
        service = SystemMonitorService()
        
        # 测试收集系统指标
        print("收集系统指标...")
        metrics = service.collect_system_metrics()
        
        print(f"CPU使用率: {metrics['cpu_percent']}%")
        print(f"CPU核心数: {metrics['cpu_count']}")
        print(f"内存使用率: {metrics['memory_percent']}%")
        print(f"磁盘使用率: {metrics['disk_percent']}%")
        
        # 验证数据类型
        assert isinstance(metrics['cpu_percent'], type(metrics['cpu_percent']))
        assert metrics['cpu_count'] > 0
        assert 0 <= float(metrics['memory_percent']) <= 100
        assert 0 <= float(metrics['disk_percent']) <= 100
        
        print("✓ 系统监控服务测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 系统监控服务测试失败: {e}")
        return False

def test_psutil_functions():
    """测试psutil基本功能"""
    print("\n测试psutil基本功能...")
    
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        print(f"CPU使用率: {cpu_percent}%")
        print(f"CPU核心数: {cpu_count}")
        
        # 内存信息
        memory = psutil.virtual_memory()
        print(f"总内存: {memory.total / (1024**3):.2f} GB")
        print(f"可用内存: {memory.available / (1024**3):.2f} GB")
        print(f"内存使用率: {memory.percent}%")
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        print(f"磁盘总容量: {disk.total / (1024**3):.2f} GB")
        print(f"磁盘使用率: {disk.used / disk.total * 100:.2f}%")
        
        # 网络信息
        network = psutil.net_io_counters()
        print(f"网络发送: {network.bytes_sent / (1024**2):.2f} MB")
        print(f"网络接收: {network.bytes_recv / (1024**2):.2f} MB")
        
        print("✓ psutil功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ psutil功能测试失败: {e}")
        return False

def test_process_monitoring():
    """测试进程监控"""
    print("\n测试进程监控...")
    
    try:
        from apps.monitoring.services import ProcessMonitorService
        
        service = ProcessMonitorService()
        
        # 收集Python进程指标
        metrics = service.collect_process_metrics(['python'])
        
        print(f"找到 {len(metrics)} 个Python进程")
        
        for metric in metrics[:3]:  # 只显示前3个
            print(f"进程: {metric['process_name']} (PID: {metric['pid']})")
            print(f"  CPU: {metric['cpu_percent']}%")
            print(f"  内存: {metric['memory_percent']}%")
        
        print("✓ 进程监控测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 进程监控测试失败: {e}")
        return False

if __name__ == '__main__':
    print("开始监控功能测试...\n")
    
    results = []
    results.append(test_psutil_functions())
    results.append(test_system_monitor_service())
    results.append(test_process_monitoring())
    
    print(f"\n测试结果: {sum(results)}/{len(results)} 通过")
    
    if all(results):
        print("✓ 所有测试通过！系统监控功能正常工作。")
        sys.exit(0)
    else:
        print("✗ 部分测试失败，请检查错误信息。")
        sys.exit(1)