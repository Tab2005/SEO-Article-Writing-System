"""
WebSocket API Endpoints.

Handles real-time WebSocket connections for task progress.
"""

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.websocket import ws_manager
from app.core.security import decode_token

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None),
):
    """
    WebSocket endpoint for real-time updates.
    
    Connect with: ws://host/api/v1/ws?token=<jwt_token>
    
    Message format (send):
    - Subscribe: {"action": "subscribe", "task_id": "xxx"}
    - Unsubscribe: {"action": "unsubscribe", "task_id": "xxx"}
    
    Message format (receive):
    - Progress: {"type": "task_update", "task_id": "xxx", "data": {...}}
    """
    # Verify token
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return
    
    # Accept connection
    await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive messages
            data = await websocket.receive_json()
            action = data.get("action")
            task_id = data.get("task_id")
            
            if action == "subscribe" and task_id:
                ws_manager.subscribe_to_task(task_id, user_id)
                await websocket.send_json({
                    "type": "subscribed",
                    "task_id": task_id,
                })
            
            elif action == "unsubscribe" and task_id:
                ws_manager.unsubscribe_from_task(task_id, user_id)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "task_id": task_id,
                })
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception:
        ws_manager.disconnect(websocket, user_id)
