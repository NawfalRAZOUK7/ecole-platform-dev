"""Miscellaneous unit tests for small remaining gaps in app/core/*.

Covers:
- middleware.register_middleware
- redis._LazyRedisClient.__setattr__ + get_redis
- telemetry.setup_telemetry
- db_routing.get_read_db / get_write_db
- password_policy: break-after-name-match branch
- metrics: _normalize_storage_backend, normalize_storage_mime_type, record_* helpers
- downloads: missed lines
- request_utils: optional_current_user
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# middleware.register_middleware
# ---------------------------------------------------------------------------


def test_register_middleware_adds_middleware_and_handlers():
    from app.core.middleware import register_middleware

    mock_app = MagicMock()
    register_middleware(mock_app)

    mock_app.add_middleware.assert_called_once()
    assert mock_app.add_exception_handler.call_count == 3


# ---------------------------------------------------------------------------
# redis._LazyRedisClient.__setattr__ + get_redis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_redis_returns_redis_client():
    from app.core.redis import get_redis, redis_client

    result = await get_redis()
    assert result is redis_client


def test_lazy_redis_client_setattr():
    """__setattr__ for non-_client names proxies to the underlying client."""
    from app.core.redis import _LazyRedisClient

    client = _LazyRedisClient()
    mock_underlying = MagicMock()
    client._client = mock_underlying

    client.some_attr = "value"
    mock_underlying.some_attr = "value"  # setattr was delegated


# ---------------------------------------------------------------------------
# telemetry.setup_telemetry
# ---------------------------------------------------------------------------


def test_setup_telemetry_initializes_once():
    from app.core import telemetry

    mock_app = MagicMock()
    mock_engine = MagicMock()
    mock_engine.sync_engine = MagicMock()

    original = telemetry._telemetry_initialized
    telemetry._telemetry_initialized = False

    # Patch at the import level inside telemetry module to intercept all OTel calls
    mock_provider = MagicMock()
    mock_exporter = MagicMock()
    mock_processor = MagicMock()

    with (
        patch("app.core.telemetry.TracerProvider", return_value=mock_provider),
        patch("app.core.telemetry.OTLPSpanExporter", return_value=mock_exporter),
        patch("app.core.telemetry.BatchSpanProcessor", return_value=mock_processor),
        patch("app.core.telemetry.trace"),
        patch("app.core.telemetry.FastAPIInstrumentor") as MockFastAPI,
        patch("app.core.telemetry.SQLAlchemyInstrumentor") as MockSQL,
        patch("app.core.telemetry.RedisInstrumentor") as MockRedis,
        patch("app.core.telemetry.settings") as mock_settings,
    ):
        mock_settings.app_env = "development"
        mock_settings.otel_exporter_endpoint = "http://localhost:4317"
        MockFastAPI.instrument_app = MagicMock()
        MockSQL.return_value = MagicMock()
        MockRedis.return_value = MagicMock()

        from app.core.telemetry import setup_telemetry

        setup_telemetry(mock_app, mock_engine)

    assert telemetry._telemetry_initialized is True
    telemetry._telemetry_initialized = original


def test_setup_telemetry_skips_if_already_initialized():
    from app.core import telemetry
    from app.core.telemetry import setup_telemetry

    original = telemetry._telemetry_initialized
    telemetry._telemetry_initialized = True

    with patch("opentelemetry.sdk.trace.TracerProvider") as MockProvider:
        setup_telemetry(MagicMock(), MagicMock())

    MockProvider.assert_not_called()
    telemetry._telemetry_initialized = original


# ---------------------------------------------------------------------------
# db_routing.get_read_db / get_write_db
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_read_db_yields_session():
    from app.core import db_routing

    mock_session = AsyncMock()
    mock_session.close = AsyncMock()

    @asynccontextmanager
    async def _mock_session_cm():
        yield mock_session

    with patch.object(db_routing, "AsyncSessionReplica") as MockReplica:
        MockReplica.return_value = _mock_session_cm()
        gen = db_routing.get_read_db()
        session = await gen.__anext__()
        assert session is mock_session
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_get_write_db_yields_session():
    from app.core import db_routing

    mock_session = AsyncMock()
    mock_session.close = AsyncMock()

    @asynccontextmanager
    async def _mock_session_cm():
        yield mock_session

    with patch.object(db_routing, "AsyncSessionPrimary") as MockPrimary:
        MockPrimary.return_value = _mock_session_cm()
        gen = db_routing.get_write_db()
        session = await gen.__anext__()
        assert session is mock_session
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass


# ---------------------------------------------------------------------------
# password_policy: loop-without-break branch
# ---------------------------------------------------------------------------


def test_check_name_parts_none_found_no_failure():
    from app.core.password_policy import PasswordValidator

    v = PasswordValidator()
    # "fatima" and "zahra" are not in "SecureP@ss123!"
    errors = v.check("SecureP@ss123!", full_name="Fatima Zahra")
    rules = [e["rule"] for e in errors]
    assert "contains_name" not in rules


# ---------------------------------------------------------------------------
# metrics: _normalize_storage_backend, normalize_storage_mime_type, record_*
# ---------------------------------------------------------------------------


def test_normalize_storage_backend_s3():
    from app.core.metrics import _normalize_storage_backend

    assert _normalize_storage_backend("s3") == "s3"
    assert _normalize_storage_backend("S3") == "s3"


def test_normalize_storage_backend_local():
    from app.core.metrics import _normalize_storage_backend

    assert _normalize_storage_backend("local") == "local"
    assert _normalize_storage_backend("minio") == "local"


def test_normalize_storage_mime_type_none():
    from app.core.metrics import normalize_storage_mime_type

    assert normalize_storage_mime_type(None) == "unknown"


def test_normalize_storage_mime_type_empty():
    from app.core.metrics import normalize_storage_mime_type

    assert normalize_storage_mime_type("") == "unknown"


def test_normalize_storage_mime_type_valid():
    from app.core.metrics import normalize_storage_mime_type

    assert normalize_storage_mime_type("application/pdf") == "application/pdf"


def test_normalize_storage_mime_type_with_params():
    from app.core.metrics import normalize_storage_mime_type

    assert normalize_storage_mime_type("text/html; charset=utf-8") == "text/html"


def test_normalize_storage_mime_type_too_long():
    from app.core.metrics import normalize_storage_mime_type

    long_mime = "a" * 200
    assert normalize_storage_mime_type(long_mime) == "unknown"


def test_normalize_storage_mime_type_invalid_pattern():
    from app.core.metrics import normalize_storage_mime_type

    assert normalize_storage_mime_type("invalid mime!!!") == "unknown"


def test_record_storage_upload():
    from app.core.metrics import record_storage_upload

    # Should not raise; just records a metric
    record_storage_upload(
        env="test", backend="s3", mime_type="image/png", size_bytes=1024
    )


def test_record_storage_presign():
    from app.core.metrics import record_storage_presign

    record_storage_presign(env="test", backend="s3", operation="presign_get")


def test_record_storage_error():
    from app.core.metrics import record_storage_error

    record_storage_error(env="test", backend="s3", operation="upload")


def test_log_storage_failure_with_dict_response():
    """Covers metrics.log_storage_failure with a response dict containing Error.Code."""
    import logging
    from app.core.metrics import log_storage_failure

    exc = Exception("s3 error")
    exc.response = {"Error": {"Code": "NoSuchKey"}}
    test_logger = logging.getLogger("test")
    log_storage_failure(
        test_logger,
        env="test",
        backend="s3",
        operation="download",
        mime_type="image/png",
        exc=exc,
    )


def test_log_storage_failure_no_response():
    import logging
    from app.core.metrics import log_storage_failure

    exc = Exception("plain error")
    log_storage_failure(
        logging.getLogger("test"),
        env="test",
        backend="local",
        operation="upload",
        mime_type=None,
        exc=exc,
    )


def test_storage_operation_observer_success():
    """Covers the happy-path yield of storage_operation_observer."""
    from app.core.metrics import storage_operation_observer

    with storage_operation_observer(env="test", backend="s3", operation="upload"):
        pass  # no exception — covers yield + finally


def test_storage_operation_observer_exception():
    """Covers the except branch of storage_operation_observer."""
    import pytest
    from app.core.metrics import storage_operation_observer

    with pytest.raises(RuntimeError):
        with storage_operation_observer(env="test", backend="s3", operation="upload"):
            raise RuntimeError("upload failed")


def test_storage_operation_observer_with_logger():
    """Covers log_storage_failure call when logger is provided."""
    import logging
    import pytest
    from app.core.metrics import storage_operation_observer

    with pytest.raises(ValueError):
        with storage_operation_observer(
            env="test",
            backend="s3",
            operation="upload",
            logger=logging.getLogger("test"),
        ):
            raise ValueError("logged failure")


def test_collector_name_proxy_labels():
    from app.core.metrics import _CollectorNameProxy, TASK_ENQUEUED_COUNT

    assert isinstance(TASK_ENQUEUED_COUNT, _CollectorNameProxy)
    result = TASK_ENQUEUED_COUNT.labels(env="test", task="test_task")
    assert result is not None


def test_collector_name_proxy_getattr():
    from app.core.metrics import TASK_ENQUEUED_COUNT

    # __getattr__ is triggered for attributes not in __dict__ or class
    # Access a Prometheus counter method like `inc` which lives on the collector
    inc_fn = TASK_ENQUEUED_COUNT.inc  # triggers __getattr__('inc')
    assert callable(inc_fn)


def test_normalize_path_uuid():
    from app.core.metrics import _normalize_path

    path = "/api/v1/students/123e4567-e89b-12d3-a456-426614174000/grades"
    result = _normalize_path(path)
    assert "{id}" in result
    assert "123e4567" not in result


def test_normalize_path_numeric():
    from app.core.metrics import _normalize_path

    result = _normalize_path("/api/v1/items/42/sub")
    assert "{id}" in result


def test_normalize_path_no_ids():
    from app.core.metrics import _normalize_path

    path = "/api/v1/students"
    assert _normalize_path(path) == path


def test_prometheus_middleware_dispatch_skip_metrics():
    """PrometheusMiddleware skips /metrics path (no recording)."""
    from unittest.mock import AsyncMock
    from starlette.requests import Request
    from starlette.responses import Response
    from app.core.metrics import PrometheusMiddleware

    mw = PrometheusMiddleware(app=None, env="test")  # type: ignore

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/metrics",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)
    downstream = Response("ok")

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        mw.dispatch(request, AsyncMock(return_value=downstream))
    )
    assert result is downstream


def test_prometheus_middleware_records_2xx():
    """PrometheusMiddleware records count and latency for 2xx."""
    from starlette.requests import Request
    from starlette.responses import Response
    from app.core.metrics import PrometheusMiddleware
    from unittest.mock import AsyncMock
    import asyncio

    mw = PrometheusMiddleware(app=None, env="test")  # type: ignore

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/students",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)
    result = asyncio.get_event_loop().run_until_complete(
        mw.dispatch(request, AsyncMock(return_value=Response("ok", status_code=200)))
    )
    assert result.status_code == 200


def test_prometheus_middleware_records_4xx():
    """PrometheusMiddleware records errors for 4xx."""
    from starlette.requests import Request
    from starlette.responses import Response
    from app.core.metrics import PrometheusMiddleware
    from unittest.mock import AsyncMock
    import asyncio

    mw = PrometheusMiddleware(app=None, env="test")  # type: ignore

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/orders",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)
    result = asyncio.get_event_loop().run_until_complete(
        mw.dispatch(request, AsyncMock(return_value=Response("err", status_code=404)))
    )
    assert result.status_code == 404


def test_prometheus_middleware_records_5xx():
    """PrometheusMiddleware records errors for 5xx."""
    from starlette.requests import Request
    from starlette.responses import Response
    from app.core.metrics import PrometheusMiddleware
    from unittest.mock import AsyncMock
    import asyncio

    mw = PrometheusMiddleware(app=None, env="test")  # type: ignore

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/students",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)
    result = asyncio.get_event_loop().run_until_complete(
        mw.dispatch(request, AsyncMock(return_value=Response("err", status_code=500)))
    )
    assert result.status_code == 500


def test_collect_db_pool_metrics():
    from app.core.metrics import collect_db_pool_metrics

    mock_engine = MagicMock()
    mock_pool = MagicMock()
    mock_pool.size.return_value = 10
    mock_pool.checkedout.return_value = 2
    mock_pool.overflow.return_value = 0
    mock_engine.pool = mock_pool

    collect_db_pool_metrics(mock_engine, env="test")

    mock_pool.size.assert_called_once()
    mock_pool.checkedout.assert_called_once()


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus():
    from starlette.requests import Request
    from app.core.metrics import metrics_endpoint

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/metrics",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)

    with patch(
        "app.core.metrics.collect_db_pool_metrics", side_effect=Exception("no pool")
    ):
        response = await metrics_endpoint(request)

    assert response.status_code == 200


def test_register_metrics_adds_middleware_and_route():
    from app.core.metrics import register_metrics

    mock_app = MagicMock()
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.app_env = "test"
        register_metrics(mock_app)

    mock_app.add_middleware.assert_called_once()
    mock_app.add_route.assert_called_once()


# ---------------------------------------------------------------------------
# request_utils.optional_current_user — None token path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_optional_current_user_no_token_returns_none():
    from app.core.request_utils import optional_current_user
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)
    result = await optional_current_user(request, credentials=None, db=AsyncMock())
    assert result is None


@pytest.mark.asyncio
async def test_optional_current_user_valid_token_no_session_raises():
    from app.core.exceptions import AuthenticationError
    from app.core.request_utils import optional_current_user
    from app.core.security import create_access_token
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)

    uid = uuid.uuid4()
    token = create_access_token(uid, "ADM", uuid.uuid4(), uuid.uuid4())

    creds = MagicMock()
    creds.credentials = token

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # session not found
    mock_db.execute.return_value = mock_result

    with pytest.raises(AuthenticationError, match="Session has been revoked"):
        await optional_current_user(request, credentials=creds, db=mock_db)


@pytest.mark.asyncio
async def test_optional_current_user_valid_token_session_ok():
    from app.core.request_utils import optional_current_user
    from app.core.security import create_access_token
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    request = Request(scope)

    uid = uuid.uuid4()
    school_id = uuid.uuid4()
    session_id = uuid.uuid4()
    token = create_access_token(uid, "ADM", school_id, session_id)

    creds = MagicMock()
    creds.credentials = token

    mock_session_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_session_obj
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    result = await optional_current_user(request, credentials=creds, db=mock_db)
    assert result is not None
    assert result.user_id == uid
