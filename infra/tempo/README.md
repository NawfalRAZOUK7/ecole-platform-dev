# Grafana Tempo Distributed Tracing

Grafana Tempo distributed tracing backend for the Ecole Platform. Collects OpenTelemetry spans from services and provides end-to-end request tracing.

## Files

- **tempo.yml** - Tempo storage, ingestion, and retention configuration

## Purpose

Tempo provides:
- **Distributed Tracing** - Track requests across microservices
- **Span Collection** - Receives OpenTelemetry spans via gRPC or HTTP
- **Storage** - Stores traces with configurable retention
- **Query Interface** - Retrieve and analyze traces
- **Grafana Integration** - Visualize traces with request flows
- **Performance Analysis** - Identify latency bottlenecks

## Supported Protocols

- **OpenTelemetry Protocol (OTLP)** - gRPC at :4317 and HTTP at :4318
- **Jaeger** - gRPC at :14250 and Thrift at :14268 (backward compatibility)
- **Zipkin** - HTTP at :9411

## Instrumentation

Application services send traces to Tempo via OpenTelemetry SDK:

```python
# Python example
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

exporter = OTLPSpanExporter(endpoint="tempo:4317")
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))
```

```javascript
// Node.js example
const { NodeSDK } = require("@opentelemetry/sdk-node");
const { OTLPTraceExporter } = require("@opentelemetry/exporter-trace-otlp-grpc");

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({ url: "grpc://tempo:4317" }),
});
sdk.start();
```

## Configuration

From `tempo.yml`:

### Ingestion
- Listens for OTLP spans on multiple protocols
- Batch size and timeout tuning
- Rate limiting to prevent overload

### Storage
- **Backend** - Local filesystem (development) or S3/GCS (production)
- **Block Retention** - How long blocks are kept (default: 24 hours)
- **Search Retention** - How long traces are searchable (default: 24 hours)
- **Compaction** - Automated block compaction and deduplication

### Query Capabilities
- Search by trace ID
- Filter by span attributes (service, duration, status, tags)
- Full-text search in span names and attributes
- Time range queries

## Trace Structure

Typical trace for an API request:
```
Trace: GET /api/students/{id}
├── Span: API Handler (50ms)
│   ├── Span: Database Query (40ms)
│   │   └── Span: PostgreSQL Protocol (35ms)
│   └── Span: Cache Lookup (5ms)
└── Span: Response Serialization (2ms)
```

Each span includes:
- Trace ID (shared across request)
- Span ID (unique to operation)
- Parent Span ID (causal relationship)
- Operation name (what the span does)
- Start time and duration
- Tags (service, environment, user_id, etc.)
- Logs (structured error information)
- Status (success, error, etc.)

## Querying Traces

### Via Tempo UI
```bash
http://localhost:3200
```

### Via Grafana
1. Go to Explore
2. Select Tempo datasource
3. Search by trace ID or filter by attributes

### Example Queries
```
# Find slow requests
{ span.duration > 1000ms }

# API errors
{ service="ecole-backend" status="error" }

# Student API calls
{ service="ecole-backend" http.method="GET" http.target="/api/students/*" }

# Database queries exceeding threshold
{ service="postgres" duration > 500ms }
```

## Common Use Cases

### Performance Debugging
1. Identify slow API endpoint from Grafana dashboard
2. Click "View traces" to see recent traces
3. Analyze span breakdown to find bottleneck
4. Correlate with logs and metrics

### Error Investigation
1. Search for traces with status="error"
2. View error span and error logs
3. Trace back to root cause
4. Check related service traces

### Dependency Mapping
1. View trace waterfall for complex request
2. Identify all services involved
3. Understand critical path (longest chain)
4. Optimize highest-latency spans

## Data Retention

Production configuration:
- **Block Retention** - 72 hours (3 days)
- **Search Retention** - 24 hours (1 day)

Adjust based on:
- Storage capacity
- Debugging needs
- Compliance requirements

Note: Traces older than search retention are archived but still accessible via trace ID if blocks haven't been compacted.

## Storage Options

### Development (Local Filesystem)
```yaml
storage:
  trace:
    backend: local
```

### Production (S3)
```yaml
storage:
  trace:
    backend: s3
    s3:
      bucket: ecole-traces
      endpoint: s3.amazonaws.com
```

### Production (GCS)
```yaml
storage:
  trace:
    backend: gcs
    gcs:
      bucket: ecole-traces
```

## Scaling Considerations

For high-volume tracing:
- Deploy Tempo distributors, ingesters, queriers as separate services
- Use object storage (S3/GCS) instead of local filesystem
- Add caching layer for frequently accessed traces
- Implement sampling at SDK level to reduce volume

See `../DEPLOYMENT.md` for distributed Tempo configuration.

## Monitoring Tempo

Monitor via:
- Prometheus metrics on :3200/metrics
- Grafana dashboard for Tempo health
- Trace query latency
- Ingestion rate and errors
- Storage usage

## Integration Points

- **Prometheus** - Export metrics for monitoring Tempo itself
- **Grafana** - Visualize and query traces
- **Loki** - Correlate traces with logs
- **Application Services** - Instrument with OpenTelemetry SDK

## Documentation

See `../DEPLOYMENT.md` for:
- Distributed Tempo architecture
- Sampling strategies
- Custom instrumentation
- Troubleshooting trace ingestion issues
- Retention policy configuration
