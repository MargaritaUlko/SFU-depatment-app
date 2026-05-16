from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, chat_id: int, ws: WebSocket) -> None:
        self._connections[chat_id].append(ws)

    def disconnect(self, chat_id: int, ws: WebSocket) -> None:
        self._connections[chat_id].remove(ws)

    async def broadcast(self, chat_id: int, data: dict) -> None:
        for ws in list(self._connections[chat_id]):
            await ws.send_json(data)


manager = ConnectionManager()
