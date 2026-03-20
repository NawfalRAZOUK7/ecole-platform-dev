"""WebSocket connection manager with Redis Pub/Sub for multi-instance support.

Reference: Phase 3C — WebSocket Real-time Notifications
- ConnectionManager tracks active WebSocket connections per user
- Redis Pub/Sub channel: "ws:user:{user_id}" for cross-instance delivery
- Heartbeat: 30s ping interval
- Connection limit: 3 per user (oldest evicted)
- Graceful degradation: if Redis is down, local-only delivery
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from typing import Any

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings

logger = logging.getLogger(__name__)

# Max WebSocket connections per user
MAX_CONNECTIONS_PER_USER = 3

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 30


class ConnectionManager:
    """Manages WebSocket connections with Redis Pub/Sub for horizontal scaling.

    Each backend instance maintains its own set of local connections.
    Redis Pub/Sub ensures events reach users connected to any instance.
    """

    def __init__(self) -> None:
        # user_id → list of WebSocket connections (local to this instance)
        self._connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)
        # Redis pub/sub subscriber connection (separate from the main client)
        self._pubsub: redis.client.PubSub | None = None
        self._subscriber_task: asyncio.Task | None = None
        self._redis: redis.Redis | None = None
        self._running = False

    async def startup(self) -> None:
        """Initialize Redis Pub/Sub subscriber. Call on app startup."""
        try:
            # Create a separate Redis connection for pub/sub (cannot share with main client)
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            self._pubsub = self._redis.pubsub()
            self._running = True
            self._subscriber_task = asyncio.create_task(self._subscriber_loop())
            logger.info("WebSocket manager started with Redis Pub/Sub")
        except Exception:
            logger.warning("Redis Pub/Sub unavailable — WebSocket will use local-only delivery")
            self._running = False

    async def shutdown(self) -> None:
        """Tear down Redis Pub/Sub and close all connections. Call on app shutdown."""
        self._running = False

        # Cancel subscriber task
        if self._subscriber_task and not self._subscriber_task.done():
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass

        # Close all WebSocket connections
        for user_id, connections in list(self._connections.items()):
            for ws in connections:
                try:
                    await ws.close(code=1001, reason="Server shutting down")
                except Exception:
                    pass
        self._connections.clear()

        # Close pub/sub
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe()
                await self._pubsub.close()
            except Exception:
                pass

        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass

        logger.info("WebSocket manager shut down")

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """Accept a WebSocket connection and register it for a user.

        Enforces MAX_CONNECTIONS_PER_USER by evicting the oldest connection.
        Subscribes to the user's Redis Pub/Sub channel.
        """
        await websocket.accept()

        connections = self._connections[user_id]

        # Evict oldest connections if at limit
        while len(connections) >= MAX_CONNECTIONS_PER_USER:
            old_ws = connections.pop(0)
            try:
                await old_ws.close(code=1008, reason="Connection limit exceeded")
            except Exception:
                pass
            logger.info("Evicted oldest WS for user %s (limit %d)", user_id, MAX_CONNECTIONS_PER_USER)

        connections.append(websocket)

        # Subscribe to user's channel in Redis
        channel = f"ws:user:{user_id}"
        if self._pubsub and self._running:
            try:
                await self._pubsub.subscribe(channel)
            except Exception:
                logger.warning("Failed to subscribe to Redis channel %s", channel)

        logger.info("WS connected: user=%s (total=%d)", user_id, len(connections))

    async def disconnect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """Remove a WebSocket connection for a user."""
        connections = self._connections.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)

        # If no more connections for this user, unsubscribe from Redis channel
        if not connections:
            self._connections.pop(user_id, None)
            channel = f"ws:user:{user_id}"
            if self._pubsub and self._running:
                try:
                    await self._pubsub.unsubscribe(channel)
                except Exception:
                    pass

        logger.info("WS disconnected: user=%s (remaining=%d)", user_id, len(connections))

    async def send_to_user(self, user_id: uuid.UUID, event: dict[str, Any]) -> None:
        """Send an event to a specific user via Redis Pub/Sub.

        This publishes to Redis so all backend instances can deliver it.
        If Redis is unavailable, falls back to local-only delivery.
        """
        message = json.dumps(event)
        channel = f"ws:user:{user_id}"

        if self._redis and self._running:
            try:
                await self._redis.publish(channel, message)
                return
            except Exception:
                logger.warning("Redis publish failed, falling back to local delivery")

        # Fallback: local-only delivery
        await self._deliver_local(user_id, message)

    async def _deliver_local(self, user_id: uuid.UUID, message: str) -> None:
        """Deliver a message to all local WebSocket connections for a user."""
        connections = self._connections.get(user_id, [])
        dead: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            if ws in connections:
                connections.remove(ws)
        if not connections:
            self._connections.pop(user_id, None)

    async def _subscriber_loop(self) -> None:
        """Background task: read messages from Redis Pub/Sub and deliver locally."""
        while self._running:
            try:
                if self._pubsub is None:
                    await asyncio.sleep(1)
                    continue

                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    # Channel format: "ws:user:{user_id}"
                    channel: str = message["channel"]
                    if channel.startswith("ws:user:"):
                        user_id_str = channel[len("ws:user:"):]
                        try:
                            user_id = uuid.UUID(user_id_str)
                            await self._deliver_local(user_id, message["data"])
                        except ValueError:
                            logger.warning("Invalid user_id in channel: %s", channel)
                else:
                    # No message — small sleep to avoid busy-waiting
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in WS subscriber loop")
                await asyncio.sleep(1)

    def get_connected_user_count(self) -> int:
        """Return the number of users with active connections (local instance only)."""
        return len(self._connections)

    def get_connection_count(self, user_id: uuid.UUID) -> int:
        """Return the number of active connections for a specific user."""
        return len(self._connections.get(user_id, []))


# Singleton instance
ws_manager = ConnectionManager()
