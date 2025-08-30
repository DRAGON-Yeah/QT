from django.db import models
from apps.core.models import TenantModel


class DatabaseConnection(TenantModel):
    """数据库连接配置"""
    
    CONNECTION_TYPES = [
        ('sqlite', 'SQLite'),
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL'),
    ]
    
    name = models.CharField('连接名称', max_length=100)
    connection_type = models.CharField('数据库类型', max_length=20, choices=CONNECTION_TYPES)
    host = models.CharField('主机地址', max_length=255, blank=True)
    port = models.IntegerField('端口', null=True, blank=True)
    database = models.CharField('数据库名', max_length=100)
    username = models.CharField('用户名', max_length=100, blank=True)
    password = models.CharField('密码', max_length=255, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    
    class Meta:
        verbose_name = '数据库连接'
        verbose_name_plural = '数据库连接'
        unique_together = ['tenant', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.connection_type})"


class QueryHistory(TenantModel):
    """SQL查询历史"""
    
    connection = models.ForeignKey(DatabaseConnection, on_delete=models.CASCADE, verbose_name='数据库连接')
    query = models.TextField('SQL查询')
    execution_time = models.FloatField('执行时间(秒)', null=True, blank=True)
    rows_affected = models.IntegerField('影响行数', null=True, blank=True)
    is_successful = models.BooleanField('是否成功', default=True)
    error_message = models.TextField('错误信息', blank=True)
    
    class Meta:
        verbose_name = 'SQL查询历史'
        verbose_name_plural = 'SQL查询历史'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.connection.name} - {self.query[:50]}..."


class RedisConnection(TenantModel):
    """Redis连接配置"""
    
    name = models.CharField('连接名称', max_length=100)
    host = models.CharField('主机地址', max_length=255, default='localhost')
    port = models.IntegerField('端口', default=6379)
    database = models.IntegerField('数据库编号', default=0)
    password = models.CharField('密码', max_length=255, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    
    class Meta:
        verbose_name = 'Redis连接'
        verbose_name_plural = 'Redis连接'
        unique_together = ['tenant', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port}/{self.database})"


class RedisCommandHistory(TenantModel):
    """Redis命令历史"""
    
    connection = models.ForeignKey(RedisConnection, on_delete=models.CASCADE, verbose_name='Redis连接')
    command = models.TextField('Redis命令')
    result = models.TextField('执行结果', blank=True)
    execution_time = models.FloatField('执行时间(秒)', null=True, blank=True)
    is_successful = models.BooleanField('是否成功', default=True)
    error_message = models.TextField('错误信息', blank=True)
    
    class Meta:
        verbose_name = 'Redis命令历史'
        verbose_name_plural = 'Redis命令历史'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.connection.name} - {self.command[:50]}..."