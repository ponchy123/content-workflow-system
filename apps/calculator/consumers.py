from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TaskProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """建立WebSocket连接"""
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'task_{self.task_id}'

        # 加入任务组
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """断开WebSocket连接"""
        # 离开任务组
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def task_update(self, event):
        """处理任务更新消息"""
        # 发送消息到WebSocket
        await self.send(text_data=json.dumps(event['data'])) 