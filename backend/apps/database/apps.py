from django.apps import AppConfig


class DatabaseConfig(AppConfig):
    """数据库管理应用配置"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.database'
    verbose_name = '数据库管理'