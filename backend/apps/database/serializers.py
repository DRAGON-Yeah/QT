from rest_framework import serializers
from .models import DatabaseConnection, QueryHistory, RedisConnection, RedisCommandHistory


class DatabaseConnectionSerializer(serializers.ModelSerializer):
    """数据库连接序列化器"""
    
    class Meta:
        model = DatabaseConnection
        fields = [
            'id', 'name', 'connection_type', 'host', 'port', 
            'database', 'username', 'password', 'is_active',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        validated_data['tenant'] = self.context['request'].user.tenant
        return super().create(validated_data)


class QueryHistorySerializer(serializers.ModelSerializer):
    """查询历史序列化器"""
    
    connection_name = serializers.CharField(source='connection.name', read_only=True)
    
    class Meta:
        model = QueryHistory
        fields = [
            'id', 'connection', 'connection_name', 'query', 
            'execution_time', 'rows_affected', 'is_successful', 
            'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RedisConnectionSerializer(serializers.ModelSerializer):
    """Redis连接序列化器"""
    
    class Meta:
        model = RedisConnection
        fields = [
            'id', 'name', 'host', 'port', 'database', 
            'password', 'is_active', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        validated_data['tenant'] = self.context['request'].user.tenant
        return super().create(validated_data)


class RedisCommandHistorySerializer(serializers.ModelSerializer):
    """Redis命令历史序列化器"""
    
    connection_name = serializers.CharField(source='connection.name', read_only=True)
    
    class Meta:
        model = RedisCommandHistory
        fields = [
            'id', 'connection', 'connection_name', 'command', 
            'result', 'execution_time', 'is_successful', 
            'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SQLQuerySerializer(serializers.Serializer):
    """SQL查询序列化器"""
    
    query = serializers.CharField(help_text='SQL查询语句')
    
    def validate_query(self, value):
        """验证SQL查询"""
        if not value.strip():
            raise serializers.ValidationError('查询语句不能为空')
        
        # 基本的SQL注入防护
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
        query_upper = value.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                # 只允许管理员执行危险操作
                request = self.context.get('request')
                if not (request and request.user.is_superuser):
                    raise serializers.ValidationError(f'不允许执行包含 {keyword} 的操作')
        
        return value


class RedisCommandSerializer(serializers.Serializer):
    """Redis命令序列化器"""
    
    command = serializers.CharField(help_text='Redis命令')
    
    def validate_command(self, value):
        """验证Redis命令"""
        if not value.strip():
            raise serializers.ValidationError('命令不能为空')
        
        # 基本的命令验证
        dangerous_commands = ['FLUSHDB', 'FLUSHALL', 'SHUTDOWN', 'CONFIG']
        command_upper = value.upper()
        
        for cmd in dangerous_commands:
            if command_upper.startswith(cmd):
                # 只允许管理员执行危险操作
                request = self.context.get('request')
                if not (request and request.user.is_superuser):
                    raise serializers.ValidationError(f'不允许执行 {cmd} 命令')
        
        return value


class TableExportSerializer(serializers.Serializer):
    """表导出序列化器"""
    
    table_name = serializers.CharField(help_text='表名')
    format_type = serializers.ChoiceField(
        choices=[('csv', 'CSV'), ('json', 'JSON')],
        default='csv',
        help_text='导出格式'
    )


class RedisKeySerializer(serializers.Serializer):
    """Redis键序列化器"""
    
    key = serializers.CharField(help_text='键名')
    value = serializers.JSONField(help_text='键值', required=False)
    key_type = serializers.ChoiceField(
        choices=[
            ('string', 'String'),
            ('hash', 'Hash'),
            ('list', 'List'),
            ('set', 'Set'),
            ('zset', 'Sorted Set')
        ],
        default='string',
        help_text='数据类型'
    )
    ttl = serializers.IntegerField(help_text='过期时间(秒)', required=False, allow_null=True)