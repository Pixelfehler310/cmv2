from typing import Dict, List, Optional
from fastapi import WebSocket
from uuid import UUID

class Connection:
    def __init__(self, websocket: WebSocket, user_id: str, role: str):
        self.websocket = websocket
        self.user_id = user_id
        self.role = role

class SessionManager:
    def __init__(self):
        # campaign_id -> list of Connections
        self.active_connections: Dict[str, List[Connection]] = {}

    async def connect(self, websocket: WebSocket, campaign_id: str, user_id: str, role: str):
        await websocket.accept()
        if campaign_id not in self.active_connections:
            self.active_connections[campaign_id] = []
        
        connection = Connection(websocket, user_id, role)
        self.active_connections[campaign_id].append(connection)
        return connection

    def disconnect(self, campaign_id: str, connection: Connection):
        if campaign_id in self.active_connections:
            if connection in self.active_connections[campaign_id]:
                self.active_connections[campaign_id].remove(connection)
            if not self.active_connections[campaign_id]:
                del self.active_connections[campaign_id]

    async def broadcast(self, campaign_id: str, message: dict, exclude_user: Optional[str] = None):
        if campaign_id in self.active_connections:
            for connection in self.active_connections[campaign_id]:
                if exclude_user and connection.user_id == exclude_user:
                    continue
                try:
                    await connection.websocket.send_json(message)
                except Exception:
                    # Handle disconnection?
                    pass

session_manager = SessionManager()
