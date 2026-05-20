# NGINX Reverse Proxy Configuration

NGINX reverse proxy configuration for the Ecole Platform. Handles HTTPS termination, load balancing, WAF rules, rate limiting, and security headers.

## Configuration Files

- **nginx.conf** - Development environment configuration
- **nginx-staging.conf** - Staging environment configuration
- **nginx-prod.conf** - Production configuration with WAF, rate limiting, security headers
- **upstream.conf** - Backend upstream definitions with health checks

## Purpose

NGINX serves as:
- **Reverse Proxy** - Routes requests to backend services
- **TLS Terminator** - Handles HTTPS encryption/decryption
- **Load Balancer** - Distributes traffic across backend instances
- **API Gateway** - Rate limiting, request validation, authentication
- **Web Application Firewall** - Lightweight regex-based WAF rules protecting against common attacks
- **Static Content Server** - Serves frontend assets

## Environment Configurations

### Development (nginx.conf)
- HTTP only (no TLS)
- Single backend instance
- Permissive CORS
- Debug logging enabled

### Staging (nginx-staging.conf)
- HTTPS with self-signed certificate
- Single backend instance
- Standard security headers
- Moderate logging

### Production (nginx-prod.conf)
- HTTPS with production certificate
- Load balancing across multiple backend instances
- Lightweight regex-based WAF rules enabled
- Rate limiting per IP and API key
- Comprehensive security headers
- DDoS protection
- Request validation

## Key Features

### Rate Limiting
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
limit_req zone=api burst=20 nodelay;
```

### Security Headers
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### WAF Rules (production)
Lightweight regex-based WAF rules:
- SQL injection prevention
- XSS protection
- Path traversal blocking
- Malicious file upload blocking
- Suspicious header detection

### Health Checks (upstream.conf)
```nginx
upstream backend {
  server backend1:8080 max_fails=3 fail_timeout=30s;
  server backend2:8080 max_fails=3 fail_timeout=30s;
}
```

## Common Operations

### Check Configuration Syntax
```bash
docker-compose exec nginx nginx -t
```

### Reload Configuration
```bash
docker-compose exec nginx nginx -s reload
```

### View Access Logs
```bash
docker-compose logs -f nginx
```

### View Error Logs
```bash
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

## Backend Routes

Standard routes configured:
- `GET  /api/*` → Backend API service
- `POST /api/*` → Backend API service
- `GET  /health` → Health check endpoint
- `GET  /metrics` → Prometheus metrics (auth required)
- `/*` → Frontend SPA

## TLS Certificate Configuration

Production certificates configured via:
```nginx
ssl_certificate /etc/nginx/certs/ecole-platform.crt;
ssl_certificate_key /etc/nginx/certs/ecole-platform.key;
```

See `../certs/README.md` for certificate management.
Automatic renewal via `../scripts/ssl-renew.sh`.

## Performance Optimization

- Gzip compression enabled for text responses
- Connection keep-alive enabled
- Caching headers set appropriately
- Buffer sizes optimized for typical payloads
- Worker process count auto-detected

## Troubleshooting

**502 Bad Gateway:**
- Check backend service health: `../scripts/healthcheck.sh`
- Verify upstream configuration in `upstream.conf`
- Review error logs for connection details

**SSL/TLS errors:**
- Verify certificate files exist: `../certs/`
- Check certificate expiration date
- Renew if needed: `../scripts/ssl-renew.sh`

**Rate limit issues:**
- Adjust `limit_req` zone parameters
- Whitelist trusted IPs if needed
- Monitor rate limit metrics in Prometheus

## Documentation

See `../DEPLOYMENT.md` for:
- Load balancing configuration
- WAF rule customization
- Certificate renewal automation
- Performance tuning
- SSL/TLS hardening
