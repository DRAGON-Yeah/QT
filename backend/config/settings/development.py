"""
开发环境设置
"""
from .base import *

# 调试模式
DEBUG = True

# 允许的主机
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# 开发环境应用
INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]

# 开发环境中间件
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# 数据库配置 - 开发环境使用SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 如果设置了DATABASE_URL，则使用PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL)

# Debug工具栏配置
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# 开发环境CORS设置
CORS_ALLOW_ALL_ORIGINS = True

# 邮件后端 - 开发环境使用控制台
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 日志配置 - 开发环境
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

# Celery配置 - 开发环境
CELERY_TASK_ALWAYS_EAGER = False  # 设为True可以同步执行任务用于调试
CELERY_TASK_EAGER_PROPAGATES = True

# 缓存配置 - 开发环境可以使用内存缓存
if not os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# 静态文件配置
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# 安全设置 - 开发环境放宽
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# 会话设置 - 开发环境
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False