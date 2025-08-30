from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from apps.core.permissions import TenantPermission
from .models import DatabaseConnection, QueryHistory, RedisConnection, RedisCommandHistory
from .serializers import (
    DatabaseConnectionSerializer, QueryHistorySerializer,
    RedisConnectionSerializer, RedisCommandHistorySerializer,
    SQLQuerySerializer, RedisCommandSerializer, TableExportSerializer,
    RedisKeySerializer
)
from .services import DatabaseService, RedisService


class DatabaseConnectionViewSet(viewsets.ModelViewSet):
    """数据库连接管理视图集"""
    
    serializer_class = DatabaseConnectionSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        return DatabaseConnection.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试数据库连接"""
        connection = self.get_object()
        service = DatabaseService(connection)
        success, message = service.test_connection()
        
        return Response({
            'success': success,
            'message': message
        })
    
    @action(detail=True, methods=['post'])
    def execute_query(self, request, pk=None):
        """执行SQL查询"""
        connection = self.get_object()
        serializer = SQLQuerySerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            service = DatabaseService(connection)
            result = service.execute_query(serializer.validated_data['query'], request.user)
            return Response(result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """获取数据库表列表"""
        connection = self.get_object()
        service = DatabaseService(connection)
        tables = service.get_tables()
        
        return Response({
            'success': True,
            'tables': tables
        })
    
    @action(detail=True, methods=['get'])
    def table_structure(self, request, pk=None):
        """获取表结构"""
        connection = self.get_object()
        table_name = request.query_params.get('table_name')
        
        if not table_name:
            return Response(
                {'error': '请提供表名'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = DatabaseService(connection)
        structure = service.get_table_structure(table_name)
        
        return Response(structure)
    
    @action(detail=True, methods=['post'])
    def export_table(self, request, pk=None):
        """导出表数据"""
        connection = self.get_object()
        serializer = TableExportSerializer(data=request.data)
        
        if serializer.is_valid():
            service = DatabaseService(connection)
            data = service.export_table_data(
                serializer.validated_data['table_name'],
                serializer.validated_data['format_type']
            )
            
            # 创建HTTP响应
            content_type = 'text/csv' if serializer.validated_data['format_type'] == 'csv' else 'application/json'
            filename = f"{serializer.validated_data['table_name']}.{serializer.validated_data['format_type']}"
            
            response = HttpResponse(data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QueryHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """查询历史视图集"""
    
    serializer_class = QueryHistorySerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        queryset = QueryHistory.objects.filter(tenant=self.request.user.tenant)
        
        # 按连接过滤
        connection_id = self.request.query_params.get('connection_id')
        if connection_id:
            queryset = queryset.filter(connection_id=connection_id)
        
        # 按成功状态过滤
        is_successful = self.request.query_params.get('is_successful')
        if is_successful is not None:
            queryset = queryset.filter(is_successful=is_successful.lower() == 'true')
        
        return queryset.order_by('-created_at')


class RedisConnectionViewSet(viewsets.ModelViewSet):
    """Redis连接管理视图集"""
    
    serializer_class = RedisConnectionSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        return RedisConnection.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试Redis连接"""
        connection = self.get_object()
        service = RedisService(connection)
        success, message = service.test_connection()
        
        return Response({
            'success': success,
            'message': message
        })
    
    @action(detail=True, methods=['post'])
    def execute_command(self, request, pk=None):
        """执行Redis命令"""
        connection = self.get_object()
        serializer = RedisCommandSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            service = RedisService(connection)
            result = service.execute_command(serializer.validated_data['command'], request.user)
            return Response(result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def info(self, request, pk=None):
        """获取Redis信息"""
        connection = self.get_object()
        service = RedisService(connection)
        info = service.get_info()
        
        return Response(info)
    
    @action(detail=True, methods=['get'])
    def keys(self, request, pk=None):
        """获取Redis键列表"""
        connection = self.get_object()
        pattern = request.query_params.get('pattern', '*')
        limit = int(request.query_params.get('limit', 100))
        
        service = RedisService(connection)
        keys = service.get_keys(pattern, limit)
        
        return Response(keys)
    
    @action(detail=True, methods=['get', 'post', 'delete'])
    def key_value(self, request, pk=None):
        """Redis键值操作"""
        connection = self.get_object()
        service = RedisService(connection)
        
        if request.method == 'GET':
            # 获取键值
            key = request.query_params.get('key')
            if not key:
                return Response(
                    {'error': '请提供键名'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = service.get_key_value(key)
            return Response(result)
        
        elif request.method == 'POST':
            # 设置键值
            serializer = RedisKeySerializer(data=request.data)
            if serializer.is_valid():
                result = service.set_key_value(
                    serializer.validated_data['key'],
                    serializer.validated_data.get('value'),
                    serializer.validated_data['key_type']
                )
                
                # 设置TTL
                ttl = serializer.validated_data.get('ttl')
                if ttl and result['success']:
                    service.client.expire(serializer.validated_data['key'], ttl)
                
                return Response(result)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # 删除键
            key = request.data.get('key')
            if not key:
                return Response(
                    {'error': '请提供键名'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = service.delete_key(key)
            return Response(result)


class RedisCommandHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Redis命令历史视图集"""
    
    serializer_class = RedisCommandHistorySerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        queryset = RedisCommandHistory.objects.filter(tenant=self.request.user.tenant)
        
        # 按连接过滤
        connection_id = self.request.query_params.get('connection_id')
        if connection_id:
            queryset = queryset.filter(connection_id=connection_id)
        
        # 按成功状态过滤
        is_successful = self.request.query_params.get('is_successful')
        if is_successful is not None:
            queryset = queryset.filter(is_successful=is_successful.lower() == 'true')
        
        return queryset.order_by('-created_at')