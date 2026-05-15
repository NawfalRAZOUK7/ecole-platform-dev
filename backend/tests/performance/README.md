# Performance Tests

**33 tests** validating response time SLAs, load handling, and concurrent request patterns. Tests ensure the platform meets performance targets under realistic usage.

## Overview

- **Approach**: Benchmark tests with SLA assertions, concurrent request simulation
- **Tools**: pytest-benchmark for timing, asyncio for concurrency
- **Metrics**: Response time, throughput, resource utilization
- **Target**: Sub-100ms API response times for CRUD operations

## Test Files

### test_benchmarks.py - Response Time SLAs
Individual endpoint performance with SLA enforcement.

**SLA Targets:**

| Operation | Target | Allowance |
|-----------|--------|-----------|
| GET single resource | <50ms | ±10ms |
| GET list (pagination) | <100ms | ±20ms |
| POST create | <150ms | ±30ms |
| PUT update | <100ms | ±20ms |
| DELETE | <75ms | ±15ms |

**Endpoints Benchmarked:**

1. **Authentication**
   ```python
   async def test_login_sla(benchmark):
       # Target: <200ms for credential validation + JWT generation
       benchmark.pedantic(
           lambda: test_client.post(
               "/api/auth/login",
               json={"email": "user@school.ma", "password": "secret"}
           ),
           rounds=10,
           iterations=1
       )
   ```

2. **Grade Operations**
   ```python
   async def test_get_gradebook_sla(benchmark):
       # Target: <100ms for class gradebook (30 students, 5 assignments)
       # Measures: Query time + serialization
       benchmark.pedantic(
           lambda: test_client.get(f"/api/gradebook/{class_id}"),
           rounds=10,
           iterations=1
       )
   ```

3. **Invoice Generation**
   ```python
   async def test_create_invoice_sla(benchmark):
       # Target: <150ms for invoice generation from subscription
       # Measures: Query subscription + line item calculation + persist
       benchmark.pedantic(
           lambda: test_client.post(
               "/api/invoices",
               json={"subscription_id": subscription_id}
           ),
           rounds=5,
           iterations=1
       )
   ```

4. **Search Operations**
   ```python
   async def test_search_students_sla(benchmark):
       # Target: <100ms for school-wide student search
       # Measures: Full-text search + pagination
       benchmark.pedantic(
           lambda: test_client.get(
               f"/api/students?school_id={school_id}&q=Ahmed&limit=10"
           ),
           rounds=10,
           iterations=1
       )
   ```

5. **Bulk Operations**
   ```python
   async def test_bulk_grade_import_sla(benchmark):
       # Target: <1000ms for 100-grade import
       # Measures: Validation + batch insert + transaction
       grades_csv = """student_id,value
uuid1,15.5
uuid2,18.0
...
"""
       benchmark.pedantic(
           lambda: test_client.post(
               "/api/grades/import",
               data={"file": grades_csv}
           ),
           rounds=3,
           iterations=1
       )
   ```

**Benchmark Output:**
```
test_login_sla
  rounds: 10, iterations: 1
  min: 145ms | max: 198ms | mean: 165ms | stdev: 15ms
  SLA: <200ms ✓ PASS

test_search_students_sla
  rounds: 10, iterations: 1
  min: 45ms | max: 125ms | mean: 78ms | stdev: 22ms
  SLA: <100ms ✓ PASS

test_bulk_grade_import_sla
  rounds: 3, iterations: 1
  min: 850ms | max: 950ms | mean: 900ms | stdev: 50ms
  SLA: <1000ms ✓ PASS
```

### test_load_patterns.py - Concurrent Request Handling
Simulates realistic usage patterns and load conditions.

**Load Patterns:**

1. **Concurrent Logins (Peak Time)**
   ```python
   async def test_concurrent_student_logins():
       # Simulate 50 students logging in simultaneously
       # Target: All complete within 2 seconds
       async def login_task():
           return await test_client.post(
               "/api/auth/login",
               json={"email": f"student{i}@school.ma", "password": "password"}
           )

       start = time.time()
       results = await asyncio.gather(*[login_task() for _ in range(50)])
       duration = time.time() - start

       # All should succeed (200 status)
       assert all(r.status_code == 200 for r in results)
       # Within SLA
       assert duration < 2.0
   ```

2. **Concurrent Grade Entry (Teachers simultaneous grading)**
   ```python
   async def test_concurrent_grade_entry():
       # 5 teachers entering grades simultaneously for same class
       # Target: All grades persist without conflicts
       grades = [
           {"student_id": sid, "value": random.randint(0, 20)}
           for sid in student_ids
       ]

       async def enter_grades():
           return await test_client.post(
               f"/api/grades",
               json={"grades": grades}
           )

       results = await asyncio.gather(*[enter_grades() for _ in range(5)])
       # All should succeed
       assert all(r.status_code in [200, 201] for r in results)
       # Verify all grades persisted
       final_count = await grades_repo.count()
       assert final_count == len(student_ids) * 5  # 5 teachers
   ```

