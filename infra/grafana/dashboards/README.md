# Grafana Dashboards

Dashboard JSON definitions for monitoring Ecole Platform. Each dashboard is automatically loaded via provisioning and provides specific insights into platform health, performance, and business metrics.

Dashboard tags and panel labels should use backend bounded contexts when a metric is domain-specific: `auth`, `user`, `school`, `academic`, `lms`, `billing`, `content`, `communication`, `reports`, `admin`, `sync`, `ai`, and `operations`.

## Available Dashboards

### api-overview.json
**Purpose** - API request metrics and performance
**Contexts** - all API domains, grouped by route or explicit domain labels where available

**Metrics Monitored**
- Request rate (req/sec by endpoint)
- Response latency (p50, p95, p99)
- HTTP status codes (2xx, 4xx, 5xx)
- Error rates and error types
- API gateway throughput

**Use Cases**
- Monitor API performance during deployments
- Detect performance regressions
- Identify slow endpoints for optimization

### auth-sessions.json
**Purpose** - Authentication and user session monitoring
**Contexts** - `auth`, `user`

**Metrics Monitored**
- Active user sessions
- Login success/failure rates
- JWT token issuance and expiration
- Session timeout metrics
- Geographic origin of logins

**Use Cases**
- Monitor authentication system health
- Detect unusual login patterns
- Track concurrent user load
- Audit authentication failures

### business-education.json
**Purpose** - Educational business metrics and Moroccan grading analytics
**Contexts** - `school`, `academic`, `lms`, `reports`

**Metrics Monitored**
- Student progress and completion rates
- Course enrollment and dropout metrics
- Grade distribution by subject (aligned to Moroccan curriculum)
- Teacher assessment metrics
- School performance aggregates
- Subject-specific analytics (Arabic, French, Math, etc.)

**Use Cases**
- Track student learning outcomes
- Monitor school adoption metrics
- Analyze grading patterns
- Identify at-risk students

### billing-providers.json
**Purpose** - Payment processing and subscription metrics
**Contexts** - `billing`, `reports`

**Metrics Monitored**
- Payment transactions (success/failure)
- Subscription churn rate
- Revenue by school tier
- Payment provider uptime
- Refund metrics
- Billing reconciliation status

**Use Cases**
- Monitor revenue health
- Detect payment processing issues
- Track churn and retention
- Verify billing accuracy

### db-redis-health.json
**Purpose** - Database and cache infrastructure health
**Contexts** - `operations`

**Metrics Monitored**
- PostgreSQL connection count and pool utilization
- Query latency and slow queries
- Database disk usage and growth rate
- Redis memory usage and eviction rate
- Cache hit/miss ratios
- Replication lag (if applicable)

**Use Cases**
- Identify database performance bottlenecks
- Monitor resource exhaustion
- Detect memory pressure
- Track cache effectiveness

### storage-minio.json
**Purpose** - MinIO/S3-backed object storage operations
**Contexts** - `content`, `reports`, `operations`

**Metrics Monitored**
- Upload count and uploaded bytes by backend and MIME type
- Presigned URL generation rate
- Storage operation latency by operation
- Storage operation errors by backend and operation

**Use Cases**
- Detect MinIO connectivity or credential failures
- Monitor presigned URL generation during media-heavy usage
- Verify upload throughput during migrations or releases
- Confirm storage errors stay low after rollback or backend flips

## Adding New Dashboards

1. Create dashboard in Grafana UI
2. Add panels with Prometheus/Loki queries
3. Set appropriate time ranges and refresh rates
4. Export JSON: Dashboard menu → "Share" → "Export" → "Save JSON"
5. Save to `dashboards/` directory with descriptive name
6. Restart Grafana to auto-provision:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart grafana
   ```

## Query Language

Dashboards use:
- **Prometheus PromQL** - For metrics queries
- **Loki LogQL** - For log-based queries
- **Tempo TraceQL** - For distributed trace queries

## Best Practices

- Use meaningful panel titles and descriptions
- Tag domain-specific panels with the bounded context name
- Set appropriate alert thresholds
- Include units and formatting
- Use consistent color schemes
- Document custom queries
- Test dashboards across time ranges
