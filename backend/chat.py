from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        # room_id -> list of connection dicts {"ws": WebSocket, "user_id": int, "username": str}
        self.active_connections: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(self, room_id: str, websocket: WebSocket, user_id: int, username: str) -> None:
        await websocket.accept()
        self.active_connections.setdefault(room_id, []).append(
            {"ws": websocket, "user_id": user_id, "username": username}
        )

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(room_id)
        if not connections:
            return

        self.active_connections[room_id] = [
            c for c in connections if c.get("ws") is not websocket
        ]
        if not self.active_connections[room_id]:
            self.active_connections.pop(room_id, None)

    async def send_personal_message(self, message: Any, websocket: WebSocket) -> None:
        await websocket.send_json(message)

    async def broadcast(self, room_id: str, message: Any) -> None:
        connections = list(self.active_connections.get(room_id, []))
        for connection in connections:
            ws = connection.get("ws")
            try:
                await ws.send_json(message)
            except Exception:
                pass

    def get_room_users(self, room_id: str) -> List[Dict[str, Any]]:
        connections = self.active_connections.get(room_id, [])
        users: Dict[int, Dict[str, Any]] = {}
        for c in connections:
            user_id = c.get("user_id")
            username = c.get("username")
            if user_id and username:
                users[user_id] = {"id": user_id, "username": username}
        return list(users.values())


manager = ConnectionManager()
