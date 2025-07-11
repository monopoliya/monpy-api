from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.connects: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.connects[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.connects:
            del self.connects[user_id]

    async def send_to(self, user_id: str, payload: dict):
        if user_id in self.connects:
            websocket = self.connects[user_id]
            await websocket.send_json(payload)


# global instance of WebSocketManager
manager = WebSocketManager()
