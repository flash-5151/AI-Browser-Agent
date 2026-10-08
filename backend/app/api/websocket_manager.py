import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("browser_agent.websocket")

class ConnectionManager:
    def __init__(self):
        # Maps task_id -> List[WebSocket]
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

    async def broadcast_to_task(self, task_id: str, message: Dict[str, Any]):
        if task_id in self.active_connections:
            dead_sockets = []
            for ws in self.active_connections[task_id]:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.disconnect(task_id, ws)

ws_manager = ConnectionManager()
