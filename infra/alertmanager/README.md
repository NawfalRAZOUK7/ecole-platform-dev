# Alertmanager Setup

## Quick Start

1. Create Slack webhooks for three channels: `#ecole-critical`, `#ecole-warnings`, `#ecole-info`
2. Copy `alertmanager.yml` and replace the placeholder webhook URLs
3. Mount the config via Docker volume (already configured in `docker-compose.prod.yml`)

## Testing Alerts

```bash
# Send a test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"info"},"annotations":{"summary":"Test alert from Ecole Platform"}}]'
```

## Alert Rules

Alert rules are defined in `../prometheus/alert_rules.yml` and evaluated by Prometheus.
Alertmanager handles routing, grouping, and notification delivery.
