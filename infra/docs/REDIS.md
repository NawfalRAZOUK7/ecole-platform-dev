# Redis Caching

Redis in-memory cache configuration for the Ecole Platform. Provides session storage, distributed caching, and real-time features.

## Files

- **redis.conf** - Redis server configuration

## Purpose

Redis serves as:
- **Session Store** - HTTP session persistence across container restarts
- **Cache Layer** - In-memory caching for database queries and API responses
- **Rate Limiter** - Token bucket rate limiting for API endpoints
- **Real-Time Features** - Pub/sub for notifications and real-time updates
- **Queue Backend** - Job queue for async tasks (if using Celery/RQ)
- **Lock Manager** - Distributed locks for critical sections

## Configuration Highlights

From `redis.conf`:

### Memory Management
- **maxmemory** - Maximum memory allocation (default: 256MB for dev, adjust for production)
- **maxmemory-policy** - Eviction policy when memory limit reached
  - Default: `allkeys-lru` (evict least-recently-used keys)
  - Alternatives: `volatile-lru`, `allkeys-random`, `volatile-random`

### Persistence
- **save** - RDB snapshots (periodic backups to disk)
  - Default: Save after 900s if 1 key changed, 300s if 10 keys, 60s if 10000 keys
- **appendonly** - AOF (append-only file) for durability
  - Default: Disabled for performance
  - Enable for critical data that must survive restarts

### Performance
- **tcp-backlog** - Connection queue size
- **timeout** - Client idle timeout (0 = no timeout)
- **databases** - Number of logical databases (0-15)

### Replication (if configured)
- **slave-read-only** - Replicas are read-only
- **repl-diskless-sync** - Stream RDB directly to slaves

## Common Operations

### Connect to Redis CLI
```bash
docker-compose exec redis redis-cli
```

### Monitor Real-Time Commands
```bash
redis-cli monitor
```

### Check Memory Usage
```bash
redis-cli info memory
```

### Flush All Data (DANGEROUS!)
```bash
redis-cli FLUSHALL
```

### Get All Keys (development only)
```bash
redis-cli KEYS '*'
```

### Estimate Key Size
```bash
redis-cli DEBUG OBJECT key_name
```

## Use Cases in Ecole Platform

### User Sessions
```
Key: session:{session_id}
Value: {user_id, role, permissions, created_at}
TTL: 24 hours
```

### API Response Cache
```
Key: cache:api:endpoint:{params_hash}
Value: JSON response
TTL: 5-30 minutes depending on endpoint
```

### Rate Limiting
```
Key: rate_limit:{user_id}:{endpoint}
Value: request_count
TTL: 60 seconds
```

### Student Progress Cache
```
Key: progress:student:{student_id}
Value: {completed_courses, grades, achievements}
TTL: 5 minutes
```

## Scalability Considerations

### Single Redis Instance (Development)
- Suitable for testing and small deployments
- No replication or failover
- Memory limits the data size

### Redis Cluster (Production)
- Multiple nodes with automatic sharding
- High availability with replicas
- Horizontal scaling for large datasets
- Requires cluster-aware client

### Redis Sentinel (High Availability)
- Master-slave replication
- Automatic failover on master loss
- Monitoring and recovery
- Simpler than cluster mode

See `../DEPLOYMENT.md` for cluster and sentinel configuration.

## Monitoring

Monitor Redis via:
- Prometheus redis_exporter metrics
- Redis INFO command stats
- Grafana dashboard: `db-redis-health.json`

Key metrics:
- Memory usage vs. limit
- Eviction rate
- Hit/miss ratios
- Connection count
- Command latency

## Backup and Recovery

Redis persistence configured in `redis.conf`:

### RDB Snapshots
- Periodic point-in-time backups to disk
- Good for full data recovery
- Can be slow during large datasets
- Enable with `save` directives

### AOF (Append-Only File)
- Logs every write operation
- Better durability guarantees
- Larger file size than RDB
- Enable with `appendonly yes`

Backup procedures:
```bash
redis-cli BGSAVE          # Background snapshot
redis-cli BGREWRITEAOF    # Optimize AOF file
```

See `../backup/README.md` for backup integration.

## Security

Production recommendations:
- Require authentication: Set password in redis.conf
- Bind to internal network only: `bind 127.0.0.1` or use Docker networks
- Use ACLs (Redis 6+) for fine-grained permissions
- Encrypt traffic with TLS wrapper (Redis 6+)
- Monitor for suspicious commands via logs
- Implement rate limiting at application level

## Troubleshooting

**Redis running out of memory:**
- Check eviction policy: `redis-cli CONFIG GET maxmemory-policy`
- Increase maxmemory if appropriate
- Audit what data is stored
- Implement TTLs on keys
- Use SCAN instead of KEYS for enumeration

**High eviction rate:**
- Indicates insufficient memory
- Increase memory allocation
- Implement application-level cache invalidation
- Review TTL configuration

**Replication lag (if clustered):**
- Check network connectivity between nodes
- Verify replication backlog size
- Monitor slave-served-stale-data setting
- Review master command processing performance
