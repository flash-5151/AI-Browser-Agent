import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # task_id -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info(f"WebSocket connected for task {task_id}")

    def disconnect(self, task_id: str, websocket: WebSocket):
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")

    async def broadcast(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message over WS: {e}")
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(task_id, conn)

ws_manager = ConnectionManager()
