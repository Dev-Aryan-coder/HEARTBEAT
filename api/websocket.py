from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import logging
import asyncio

logger = logging.getLogger("HEARTBEAT_WS")

class HeartbeatMonitor:
    """Manages constant live feed connections."""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass  # Already removed
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_cell_event(self, user_id: str, message: dict):
        """Sends live cell status to all of the user's open monitors.
        ISSUE 13 FIX: Each send is wrapped in try/except to handle dead connections."""
        if user_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.debug(f"Dead WebSocket connection for {user_id}: {str(e)}")
                    dead_connections.append(connection)
            # Clean up dead connections
            for dead in dead_connections:
                self.disconnect(dead, user_id)

monitor = HeartbeatMonitor()

async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Real-time WS Handler.
    ISSUE 13 FIX: Broad exception handling + ping/pong keepalive."""
    await monitor.connect(websocket, user_id)
    try:
        while True:
            try:
                # ISSUE 13 FIX: Add timeout to detect dead connections
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )
                # Echo pong for keepalive
                if data.strip().lower() == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to check if client is still alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.warning(f"WebSocket error for user {user_id}: {str(e)}")
    finally:
        monitor.disconnect(websocket, user_id)
        logger.info(f"WebSocket cleaned up for user: {user_id}")