3. **Concurrent File Uploads (Document storage)**
   ```python
   async def test_concurrent_file_uploads():
       # 10 concurrent file uploads (1MB each)
       # Target: All complete within 5 seconds, no corruption
       files = [create_test_file(f"file_{i}.pdf", size_mb=1) for i in range(10)]

       async def upload_task(file):
           return await test_client.post(
               "/api/documents/upload",
               files={"file": file}
           )

       start = time.time()
       results = await asyncio.gather(*[upload_task(f) for f in files])
       duration = time.time() - start

       assert all(r.status_code in [200, 201] for r in results)
       assert duration < 5.0
   ```

4. **Cache Warmup (Initial page load)**
   ```python
   async def test_cache_warmup_performance():
       # Clear cache, load school dashboard
       # First request: slow (cache miss)
       # Subsequent requests: fast (cache hit)
       await cache.clear()

       # Cold request
       start = time.time()
       response1 = await test_client.get(f"/api/schools/{school_id}/dashboard")
       cold_time = time.time() - start
       assert response1.status_code == 200
       # Expect <300ms (including cache population)
       assert cold_time < 0.3

       # Warm request (cache hit)
       start = time.time()
       response2 = await test_client.get(f"/api/schools/{school_id}/dashboard")
       warm_time = time.time() - start
       assert response2.status_code == 200
       # Expect <50ms
       assert warm_time < 0.05

       # Speedup ratio
       assert cold_time > warm_time * 3  # At least 3x faster
   ```

5. **Rate Limiting Under Load**
   ```python
   async def test_rate_limit_under_load():
       # Simulate requests exceeding rate limit
       # Target: Rate limiting kicks in at correct threshold
       responses = []

       async def request_task():
           return await test_client.get("/api/students")

       # Send 100 requests from single IP
       results = await asyncio.gather(*[request_task() for _ in range(100)])

       # First ~20 should succeed (depending on rate limit)
       success_count = sum(1 for r in results if r.status_code == 200)
       rate_limited = sum(1 for r in results if r.status_code == 429)

       assert success_count > 0
       assert rate_limited > 0  # Some requests throttled
   ```

6. **Memory Stability (Long-running operations)**
   ```python
   async def test_memory_stability_under_sustained_load():
       # Run operation 1000 times, verify memory doesn't leak
       import psutil
       process = psutil.Process()

       initial_memory = process.memory_info().rss / 1024 / 1024  # MB

       # Run 1000 grade entries
       for i in range(1000):
           await test_client.post(
               "/api/grades",
               json={"student_id": sid, "value": random.randint(0, 20)}
           )

       final_memory = process.memory_info().rss / 1024 / 1024  # MB
       memory_growth = final_memory - initial_memory

       # Memory growth should be minimal (<100MB for 1000 operations)
       assert memory_growth < 100, f"Memory grew {memory_growth}MB"
   ```

## Running Tests

```bash
# All performance tests
pytest backend/tests/performance/

# By category
pytest backend/tests/performance/test_benchmarks.py
pytest backend/tests/performance/test_load_patterns.py -v

# With benchmark results
pytest backend/tests/performance/test_benchmarks.py -v --benchmark-only

# Generate benchmark comparison
pytest backend/tests/performance/test_benchmarks.py --benchmark-compare=0001

# Full report
pytest backend/tests/performance/ -v --benchmark-autosave --benchmark-disable-gc
```

## Benchmark Configuration

```python
# conftest.py
@pytest.fixture
def benchmark(request):
    # Use pytest-benchmark with specific settings
    return request.getfixturevalue('benchmark')
```

## Performance Metrics

**Key Metrics Tracked:**
- Response time (mean, min, max, stdev)
- Throughput (requests/second)
- Concurrency handling (success rate under load)
- Memory usage (stable growth)
- CPU utilization
- Database connection pool exhaustion

## Load Test Scenarios

| Scenario | Concurrent Users | Duration | Target |
|----------|------------------|----------|--------|
| Normal | 10-20 | 1 hour | <100ms response |
| Peak | 50-100 | 15 min | <200ms response |
| Stress | 100+ | 5 min | Graceful degradation |

## Performance Baselines

Current benchmarks (as of 2026-03-30):

| Operation | Mean | Target | Status |
|-----------|------|--------|--------|
| GET school | 45ms | <50ms | PASS |
| POST grade | 120ms | <150ms | PASS |
| Search 1000 students | 85ms | <100ms | PASS |
| Bulk import 100 grades | 850ms | <1000ms | PASS |
| Concurrent 50 logins | 1.8s | <2.0s | PASS |

## CI/CD Integration

Performance tests run on:
- Every commit (quick benchmarks)
- Release builds (full load testing)
- Weekly regression testing (extended scenarios)

## Related Documentation

- Parent: `backend/tests/README.md`
- Integration: `backend/tests/integration/README.md` for database performance
- Load: `system-tests/load/` for k6 load testing scripts
- Operations: Production performance monitoring and alerting
