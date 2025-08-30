"""
核心任务模块
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(subject, message, recipient_list):
    """
    发送邮件任务
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"邮件发送成功: {subject} -> {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


@shared_task
def cleanup_old_data():
    """
    清理旧数据任务
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # 清理30天前的日志
    cutoff_date = timezone.now() - timedelta(days=30)
    
    # 这里可以添加具体的清理逻辑
    logger.info(f"开始清理 {cutoff_date} 之前的数据")
    
    # 示例：清理旧的会话数据
    from django.contrib.sessions.models import Session
    expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
    count = expired_sessions.count()
    expired_sessions.delete()
    
    logger.info(f"清理完成，删除了 {count} 个过期会话")
    return count


@shared_task
def system_health_check():
    """
    系统健康检查任务
    """
    from django.db import connection
    from django.core.cache import cache
    import redis
    
    health_status = {
        'timestamp': timezone.now().isoformat(),
        'database': False,
        'cache': False,
        'redis': False,
    }
    
    # 检查数据库
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['database'] = True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
    
    # 检查缓存
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['cache'] = True
    except Exception as e:
        logger.error(f"缓存健康检查失败: {e}")
    
    # 检查Redis
    try:
        redis_client = redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
        health_status['redis'] = True
    except Exception as e:
        logger.error(f"Redis健康检查失败: {e}")
    
    logger.info(f"系统健康检查完成: {health_status}")
    return health_status