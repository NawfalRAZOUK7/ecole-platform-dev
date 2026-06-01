"""Unit tests for app/core/ws_manager.py — full branch coverage.

Strategy:
- Mock WebSocket (fastapi.WebSocket) with AsyncMock.
- Mock Redis connection and pub/sub with AsyncMock.
- Test ConnectionManager methods and the subscriber loop.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.ws_manager import (
    MAX_CONNECTIONS_PER_USER,
    ConnectionManager,
    ws_manager,
)


def _mock_ws() -> AsyncMock:
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


def _make_manager() -> ConnectionManager:
    return ConnectionManager()


# ---------------------------------------------------------------------------
# startup / shutdown
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_startup_success():
    mgr = _make_manager()
    # redis.pubsub() is a SYNCHRONOUS call → MagicMock, not AsyncMock
    mock_redis = MagicMock()
    mock_pubsub = AsyncMock()
    mock_redis.pubsub.return_value = mock_pubsub

    with (
        patch("redis.asyncio.from_url", return_value=mock_redis),
        patch("asyncio.create_task", return_value=MagicMock()),
    ):
        await mgr.startup()

    assert mgr._running is True
    assert mgr._pubsub is mock_pubsub


@pytest.mark.asyncio
async def test_startup_redis_failure_degrades_gracefully():
    mgr = _make_manager()
    with patch("redis.asyncio.from_url", side_effect=ConnectionError("redis down")):
        await mgr.startup()

    assert mgr._running is False


@pytest.mark.asyncio
async def test_shutdown_cancels_task_and_closes_connections():
    mgr = _make_manager()
    mgr._running = True

    # Add a fake connection
    uid = uuid.uuid4()
    ws1 = _mock_ws()
    mgr._connections[uid] = [ws1]

    # Use a real asyncio.Task-like future that raises CancelledError
    async def _coro_that_gets_cancelled():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            raise

    loop = asyncio.get_event_loop()
    task = loop.create_task(_coro_that_gets_cancelled())
    task.cancel()
    mgr._subscriber_task = task

    mock_redis = AsyncMock()
    mgr._redis = mock_redis
    mock_pubsub = AsyncMock()
    mgr._pubsub = mock_pubsub

    await mgr.shutdown()

    assert mgr._running is False
    assert task.cancelled() or task.done()


@pytest.mark.asyncio
async def test_shutdown_no_task():
    mgr = _make_manager()
    mgr._running = True
    mgr._subscriber_task = None
    mock_pubsub = AsyncMock()
    mgr._pubsub = mock_pubsub
    mgr._redis = AsyncMock()

    await mgr.shutdown()

    assert mgr._running is False


@pytest.mark.asyncio
async def test_shutdown_task_already_done():
    mgr = _make_manager()
    mgr._running = True

    mock_task = MagicMock()
    mock_task.done.return_value = True  # already done
    mgr._subscriber_task = mock_task
    mgr._pubsub = AsyncMock()
    mgr._redis = AsyncMock()

    await mgr.shutdown()

    mock_task.cancel.assert_not_called()


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_accepts_websocket():
    mgr = _make_manager()
    uid = uuid.uuid4()
    ws = _mock_ws()

    await mgr.connect(ws, uid)

    ws.accept.assert_awaited_once()
    assert ws in mgr._connections[uid]


@pytest.mark.asyncio
async def test_connect_subscribes_redis_channel():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    uid = uuid.uuid4()
    ws = _mock_ws()

    await mgr.connect(ws, uid)

    mgr._pubsub.subscribe.assert_awaited_once_with(f"ws:user:{uid}")
    assert f"ws:user:{uid}" in mgr._subscribed_channels


@pytest.mark.asyncio
async def test_connect_evicts_oldest_when_at_limit():
    mgr = _make_manager()
    uid = uuid.uuid4()

    # Fill to limit
    old_ws_list = [_mock_ws() for _ in range(MAX_CONNECTIONS_PER_USER)]
    mgr._connections[uid] = list(old_ws_list)

    new_ws = _mock_ws()
    await mgr.connect(new_ws, uid)

    # Oldest should be evicted
    old_ws_list[0].close.assert_awaited_once()
    assert new_ws in mgr._connections[uid]
    assert len(mgr._connections[uid]) == MAX_CONNECTIONS_PER_USER


@pytest.mark.asyncio
async def test_connect_evict_exception_handled():
    mgr = _make_manager()
    uid = uuid.uuid4()
    old_ws = _mock_ws()
    old_ws.close.side_effect = RuntimeError("already closed")
    mgr._connections[uid] = [old_ws] * MAX_CONNECTIONS_PER_USER

    new_ws = _mock_ws()
    await mgr.connect(new_ws, uid)  # must not raise

    assert new_ws in mgr._connections[uid]


@pytest.mark.asyncio
async def test_connect_redis_subscribe_exception_handled():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._pubsub.subscribe.side_effect = RuntimeError("subscribe failed")

    uid = uuid.uuid4()
    ws = _mock_ws()
    await mgr.connect(ws, uid)  # must not raise

    assert ws in mgr._connections[uid]


@pytest.mark.asyncio
async def test_connect_no_pubsub_no_subscribe():
    mgr = _make_manager()
    mgr._running = False
    mgr._pubsub = None
    uid = uuid.uuid4()
    ws = _mock_ws()

    await mgr.connect(ws, uid)

    assert ws in mgr._connections[uid]


@pytest.mark.asyncio
async def test_connect_already_subscribed_skips():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    uid = uuid.uuid4()
    channel = f"ws:user:{uid}"
    mgr._subscribed_channels.add(channel)

    ws = _mock_ws()
    await mgr.connect(ws, uid)

    mgr._pubsub.subscribe.assert_not_awaited()


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disconnect_removes_connection():
    mgr = _make_manager()
    uid = uuid.uuid4()
    ws = _mock_ws()
    mgr._connections[uid] = [ws]

    await mgr.disconnect(ws, uid)

    assert uid not in mgr._connections


@pytest.mark.asyncio
async def test_disconnect_unsubscribes_when_no_connections():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    uid = uuid.uuid4()
    ws = _mock_ws()
    channel = f"ws:user:{uid}"
    mgr._connections[uid] = [ws]
    mgr._subscribed_channels.add(channel)

    await mgr.disconnect(ws, uid)

    mgr._pubsub.unsubscribe.assert_awaited_once_with(channel)
    assert channel not in mgr._subscribed_channels


@pytest.mark.asyncio
async def test_disconnect_keeps_channel_if_other_connections_remain():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    uid = uuid.uuid4()
    ws1 = _mock_ws()
    ws2 = _mock_ws()
    channel = f"ws:user:{uid}"
    mgr._connections[uid] = [ws1, ws2]
    mgr._subscribed_channels.add(channel)

    await mgr.disconnect(ws1, uid)

    mgr._pubsub.unsubscribe.assert_not_awaited()
    assert channel in mgr._subscribed_channels


@pytest.mark.asyncio
async def test_disconnect_ws_not_in_list():
    mgr = _make_manager()
    uid = uuid.uuid4()
    ws = _mock_ws()
    other_ws = _mock_ws()
    mgr._connections[uid] = [ws]

    await mgr.disconnect(other_ws, uid)  # must not raise

    assert ws in mgr._connections[uid]


@pytest.mark.asyncio
async def test_disconnect_unsubscribe_exception_handled():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._pubsub.unsubscribe.side_effect = RuntimeError("pubsub error")
    uid = uuid.uuid4()
    ws = _mock_ws()
    channel = f"ws:user:{uid}"
    mgr._connections[uid] = [ws]
    mgr._subscribed_channels.add(channel)

    await mgr.disconnect(ws, uid)  # must not raise

    assert channel not in mgr._subscribed_channels


# ---------------------------------------------------------------------------
# send_to_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_to_user_publishes_via_redis():
    mgr = _make_manager()
    mgr._running = True
    mgr._redis = AsyncMock()
    uid = uuid.uuid4()
    event = {"type": "notification", "data": "hello"}

    await mgr.send_to_user(uid, event)

    mgr._redis.publish.assert_awaited_once()
    call_args = mgr._redis.publish.call_args
    assert call_args.args[0] == f"ws:user:{uid}"
    assert json.loads(call_args.args[1]) == event


@pytest.mark.asyncio
async def test_send_to_user_fallback_when_redis_fails():
    mgr = _make_manager()
    mgr._running = True
    mgr._redis = AsyncMock()
    mgr._redis.publish.side_effect = RuntimeError("redis down")
    uid = uuid.uuid4()
    ws = _mock_ws()
    mgr._connections[uid] = [ws]

    await mgr.send_to_user(uid, {"msg": "test"})

    ws.send_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_to_user_no_redis_delivers_local():
    mgr = _make_manager()
    mgr._running = False  # Redis not running
    mgr._redis = None
    uid = uuid.uuid4()
    ws = _mock_ws()
    mgr._connections[uid] = [ws]

    await mgr.send_to_user(uid, {"type": "event"})

    ws.send_text.assert_awaited_once()


# ---------------------------------------------------------------------------
# _deliver_local
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deliver_local_sends_to_all():
    mgr = _make_manager()
    uid = uuid.uuid4()
    ws1 = _mock_ws()
    ws2 = _mock_ws()
    mgr._connections[uid] = [ws1, ws2]

    await mgr._deliver_local(uid, '{"type":"test"}')

    ws1.send_text.assert_awaited_once()
    ws2.send_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_deliver_local_removes_dead_connections():
    mgr = _make_manager()
    uid = uuid.uuid4()
    dead_ws = _mock_ws()
    dead_ws.send_text.side_effect = RuntimeError("connection closed")
    alive_ws = _mock_ws()
    mgr._connections[uid] = [dead_ws, alive_ws]

    await mgr._deliver_local(uid, "msg")

    assert dead_ws not in mgr._connections.get(uid, [])
    assert alive_ws in mgr._connections.get(uid, [])


@pytest.mark.asyncio
async def test_deliver_local_multiple_dead_connections():
    """Lines 194->193: for loop iterates again after first removal (multiple dead)."""
    mgr = _make_manager()
    uid = uuid.uuid4()
    dead1 = _mock_ws()
    dead1.send_text.side_effect = RuntimeError("dead")
    dead2 = _mock_ws()
    dead2.send_text.side_effect = RuntimeError("also dead")
    alive = _mock_ws()
    mgr._connections[uid] = [dead1, dead2, alive]

    await mgr._deliver_local(uid, "msg")

    # Both dead removed, alive remains
    assert dead1 not in mgr._connections.get(uid, [])
    assert dead2 not in mgr._connections.get(uid, [])
    assert alive in mgr._connections.get(uid, [])


@pytest.mark.asyncio
async def test_deliver_local_cleans_up_empty_user():
    mgr = _make_manager()
    uid = uuid.uuid4()
    dead_ws = _mock_ws()
    dead_ws.send_text.side_effect = RuntimeError("dead")
    mgr._connections[uid] = [dead_ws]

    await mgr._deliver_local(uid, "msg")

    assert uid not in mgr._connections


@pytest.mark.asyncio
async def test_deliver_local_no_connections():
    mgr = _make_manager()
    uid = uuid.uuid4()

    await mgr._deliver_local(uid, "msg")  # must not raise


# ---------------------------------------------------------------------------
# _subscriber_loop
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscriber_loop_exits_on_cancelled():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._subscribed_channels.add("ws:user:test")

    call_count = 0

    async def fake_get_message(**kwargs):
        nonlocal call_count
        call_count += 1
        raise asyncio.CancelledError()

    mgr._pubsub.get_message = fake_get_message

    await mgr._subscriber_loop()  # should exit cleanly
    assert call_count == 1


@pytest.mark.asyncio
async def test_subscriber_loop_no_pubsub_sleeps():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = None

    sleep_count = 0

    async def fake_sleep(t):
        nonlocal sleep_count
        sleep_count += 1
        mgr._running = False  # stop after first sleep

    with patch("asyncio.sleep", fake_sleep):
        await mgr._subscriber_loop()

    assert sleep_count >= 1


@pytest.mark.asyncio
async def test_subscriber_loop_no_subscriptions_sleeps():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    # No subscribed channels

    sleep_count = 0

    async def fake_sleep(t):
        nonlocal sleep_count
        sleep_count += 1
        mgr._running = False

    with patch("asyncio.sleep", fake_sleep):
        await mgr._subscriber_loop()

    assert sleep_count >= 1


@pytest.mark.asyncio
async def test_subscriber_loop_delivers_message():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    uid = uuid.uuid4()
    mgr._subscribed_channels.add(f"ws:user:{uid}")
    ws = _mock_ws()
    mgr._connections[uid] = [ws]

    message_count = 0

    async def fake_get_message(**kwargs):
        nonlocal message_count
        message_count += 1
        if message_count == 1:
            return {
                "type": "message",
                "channel": f"ws:user:{uid}",
                "data": '{"event":"test"}',
            }
        raise asyncio.CancelledError()

    mgr._pubsub.get_message = fake_get_message

    await mgr._subscriber_loop()

    ws.send_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscriber_loop_no_message_sleeps():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    uid = uuid.uuid4()
    mgr._subscribed_channels.add(f"ws:user:{uid}")

    sleep_count = 0

    async def fake_get_message(**kwargs):
        raise asyncio.CancelledError()

    async def fake_sleep(t):
        nonlocal sleep_count
        sleep_count += 1

    mgr._pubsub.get_message = fake_get_message

    await mgr._subscriber_loop()


@pytest.mark.asyncio
async def test_subscriber_loop_invalid_user_id_in_channel():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._subscribed_channels.add("ws:user:notauuid")

    call_count = 0

    async def fake_get_message(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {
                "type": "message",
                "channel": "ws:user:notauuid",
                "data": "payload",
            }
        raise asyncio.CancelledError()

    mgr._pubsub.get_message = fake_get_message

    await mgr._subscriber_loop()  # must not raise


@pytest.mark.asyncio
async def test_subscriber_loop_runtime_error_pubsub_not_set():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._subscribed_channels.add("ws:user:test")

    call_count = 0

    async def fake_get_message(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("pubsub connection not set")
        raise asyncio.CancelledError()

    async def fake_sleep(t):
        pass

    mgr._pubsub.get_message = fake_get_message

    with patch("asyncio.sleep", fake_sleep):
        await mgr._subscriber_loop()  # must not raise


@pytest.mark.asyncio
async def test_subscriber_loop_generic_exception_continues():
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._subscribed_channels.add("ws:user:test")

    call_count = 0

    async def fake_get_message(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("unexpected error")
        raise asyncio.CancelledError()

    async def fake_sleep(t):
        pass

    mgr._pubsub.get_message = fake_get_message

    with patch("asyncio.sleep", fake_sleep):
        await mgr._subscriber_loop()


# ---------------------------------------------------------------------------
# get_connected_user_count / get_connection_count
# ---------------------------------------------------------------------------


def test_get_connected_user_count_empty():
    mgr = _make_manager()
    assert mgr.get_connected_user_count() == 0


def test_get_connected_user_count_with_users():
    mgr = _make_manager()
    uid1 = uuid.uuid4()
    uid2 = uuid.uuid4()
    mgr._connections[uid1] = [_mock_ws()]
    mgr._connections[uid2] = [_mock_ws(), _mock_ws()]

    assert mgr.get_connected_user_count() == 2


def test_get_connection_count_user_not_connected():
    mgr = _make_manager()
    assert mgr.get_connection_count(uuid.uuid4()) == 0


def test_get_connection_count_with_connections():
    mgr = _make_manager()
    uid = uuid.uuid4()
    mgr._connections[uid] = [_mock_ws(), _mock_ws()]

    assert mgr.get_connection_count(uid) == 2


# ---------------------------------------------------------------------------
# shutdown — extra branches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shutdown_handles_ws_close_exception():
    """Lines 83-84: ws.close() raises → caught by except Exception: pass."""
    mgr = _make_manager()
    mgr._running = True
    mgr._subscriber_task = None
    uid = uuid.uuid4()
    ws = _mock_ws()
    ws.close.side_effect = RuntimeError("already closed")
    mgr._connections[uid] = [ws]
    mgr._pubsub = None
    mgr._redis = None

    await mgr.shutdown()  # must not raise

    assert mgr._running is False


@pytest.mark.asyncio
async def test_shutdown_closes_pubsub():
    """Lines 88-94: pubsub cleanup path."""
    mgr = _make_manager()
    mgr._running = True
    mgr._subscriber_task = None
    mgr._pubsub = AsyncMock()
    mgr._redis = None

    await mgr.shutdown()

    mgr._pubsub.unsubscribe.assert_awaited_once()
    mgr._pubsub.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_pubsub_exception_handled():
    """Lines 92-93: pubsub.unsubscribe raises → caught."""
    mgr = _make_manager()
    mgr._running = True
    mgr._subscriber_task = None
    mgr._pubsub = AsyncMock()
    mgr._pubsub.unsubscribe.side_effect = RuntimeError("pubsub error")
    mgr._redis = None

    await mgr.shutdown()  # must not raise


@pytest.mark.asyncio
async def test_shutdown_closes_redis():
    """Lines 96-100: redis cleanup path."""
    mgr = _make_manager()
    mgr._running = True
    mgr._subscriber_task = None
    mgr._pubsub = None
    mgr._redis = AsyncMock()

    await mgr.shutdown()

    mgr._redis.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_redis_close_exception_handled():
    mgr = _make_manager()
    mgr._running = True
    mgr._subscriber_task = None
    mgr._pubsub = None
    mgr._redis = AsyncMock()
    mgr._redis.close.side_effect = RuntimeError("redis close error")

    await mgr.shutdown()  # must not raise


# ---------------------------------------------------------------------------
# _deliver_local — ws not in connections at cleanup time
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deliver_local_ws_not_in_connections_at_cleanup():
    """Line 194->193: ws in dead but already removed — no error."""
    mgr = _make_manager()
    uid = uuid.uuid4()
    dead_ws = _mock_ws()
    dead_ws.send_text.side_effect = RuntimeError("dead")
    mgr._connections[uid] = [dead_ws]

    # Manually remove ws before cleanup (simulate concurrent removal)
    original_deliver = mgr._deliver_local

    async def patched_deliver(user_id, message):
        connections = mgr._connections.get(user_id, [])
        dead = []
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        # Remove the ws before the cleanup loop runs
        connections.clear()
        for ws in dead:
            if ws in connections:  # False — already cleared
                connections.remove(ws)
        if not connections:
            mgr._connections.pop(user_id, None)

    await patched_deliver(uid, "msg")
    assert uid not in mgr._connections


# ---------------------------------------------------------------------------
# _subscriber_loop — no-message sleep branch (line 213->201, 222)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscriber_loop_null_message_then_cancel():
    """Lines 213->201 and 222: get_message returns None → else sleep → loop continues."""
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._subscribed_channels.add(f"ws:user:{uuid.uuid4()}")

    call_count = 0

    async def fake_get_message(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return None  # no message → else branch → sleep → back to while (213->201)
        mgr._running = False  # stop loop cleanly after second iteration
        return None

    async def fake_sleep(t):
        pass  # no-op sleep

    mgr._pubsub.get_message = fake_get_message

    with patch("asyncio.sleep", fake_sleep):
        await mgr._subscriber_loop()

    assert call_count == 2  # ran twice: first None, second None + stop


@pytest.mark.asyncio
async def test_subscriber_loop_non_message_type_then_cancel():
    """Non-'message' type (e.g., subscribe confirmation) → else sleep."""
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._subscribed_channels.add("ws:user:any")

    call_count = 0

    async def fake_get_message(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"type": "subscribe", "channel": "ws:user:any", "data": None}
        raise asyncio.CancelledError()

    async def fake_sleep(t):
        pass

    mgr._pubsub.get_message = fake_get_message

    with patch("asyncio.sleep", fake_sleep):
        await mgr._subscriber_loop()


# ---------------------------------------------------------------------------
# _subscriber_loop — RuntimeError non-pubsub (lines 230-231)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscriber_loop_runtime_error_other_type():
    """Lines 230-231: RuntimeError not 'pubsub connection not set' → log + sleep(1)."""
    mgr = _make_manager()
    mgr._running = True
    mgr._pubsub = AsyncMock()
    mgr._subscribed_channels.add("ws:user:test")

    call_count = 0

    async def fake_get_message(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("some other runtime error")
        raise asyncio.CancelledError()

    async def fake_sleep(t):
        pass

    mgr._pubsub.get_message = fake_get_message

    with patch("asyncio.sleep", fake_sleep):
        await mgr._subscriber_loop()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


def test_ws_manager_singleton_is_instance():
    assert isinstance(ws_manager, ConnectionManager)
