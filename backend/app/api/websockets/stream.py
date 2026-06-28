import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # We can subscribe to specific machine IDs or 'all'
        self.active_connections['all'] = set()

    async def connect(self, websocket: WebSocket, machine_id: str = 'all'):
        await websocket.accept()
        if machine_id not in self.active_connections:
            self.active_connections[machine_id] = set()
        self.active_connections[machine_id].add(websocket)

    def disconnect(self, websocket: WebSocket, machine_id: str = 'all'):
        if machine_id in self.active_connections:
            self.active_connections[machine_id].discard(websocket)

    async def broadcast(self, message: dict, machine_id: str = 'all'):
        if machine_id in self.active_connections:
            for connection in self.active_connections[machine_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    pass

manager = ConnectionManager()

@router.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, 'all')
    try:
        while True:
            # Just keep the connection open, clients mostly receive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, 'all')
