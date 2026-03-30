# AlertManager Configuration

Prometheus AlertManager routing and notification rules for the Ecole Platform. Handles alert delivery to email and Slack channels with severity-based routing.

## Files

- **alertmanager.yml** - Alert routing rules, receiver configuration, and notification templates

## Purpose

AlertManager receives alerts fired by Prometheus (defined in `../prometheus/alert_rules.yml`) and routes them to appropriate notification channels based on:
- Alert severity (critical, warning, info)
- Alert labels and annotations
- Service or component affected

## Key Receivers

- **Email** - Critical and warning alerts sent to ops team
- **Slack** - Real-time notifications to #alerts channel
- **Escalation** - Critical alerts with on-call page integration (if configured)

## Alert Examples

- Database connection failures
- High API error rates (>5%)
- Memory/CPU threshold breaches
- Certificate expiration warnings
- Backup job failures

## Configuration

AlertManager is deployed as part of the monitoring stack:
```bash
docker-compose -f docker-compose.monitoring.yml up alertmanager
```

## Testing Alerts

Send test alert to AlertManager:
```bash
curl -XPOST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '{
    "alerts": [{
      "status": "firing",
      "labels": {"alertname": "TestAlert", "severity": "warning"},
      "annotations": {"description": "Test alert"}
    }]
  }'
```

## Documentation

See `../DEPLOYMENT.md` for:
- Alert routing customization
- Slack/email integration setup
- Custom receiver configuration
- Notification template customization
