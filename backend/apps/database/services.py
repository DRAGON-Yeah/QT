import sqlite3
import time
import json
import redis
from typing import Dict, List, Any, Tuple, Optional
from django.db import connections, connection
from django.conf import settings
from contextlib import contextmanager
import pymysql
import psycopg2
from psycopg2.extras import RealDictCursor
from .models import DatabaseConnection, QueryHistory, RedisConnection, RedisCommandHistory


class DatabaseService:
    """数据库管理服务"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            if self.db_connection.connection_type == 'sqlite':
                conn = sqlite3.connect(self.db_connection.database)
                conn.row_factory = sqlite3.Row
            elif self.db_connection.connection_type == 'mysql':
                conn = pymysql.connect(
                    host=self.db_connection.host,
                    port=self.db_connection.port or 3306,
                    user=self.db_connection.username,
                    password=self.db_connection.password,
                    database=self.db_connection.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
            elif self.db_connection.connection_type == 'postgresql':
                conn = psycopg2.connect(
                    host=self.db_connection.host,
                    port=self.db_connection.port or 5432,
                    user=self.db_connection.username,
                    password=self.db_connection.password,
                    database=self.db_connection.database,
                    cursor_factory=RealDictCursor
                )
            
            yield conn
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> Tuple[bool, str]:
        """测试数据库连接"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True, "连接成功"
        except Exception as e:
            return False, str(e)
    
    def execute_query(self, query: str, user) -> Dict[str, Any]:
        """执行SQL查询"""
        start_time = time.time()
        result = {
            'success': False,
            'data': [],
            'columns': [],
            'rows_affected': 0,
            'execution_time': 0,
            'error': None
        }
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                # 如果是SELECT查询，获取结果
                if query.strip().upper().startswith('SELECT'):
                    if self.db_connection.connection_type == 'sqlite':
                        result['columns'] = [desc[0] for desc in cursor.description]
                        result['data'] = [dict(row) for row in cursor.fetchall()]
                    else:
                        result['columns'] = [desc[0] for desc in cursor.description]
                        result['data'] = cursor.fetchall()
                    result['rows_affected'] = len(result['data'])
                else:
                    # 对于INSERT, UPDATE, DELETE等操作
                    conn.commit()
                    result['rows_affected'] = cursor.rowcount
                
                result['success'] = True
                
        except Exception as e:
            result['error'] = str(e)
        
        result['execution_time'] = time.time() - start_time
        
        # 记录查询历史
        QueryHistory.objects.create(
            tenant=user.tenant,
            connection=self.db_connection,
            query=query,
            execution_time=result['execution_time'],
            rows_affected=result['rows_affected'],
            is_successful=result['success'],
            error_message=result['error'] or ''
        )
        
        return result
    
    def get_tables(self) -> List[Dict[str, Any]]:
        """获取数据库表列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_connection.connection_type == 'sqlite':
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [{'name': row[0]} for row in cursor.fetchall()]
                elif self.db_connection.connection_type == 'mysql':
                    cursor.execute("SHOW TABLES")
                    tables = [{'name': list(row.values())[0]} for row in cursor.fetchall()]
                elif self.db_connection.connection_type == 'postgresql':
                    cursor.execute("""
                        SELECT tablename as name 
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                    """)
                    tables = [dict(row) for row in cursor.fetchall()]
                
                return tables
        except Exception as e:
            return []
    
    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_connection.connection_type == 'sqlite':
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            'name': row[1],
                            'type': row[2],
                            'nullable': not row[3],
                            'default': row[4],
                            'primary_key': bool(row[5])
                        })
                elif self.db_connection.connection_type == 'mysql':
                    cursor.execute(f"DESCRIBE {table_name}")
                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            'name': row['Field'],
                            'type': row['Type'],
                            'nullable': row['Null'] == 'YES',
                            'default': row['Default'],
                            'primary_key': row['Key'] == 'PRI'
                        })
                elif self.db_connection.connection_type == 'postgresql':
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = %s
                    """, (table_name,))
                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            'name': row['column_name'],
                            'type': row['data_type'],
                            'nullable': row['is_nullable'] == 'YES',
                            'default': row['column_default'],
                            'primary_key': False  # 需要额外查询
                        })
                
                return {
                    'table_name': table_name,
                    'columns': columns
                }
        except Exception as e:
            return {'error': str(e)}
    
    def export_table_data(self, table_name: str, format_type: str = 'csv') -> str:
        """导出表数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                
                if format_type == 'csv':
                    import csv
                    import io
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # 写入列名
                    columns = [desc[0] for desc in cursor.description]
                    writer.writerow(columns)
                    
                    # 写入数据
                    for row in cursor.fetchall():
                        if isinstance(row, dict):
                            writer.writerow(row.values())
                        else:
                            writer.writerow(row)
                    
                    return output.getvalue()
                
                elif format_type == 'json':
                    columns = [desc[0] for desc in cursor.description]
                    data = []
                    for row in cursor.fetchall():
                        if isinstance(row, dict):
                            data.append(row)
                        else:
                            data.append(dict(zip(columns, row)))
                    
                    return json.dumps(data, indent=2, ensure_ascii=False)
                
        except Exception as e:
            return f"导出失败: {str(e)}"


class RedisService:
    """Redis管理服务"""
    
    def __init__(self, redis_connection: RedisConnection):
        self.redis_connection = redis_connection
        self._client = None
    
    @property
    def client(self):
        """获取Redis客户端"""
        if not self._client:
            self._client = redis.Redis(
                host=self.redis_connection.host,
                port=self.redis_connection.port,
                db=self.redis_connection.database,
                password=self.redis_connection.password or None,
                decode_responses=True
            )
        return self._client
    
    def test_connection(self) -> Tuple[bool, str]:
        """测试Redis连接"""
        try:
            self.client.ping()
            return True, "连接成功"
        except Exception as e:
            return False, str(e)
    
    def execute_command(self, command: str, user) -> Dict[str, Any]:
        """执行Redis命令"""
        start_time = time.time()
        result = {
            'success': False,
            'result': None,
            'execution_time': 0,
            'error': None
        }
        
        try:
            # 解析命令
            parts = command.strip().split()
            if not parts:
                raise ValueError("命令不能为空")
            
            cmd = parts[0].upper()
            args = parts[1:]
            
            # 执行命令
            if hasattr(self.client, cmd.lower()):
                method = getattr(self.client, cmd.lower())
                result['result'] = method(*args)
            else:
                result['result'] = self.client.execute_command(cmd, *args)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        result['execution_time'] = time.time() - start_time
        
        # 记录命令历史
        RedisCommandHistory.objects.create(
            tenant=user.tenant,
            connection=self.redis_connection,
            command=command,
            result=str(result['result']) if result['result'] is not None else '',
            execution_time=result['execution_time'],
            is_successful=result['success'],
            error_message=result['error'] or ''
        )
        
        return result
    
    def get_info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        try:
            info = self.client.info()
            return {
                'success': True,
                'info': info
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_keys(self, pattern: str = '*', limit: int = 100) -> Dict[str, Any]:
        """获取键列表"""
        try:
            keys = []
            for key in self.client.scan_iter(match=pattern, count=limit):
                key_type = self.client.type(key)
                ttl = self.client.ttl(key)
                keys.append({
                    'key': key,
                    'type': key_type,
                    'ttl': ttl if ttl > 0 else None
                })
                if len(keys) >= limit:
                    break
            
            return {
                'success': True,
                'keys': keys
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_key_value(self, key: str) -> Dict[str, Any]:
        """获取键值"""
        try:
            if not self.client.exists(key):
                return {
                    'success': False,
                    'error': '键不存在'
                }
            
            key_type = self.client.type(key)
            ttl = self.client.ttl(key)
            
            if key_type == 'string':
                value = self.client.get(key)
            elif key_type == 'hash':
                value = self.client.hgetall(key)
            elif key_type == 'list':
                value = self.client.lrange(key, 0, -1)
            elif key_type == 'set':
                value = list(self.client.smembers(key))
            elif key_type == 'zset':
                value = self.client.zrange(key, 0, -1, withscores=True)
            else:
                value = f"不支持的数据类型: {key_type}"
            
            return {
                'success': True,
                'key': key,
                'type': key_type,
                'value': value,
                'ttl': ttl if ttl > 0 else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_key_value(self, key: str, value: Any, key_type: str = 'string') -> Dict[str, Any]:
        """设置键值"""
        try:
            if key_type == 'string':
                self.client.set(key, value)
            elif key_type == 'hash':
                if isinstance(value, dict):
                    self.client.hset(key, mapping=value)
                else:
                    raise ValueError("哈希类型需要字典值")
            elif key_type == 'list':
                if isinstance(value, list):
                    self.client.delete(key)
                    if value:
                        self.client.lpush(key, *reversed(value))
                else:
                    raise ValueError("列表类型需要列表值")
            elif key_type == 'set':
                if isinstance(value, (list, set)):
                    self.client.delete(key)
                    if value:
                        self.client.sadd(key, *value)
                else:
                    raise ValueError("集合类型需要列表或集合值")
            else:
                raise ValueError(f"不支持的数据类型: {key_type}")
            
            return {
                'success': True,
                'message': '设置成功'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_key(self, key: str) -> Dict[str, Any]:
        """删除键"""
        try:
            result = self.client.delete(key)
            return {
                'success': True,
                'deleted': result > 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }