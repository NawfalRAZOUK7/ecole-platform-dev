"""WebSocket endpoint for real-time notifications.

Reference: Phase 3C — WebSocket Real-time Notifications
- GET /ws?token={access_token} — upgrade to WebSocket with JWT auth
- Heartbeat ping every 30s, client must respond with pong
- Max 3 connections per user (oldest evicted)
- Events delivered as JSON: { "event": "...", "data": { ... } }
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import async_session
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.core.ws_manager import HEARTBEAT_INTERVAL, ws_manager
from app.models.iam import Session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def _authenticate_ws(token: str) -> dict:
    """Validate the JWT token for WebSocket connection.

    Returns the decoded payload or raises AuthenticationError.
    Also verifies the session is not revoked.
    """
    payload = decode_access_token(token)

    # Verify session is still active
    session_id = uuid.UUID(payload["session_id"])
    async with async_session() as db:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.revoke_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise AuthenticationError("Session revoked", error_code="ERR-IAM-401")

    return payload


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time event delivery.

    Connection flow:
    1. Client connects: GET /api/v1/ws?token={access_token}
    2. Server validates JWT and checks session
    3. If valid, accepts connection and registers with ConnectionManager
    4. Server sends heartbeat pings every 30s
    5. Events are pushed as JSON messages
    6. Client can send "pong" in response to pings

    Event format: {"event": "<type>", "data": { ... }}
    Heartbeat format: {"event": "ping"}
    """
    # 1. Authenticate
    try:
        payload = await _authenticate_ws(token)
    except (AuthenticationError, Exception) as exc:
        logger.warning("WS auth failed: %s", exc)
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_id = uuid.UUID(payload["sub"])
    school_id = uuid.UUID(payload["school_id"])
    role = payload["role"]

    # 2. Connect
    await ws_manager.connect(websocket, user_id)

    # Send welcome message
    try:
        await websocket.send_text(json.dumps({
            "event": "connected",
            "data": {
                "user_id": str(user_id),
                "school_id": str(school_id),
                "role": role,
                "message": "WebSocket connected",
            },
        }))
    except Exception:
        await ws_manager.disconnect(websocket, user_id)
        return

    # 3. Heartbeat + receive loop
    try:
        while True:
            try:
                # Wait for client message with heartbeat timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HEARTBEAT_INTERVAL,
                )
                # Handle client messages (pong, etc.)
                try:
                    msg = json.loads(data)
                    if msg.get("event") == "pong":
                        continue  # Expected heartbeat response
                except (json.JSONDecodeError, AttributeError):
                    pass

            except asyncio.TimeoutError:
                # No message received within heartbeat interval — send ping
                try:
                    await websocket.send_text(json.dumps({"event": "ping"}))
                except Exception:
                    break  # Connection dead

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS error for user %s", user_id)
    finally:
        await ws_manager.disconnect(websocket, user_id)
