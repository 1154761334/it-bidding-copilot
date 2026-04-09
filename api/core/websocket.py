from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        # Maps project/channel IDs to list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel_id: str):
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)

    def disconnect(self, websocket: WebSocket, channel_id: str):
        if channel_id in self.active_connections:
            self.active_connections[channel_id].remove(websocket)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]

    async def broadcast(self, message: dict, channel_id: str):
        if channel_id in self.active_connections:
            # We use asyncio.gather to broadcast to all clients concurrently
            json_msg = json.dumps(message)
            tasks = [connection.send_text(json_msg) for connection in self.active_connections[channel_id]]
            await asyncio.gather(*tasks, return_exceptions=True)

manager = ConnectionManager()
