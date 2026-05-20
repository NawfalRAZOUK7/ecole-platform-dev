# Loki Alerting Rules

Log-based alerting rules for the Ecole Platform. Loki monitors logs and fires alerts based on error patterns, security events, and anomalies.

Domain-specific rules should use backend bounded context names in labels or annotations: `auth`, `user`, `school`, `academic`, `lms`, `billing`, `content`, `communication`, `reports`, `admin`, `sync`, `ai`, and `operations`.

## Files

- **ecole-alerts.yml** - Alert rules for application and infrastructure monitoring

## Alert Types

### Error Detection
- High error rate in API logs (>5% of requests)
- Database connection failures
- Service crash or restart detection
- Uncaught exception patterns

### Security Alerts
- Failed authentication attempts in the `auth` context (multiple retries)
- Unauthorized API access attempts
- Suspicious SQL patterns
- Rate limit threshold breaches

### System Health
- Memory pressure or OOM errors
- Disk full warnings
- Network connectivity issues
- Certificate expiration warnings

### Data Integrity
- Database transaction failures
- Data validation errors
- Duplicate record detection
- Audit log anomalies

## Rule Format

LogQL alerting rules:
```yaml
groups:
  - name: ecole_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({job="ecole-backend"} | json | level="error" [5m]))
          /
          sum(rate({job="ecole-backend"} [5m])) > 0.05
        for: 5m
        annotations:
          summary: "API error rate above 5%"
```

## Rule Evaluation

- Loki continuously evaluates rules against incoming logs
- Rules must fire for duration specified in `for:` clause
- Matching alerts sent to AlertManager for routing
- AlertManager delivers notifications (email, Slack, etc.)

## Critical Alerts

Alerts requiring immediate response:
- Service outages (no logs appearing)
- Database errors and connection failures
- Authentication system failures
- Critical security events
- Data loss or corruption

## Warning Alerts

Alerts for monitoring and investigation:
- Elevated error rates (not critical threshold)
- Slow query detection
- Unusual traffic patterns
- Resource pressure (approaching limits)

## Information Alerts

Low-priority notifications:
- Service restarts/deployments
- Quota usage approaching limits
- Scheduled maintenance notifications

## Testing Rules

To test alert rule logic:
```bash
curl 'http://localhost:3100/loki/api/v1/query?query=<logql>'
```

For example:
```bash
curl 'http://localhost:3100/loki/api/v1/query?query={job="ecole-backend"}%20|%20json%20|%20level=%22error%22'
```

## Modifying Rules

1. Edit `ecole-alerts.yml`
2. Reload Loki configuration:
   ```bash
   docker-compose -f docker-compose.monitoring.yml exec loki curl -X POST http://localhost:3100/loki/config/reload
   ```
3. Verify rules loaded successfully:
   ```bash
   docker-compose logs loki | grep "rule"
   ```
4. Test new rules via LogQL query

## Thresholds

Current thresholds (customize per environment):
- Error rate alert: >5% over 5 minutes
- Failed `auth` alert: >10 failures in 1 minute
- Critical error alert: >20 errors in 1 minute
- Slow query alert: >1s response time

Adjust thresholds in `ecole-alerts.yml` based on SLA requirements.

## Integration with AlertManager

Alerts are fired to AlertManager which routes notifications:
- Critical → Email + Slack + PagerDuty
- Warning → Slack + Email
- Info → Slack only

See `../alertmanager/README.md` for routing configuration.
