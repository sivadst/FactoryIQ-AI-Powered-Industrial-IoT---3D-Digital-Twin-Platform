import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Dict, Set, Optional
from app.core.security import verify_token

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
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
            dead_connections = []
            for connection in self.active_connections[machine_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, machine_id)

manager = ConnectionManager()

@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    machine_id: str = Query('all')
):
    # Authenticate token if provided
    if token:
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await manager.connect(websocket, machine_id)
    try:
        while True:
            # Client heartbeat or client-sent command
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, machine_id)
    except Exception:
        manager.disconnect(websocket, machine_id)
