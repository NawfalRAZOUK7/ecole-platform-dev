# Datasource Provisioning

Automatic datasource configuration for Grafana. Configures connections to Prometheus, Loki, and Tempo backends on startup.

## Configuration File

- **datasources.yml** - Datasource definitions for metrics, logs, and traces

## Datasources Configured

### Prometheus
- **Purpose** - Metrics backend
- **Connection** - `http://prometheus:9090`
- **Use** - Query application and infrastructure metrics
- **Query Language** - PromQL

### Loki
- **Purpose** - Log aggregation backend
- **Connection** - `http://loki:3100`
- **Use** - Query logs from all containers
- **Query Language** - LogQL

### Tempo
- **Purpose** - Distributed tracing backend
- **Connection** - `http://tempo:3200`
- **Use** - Query distributed traces and spans
- **Query Language** - TraceQL

## How Datasources Are Configured

On Grafana startup:
1. Read datasources.yml
2. Create/update datasource connections
3. Test connectivity to each backend
4. Make available for dashboard queries

## Testing Datasources

In Grafana UI:
1. Go to Configuration → Data Sources
2. Click datasource name
3. Click "Test" button to verify connectivity
4. Confirm metrics/logs/traces appear in selector

## Adding New Datasources

To add a new datasource:

1. Edit `datasources.yml` with new datasource definition
2. Include connection details, auth, and query settings
3. Restart Grafana:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart grafana
   ```
4. Datasource appears in Data Sources list

## Configuration Format

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
    editable: false
```

## Security

- Use `access: proxy` for secure backend communication
- Database URLs and credentials stored securely in Grafana
- Connections from Grafana container to backends use internal Docker network
- API keys/tokens stored encrypted in Grafana database

## Troubleshooting

**Red datasource status:**
- Check backend service is running
- Verify network connectivity between containers
- Review Grafana logs for connection errors
- Test connectivity manually from Grafana container:
  ```bash
  docker-compose exec grafana curl http://prometheus:9090/-/healthy
  ```

**Queries fail:**
- Test datasource connection via Grafana UI
- Verify query syntax (PromQL, LogQL, TraceQL)
- Check user has query permissions in backend service
