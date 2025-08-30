import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class MarketDataConsumer(AsyncWebsocketConsumer):
    """市场数据WebSocket消费者"""
    
    async def connect(self):
        """连接处理"""
        # 验证用户认证
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return
        
        # 获取用户和租户信息
        self.user = self.scope["user"]
        self.tenant = self.user.tenant
        
        # 初始化订阅列表
        self.subscribed_symbols = set()
        
        await self.accept()
        
        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '市场数据连接已建立'
        }))
    
    async def disconnect(self, close_code):
        """断开连接处理"""
        # 离开所有订阅的组
        for symbol in self.subscribed_symbols:
            await self.channel_layer.group_discard(
                f"market_{symbol}",
                self.channel_name
            )
    
    async def receive(self, text_data):
        """接收消息处理"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'subscribe':
                await self.handle_subscribe(data)
            elif action == 'unsubscribe':
                await self.handle_unsubscribe(data)
            elif action == 'get_ticker':
                await self.