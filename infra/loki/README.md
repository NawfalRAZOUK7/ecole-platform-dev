# Grafana Loki Log Aggregation

Loki log aggregation system for the Ecole Platform. Collects logs from all containers and services with configurable retention, indexing, and alerting.

## Files

- **loki-config.yml** - Loki storage, ingestion, and retention configuration
- **promtail-config.yml** - Promtail log collection agent configuration
- **rules/** - Loki alerting rules for log-based alerts

## Purpose

Loki provides:
- Centralized log collection from all services
- Efficient log storage with label-based indexing
- LogQL query language for log analysis
- Log-based alerting rules
- Integration with Grafana for visualization

## Log Collection

Promtail agent:
- Runs as sidecar in each container or as separate service
- Tails application logs from containers
- Adds labels (service name, environment, version)
- Ships logs to Loki via push API

## Storage Configuration

From `loki-config.yml`:
- **Storage Backend** - Local filesystem (development) or S3 (production)
- **Index Retention** - 24 hours (configurable)
- **Log Retention** - 30 days (configurable per log stream)
- **Chunk Size** - 262KB (balanced for performance)

## Querying Logs

Via Grafana:
```
{job="ecole-backend"} | logfmt
{service="api", env="production"} | json
```

Via Loki API:
```bash
curl 'http://localhost:3100/loki/api/v1/query_range?query={job="ecole-backend"}'
```

## Log Labels

Standard labels applied to all logs:
- `job` - Service name (e.g., "ecole-backend", "postgres")
- `service` - Application service identifier
- `env` - Environment (dev, staging, prod)
- `pod` - Container/pod name
- `stream` - stdout or stderr

## Alerting Rules

Log-based alerts configured in `rules/` directory:
- Error rate thresholds
- Security event detection (failed auth, suspicious patterns)
- Service crash detection
- Database error monitoring
- Request latency warnings

## Subdirectories

- **rules/** - LogQL alerting rule definitions

## Common Queries

### Error logs in production
```
{env="production"} | json | level="error"
```

### Authentication failures
```
{job="ecole-backend"} | json | level="error" | pattern="auth"
```

### Database connection errors
```
{job="postgres"} | pattern="connection"
```

### API request latency
```
{job="ecole-api"} | json | latency > 1000
```

## Scaling Considerations

For large scale deployments:
- Use S3 or GCS backend storage instead of filesystem
- Deploy Loki in distributed mode (ingester, querier, distributor)
- Add caching layer for frequently accessed logs
- Implement log sampling to reduce storage costs

See `../DEPLOYMENT.md` for production configuration.

## Documentation

See subdirectories for:
- `rules/README.md` - Alerting rules configuration

See `../DEPLOYMENT.md` for:
- Log retention policies by environment
- S3 backend configuration
- Distributed Loki setup
- Performance tuning
