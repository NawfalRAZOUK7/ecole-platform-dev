"""OpenTelemetry setup for distributed tracing."""

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings

_telemetry_initialized = False


def setup_telemetry(app: FastAPI, engine: AsyncEngine) -> None:
    """Initialize tracing once for the process."""
    global _telemetry_initialized

    if _telemetry_initialized:
        return

    resource = Resource.create(
        {
            "service.name": "ecole-backend",
            "service.version": "0.1.0",
            "deployment.environment": settings.app_env,
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_endpoint,
        insecure=True,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    RedisInstrumentor().instrument()
    _telemetry_initialized = True
