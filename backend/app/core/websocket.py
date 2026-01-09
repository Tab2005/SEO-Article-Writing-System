"""
WebSocket Manager.

Handles real-time progress updates via WebSocket connections.
"""

import json
from typing import Dict, Set
from fastapi import WebSocket

from app.config import settings


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Task subscribers: task_id -> set of user_ids
        self.task_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    def subscribe_to_task(self, task_id: str, user_id: str) -> None:
        """Subscribe user to task updates."""
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()
        self.task_subscribers[task_id].add(user_id)
    
    def unsubscribe_from_task(self, task_id: str, user_id: str) -> None:
        """Unsubscribe user from task updates."""
        if task_id in self.task_subscribers:
            self.task_subscribers[task_id].discard(user_id)
            if not self.task_subscribers[task_id]:
                del self.task_subscribers[task_id]
    
    async def send_personal_message(self, message: dict, user_id: str) -> None:
        """Send message to specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # Connection may have closed
    
    async def broadcast_task_update(self, task_id: str, update: dict) -> None:
        """Broadcast task update to all subscribers."""
        if task_id not in self.task_subscribers:
            return
        
        message = {
            "type": "task_update",
            "task_id": task_id,
            "data": update,
        }
        
        for user_id in self.task_subscribers[task_id]:
            await self.send_personal_message(message, user_id)
    
    async def send_progress(
        self,
        task_id: str,
        progress: int,
        status: str,
        message: str = "",
    ) -> None:
        """Send progress update for a task."""
        update = {
            "progress": progress,
            "status": status,
            "message": message,
        }
        await self.broadcast_task_update(task_id, update)
    
    async def send_completion(self, task_id: str, result: dict) -> None:
        """Send task completion notification."""
        update = {
            "progress": 100,
            "status": "completed",
            "message": "Task completed",
            "result": result,
        }
        await self.broadcast_task_update(task_id, update)
        
        # Clean up subscribers
        if task_id in self.task_subscribers:
            del self.task_subscribers[task_id]
    
    async def send_error(self, task_id: str, error: str) -> None:
        """Send task error notification."""
        update = {
            "progress": 0,
            "status": "failed",
            "message": error,
            "error": error,
        }
        await self.broadcast_task_update(task_id, update)
        
        # Clean up subscribers
        if task_id in self.task_subscribers:
            del self.task_subscribers[task_id]


# Singleton instance
ws_manager = ConnectionManager()
