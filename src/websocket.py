from typing import Any
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self._connects: dict[str, list[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket):
        await ws.accept()
        self._connects.setdefault(room, []).append(ws)

    def disconnect(self, room: str, ws: WebSocket):
        conns = self._connects.get(room)
        if conns and ws in conns:
            conns.remove(ws)

    async def broadcast(self, room: str, message: list[str, Any]) -> None:
        for ws in self._connects.get(room, []):
            await ws.send_json(message)


# global instance of WebSocketManager
manager = WebSocketManager()
