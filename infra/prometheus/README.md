# Prometheus Monitoring

Prometheus time-series metrics database for the Ecole Platform. Collects metrics from all services and evaluates alerting rules.

## Files

- **prometheus.yml** - Prometheus scrape configuration (targets, intervals, relabeling)
- **alert_rules.yml** - Alert rule definitions for SLAs, error rates, and resource thresholds

## Purpose

Prometheus provides:
- Centralized metrics collection from instrumented services
- Powerful time-series data storage and querying
- PromQL query language for metrics analysis
- Alert rule evaluation and firing
- Integration with Grafana for visualization
- Long-term metrics retention (15 days default, configurable)

## Scrape Targets

Configured in `prometheus.yml`:
- **Application Backend** - Custom metrics from application code
- **Prometheus Self** - Prometheus own metrics

> Note: Additional exporters (PostgreSQL, Redis, NGINX, Node, Docker/cadvisor)
> can be added to `docker-compose.monitoring.yml` as needed.

## Key Metrics

### Application Metrics
- HTTP request rate and latency (p50, p95, p99)
- API endpoint performance by method/path
- Authentication success/failure rates
- Database query latency
- Cache hit/miss ratios

### System Metrics (when exporters are deployed)
- CPU usage by container
- Memory usage and pressure
- Disk I/O and available space
- Network throughput
- Container startup/restart events

### Business Metrics
- Student enrollment counts
- Course completion rates
- API usage by school/organization
- Feature adoption metrics

## Scrape Interval

Default intervals configured in `prometheus.yml`:
- Standard metrics: 15 seconds
- Node metrics: 30 seconds
- Custom application metrics: 10 seconds (high granularity)

Adjust intervals based on:
- Storage capacity requirements
- Query precision needs
- Load on monitoring system

## Alert Rules

Alerts defined in `alert_rules.yml` for:
- High error rates (API, database, service failures)
- Resource exhaustion (CPU, memory, disk)
- SLA violations (response time, availability)
- Service health (uptime, connectivity)
- Backup and disaster recovery metrics

Rules are evaluated continuously and fire alerts to AlertManager.

## Querying Metrics

Via Prometheus UI:
```bash
http://localhost:9090/
```

Example PromQL queries:
```
# API request rate
rate(http_requests_total[5m])

# API p99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Memory usage as percentage
(container_memory_working_set_bytes / container_spec_memory_limit_bytes) * 100

# Database connection pool usage
pg_stat_activity_count / pg_settings_max_connections * 100
```

## Data Retention

Configuration in docker-compose file:
```yaml
command:
  - '--storage.tsdb.retention.time=15d'
```

Adjust `retention.time` based on:
- Available storage capacity
- Historical analysis needs
- Cost constraints

Typical retention:
- Development: 7 days
- Staging: 15 days
- Production: 30 days

## High Availability

For HA Prometheus setup:
- Deploy multiple Prometheus instances
- Use Cortex or Thanos for remote storage
- Configure service discovery for dynamic targets
- Use AlertManager clustering for alert deduplication

See `../DEPLOYMENT.md` for HA configuration.

## Troubleshooting

**Metrics missing:**
- Check target status: Prometheus UI → Status → Targets
- Verify service is running and exposing metrics endpoint
- Check firewall rules allow metric collection
- Review prometheus.yml for correct target addresses

**High memory usage:**
- Reduce number of scraped metrics
- Increase scrape interval
- Reduce retention time
- Add more Prometheus replicas

**Query slow:**
- Use appropriate time ranges
- Avoid querying all data at once
- Aggregate metrics appropriately
- Use recording rules for complex queries

## Documentation

See `../DEPLOYMENT.md` for:
- Adding new metric targets
- Recording rules for common queries
- Federated Prometheus setup
- Remote storage configuration (Cortex/Thanos)
- Performance tuning

See `../grafana/README.md` for metrics visualization.
