"""
测试环境设置
"""
from .base import *

# 调试模式
DEBUG = True

# 数据库配置 - 测试环境使用内存数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 缓存配置 - 测试环境使用虚拟缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# 邮件后端 - 测试环境
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Celery配置 - 测试环境同步执行
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# 密码验证 - 测试环境简化
AUTH_PASSWORD_VALIDATORS = []

# 日志配置 - 测试环境
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# 静态文件配置
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# 安全设置 - 测试环境
SECRET_KEY = 'test-secret-key-not-for-production'
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# 禁用迁移以加速测试
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()