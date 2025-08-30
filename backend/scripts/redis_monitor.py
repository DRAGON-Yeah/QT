#!/usr/bin/env python
"""
Redis监控脚本
"""
import redis
import json
import time
from datetime import datetime


class RedisMonitor:
    def __init__(self, redis_url='redis://localhost:6379/0'):
        self.redis_client = redis.from_url(redis_url)
    
    def get_info(self):
        """获取Redis信息"""
        try:
            info = self.redis_client.info()
            return {
                'status': 'connected',
                'version': info.get('redis_version'),
                'memory_used': info.get('used_memory_human'),
                'memory_peak': info.get('used_memory_peak_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'uptime_in_seconds': info.get('uptime_in_seconds'),
            }
        except redis.ConnectionError:
            return {'status': 'disconnected'}
    
    def get_key_count(self, pattern='*'):
        """获取键数量"""
        try:
            keys = self.redis_client.keys(pattern)
            return len(keys)
        except redis.ConnectionError:
            return 0
    
    def test_connection(self):
        """测试连接"""
        try:
            self.redis_client.ping()
            return True
        except redis.ConnectionError:
            return False
    
    def clear_cache(self, pattern='*'):
        """清理缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                return len(keys)
            return 0
        except redis.ConnectionError:
            return 0


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python redis_monitor.py [info|test|clear|count]")
        return
    
    command = sys.argv[1]
    monitor = RedisMonitor()
    
    if command == 'info':
        info = monitor.get_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    elif command == 'test':
        if monitor.test_connection():
            print("Redis连接正常")
        else:
            print("Redis连接失败")
    
    elif command == 'clear':
        pattern = sys.argv[2] if len(sys.argv) > 2 else '*'
        count = monitor.clear_cache(pattern)
        print(f"清理了 {count} 个键")
    
    elif command == 'count':
        pattern = sys.argv[2] if len(sys.argv) > 2 else '*'
        count = monitor.get_key_count(pattern)
        print(f"匹配模式 '{pattern}' 的键数量: {count}")
    
    else:
        print("未知命令")


if __name__ == '__main__':
    main()