import asyncio
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
        await websocket.close()

    async def send_to_user(self, user_id: int, message: dict) -> None:
        async with self._lock:
            connections = list(self.active_connections.get(user_id, []))
        dead = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning("WS连接管理异常", exc_info=True)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self.active_connections.get(user_id, []):
                        self.active_connections[user_id].remove(ws)
                if user_id in self.active_connections and not self.active_connections[user_id]:
                    del self.active_connections[user_id]

    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            all_connections = [ws for conns in self.active_connections.values() for ws in conns]
        dead = []
        for ws in all_connections:
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning("WS连接清理异常", exc_info=True)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    for conns in self.active_connections.values():
                        if ws in conns:
                            conns.remove(ws)
                self.active_connections = {uid: conns for uid, conns in self.active_connections.items() if conns}


connection_manager = ConnectionManager()
