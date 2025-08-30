#!/usr/bin/env python3
"""
Celery监控功能测试脚本
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
        # Celery配置
        CELERY_BROKER_URL='redis://localhost:6379/0',
        CELERY_RESULT_BACKEND='redis://localhost:6379/0',
        CELERY_TASK_ALWAYS_EAGER=True,  # 同步执行任务用于测试
    )

django.setup()

def test_celery_monitor_service():
    """测试Celery监控服务"""
    print("测试Celery监控服务...")
    
    try:
        from apps.monitoring.celery_services import CeleryMonitorService
        
        service = CeleryMonitorService()
        
        # 测试获取Worker统计
        print("获取Worker统计信息...")
        workers = service.get_worker_stats()
        print(f"找到 {len(workers)} 个Worker")
        
        for worker in workers:
            print(f"Worker: {worker['worker_name']}")
            print(f"  状态: {worker['status']}")
            print(f"  活跃任务: {worker['active_tasks']}")
            print(f"  已处理任务: {worker['processed_tasks']}")
        
        # 测试获取任务统计
        print("\n获取任务统计信息...")
        tasks = service.get_task_stats()
        print(f"找到 {len(tasks)} 个任务")
        
        for task in tasks[:3]:  # 只显示前3个
            print(f"任务: {task['task_name']}")
            print(f"  状态: {task['state']}")
            print(f"  Worker: {task['worker_name']}")
        
        # 测试获取队列统计
        print("\n获取队列统计信息...")
        queues = service.get_queue_stats()
        print(f"找到 {len(queues)} 个队列")
        
        for queue in queues:
            print(f"队列: {queue['queue_name']}")
            print(f"  等待任务: {queue['pending_tasks']}")
            print(f"  活跃任务: {queue['active_tasks']}")
        
        print("✓ Celery监控服务测试通过")
        return True
        
    except Exception as e:
        print(f"✗ Celery监控服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_celery_basic_functions():
    """测试Celery基本功能"""
    print("\n测试Celery基本功能...")
    
    try:
        from celery import current_app
        
        # 测试Celery应用配置
        print(f"Celery应用名称: {current_app.main}")
        print(f"Broker URL: {current_app.conf.broker_url}")
        print(f"Result Backend: {current_app.conf.result_backend}")
        
        # 测试控制接口
        control = current_app.control
        inspect = control.inspect()
        
        # 尝试获取统计信息（可能为空，因为没有运行的worker）
        try:
            stats = inspect.stats()
            print(f"Worker统计: {stats}")
        except Exception as e:
            print(f"获取Worker统计失败（正常，因为没有运行的worker）: {e}")
        
        print("✓ Celery基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ Celery基本功能测试失败: {e}")
        return False

def test_celery_task_creation():
    """测试Celery任务创建"""
    print("\n测试Celery任务创建...")
    
    try:
        from celery import shared_task
        
        # 定义一个测试任务
        @shared_task
        def test_task(x, y):
            return x + y
        
        # 测试任务注册
        print(f"任务名称: {test_task.name}")
        
        # 在测试模式下同步执行任务
        result = test_task.apply(args=[2, 3])
        print(f"任务结果: {result.result}")
        print(f"任务状态: {result.status}")
        
        assert result.result == 5
        assert result.status == 'SUCCESS'
        
        print("✓ Celery任务创建测试通过")
        return True
        
    except Exception as e:
        print(f"✗ Celery任务创建测试失败: {e}")
        return False

def test_celery_models():
    """测试Celery模型"""
    print("\n测试Celery模型...")
    
    try:
        from apps.monitoring.models import CeleryWorker, CeleryTask, CeleryQueue
        from apps.users.models import Tenant
        
        # 创建测试租户
        tenant = Tenant.objects.create(name='Test Tenant')
        
        # 测试CeleryWorker模型
        worker = CeleryWorker.objects.create(
            tenant=tenant,
            worker_name='test-worker',
            hostname='localhost',
            status='online',
            active_tasks=5,
            processed_tasks=100
        )
        print(f"创建Worker: {worker.worker_name}")
        
        # 测试CeleryTask模型
        task = CeleryTask.objects.create(
            tenant=tenant,
            task_id='test-task-123',
            task_name='test_task',
            state='SUCCESS',
            worker_name='test-worker'
        )
        print(f"创建任务: {task.task_name}")
        
        # 测试CeleryQueue模型
        queue = CeleryQueue.objects.create(
            tenant=tenant,
            queue_name='celery',
            pending_tasks=10,
            active_tasks=5
        )
        print(f"创建队列: {queue.queue_name}")
        
        print("✓ Celery模型测试通过")
        return True
        
    except Exception as e:
        print(f"✗ Celery模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始Celery监控功能测试...\n")
    
    results = []
    results.append(test_celery_basic_functions())
    results.append(test_celery_task_creation())
    results.append(test_celery_models())
    results.append(test_celery_monitor_service())
    
    print(f"\n测试结果: {sum(results)}/{len(results)} 通过")
    
    if all(results):
        print("✓ 所有测试通过！Celery监控功能正常工作。")
        sys.exit(0)
    else:
        print("✗ 部分测试失败，请检查错误信息。")
        sys.exit(1)