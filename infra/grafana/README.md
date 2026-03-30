# Grafana Monitoring

Grafana visualization and monitoring dashboards for the Ecole Platform. Includes auto-provisioned dashboards and datasources for comprehensive observability.

## Subdirectories

- **dashboards/** - Dashboard JSON definitions (business metrics, API performance, infrastructure health)
- **provisioning/** - Auto-provisioning configuration for dashboards and datasources

## Key Dashboards

Deployed automatically via provisioning:

### Application Dashboards
- **api-overview.json** - API request/response metrics, latency, error rates
- **auth-sessions.json** - User authentication and session metrics
- **business-education.json** - Educational metrics (student progress, course completion, Moroccan grading analytics)
- **billing-providers.json** - Billing system and payment provider metrics
- **db-redis-health.json** - PostgreSQL and Redis health, connection counts, memory usage

### Infrastructure Dashboards
- Node/container metrics
- Network I/O and throughput
- Storage usage and IOPS
- Docker/Kubernetes resource utilization

## Datasources

Automatically configured to connect:
- **Prometheus** - Metrics backend
- **Loki** - Logs backend
- **Tempo** - Distributed traces

See `provisioning/datasources/` for configuration.

## Access

Development:
```bash
http://localhost:3000
# Default credentials: admin / admin
```

Staging/Production:
```bash
https://monitoring.ecole.example.com
# Use SSO or configured auth backend
```

## Dashboard Management

### View Existing Dashboards
```bash
http://localhost:3000/dashboards
```

### Create New Dashboard
1. Click "+" → "Dashboard" in Grafana UI
2. Add panels with Prometheus/Loki queries
3. Export dashboard JSON to `dashboards/`
4. Restart Grafana to auto-provision

### Update Dashboard
Edit JSON file in `dashboards/` and restart Grafana, or use Grafana UI with `provisioning/` mode enabled.

## Provisioning Configuration

See `provisioning/` subdirectory for:
- Dashboard auto-loading from `dashboards/` directory
- Datasource connection auto-setup
- Default dashboard layout

## Documentation

See `../DEPLOYMENT.md` for:
- Datasource configuration details
- Custom dashboard creation
- Authentication setup (LDAP, SAML)
- Dashboard backup and recovery
