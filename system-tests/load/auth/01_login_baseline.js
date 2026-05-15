import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, SCHOOL_ID as DEFAULT_SCHOOL_ID, assertSafeLoadTarget } from '../config.js';

// Custom metrics
const loginSuccessRate = new Rate('login_success_rate');
const loginLatency = new Trend('login_latency');

// Configuration
export const options = {
  stages: [
    { duration: '1m', target: 20 },   // Ramp up to 20 RPS
    { duration: '3m', target: 100 },  // Ramp up to 100 RPS
    { duration: '5m', target: 100 },  // Stay at 100 RPS
    { duration: '1m', target: 0 },    // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests under 500ms, 99% under 1s
    login_success_rate: ['rate>0.95'], // 95% success rate
  },
};

// Test configuration
assertSafeLoadTarget(BASE_URL, 'BASE_URL');

const SCHOOL_ID = __ENV.SCHOOL_ID || DEFAULT_SCHOOL_ID;
const TEST_EMAIL = __ENV.TEST_EMAIL || 'admin@ecole-benani.ma';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || 'admin123';

export default function () {
  const payload = JSON.stringify({
    email: TEST_EMAIL,
    password: TEST_PASSWORD,
    school_id: SCHOOL_ID,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const start = Date.now();
  const res = http.post(`${BASE_URL}/auth/login`, payload, params);
  const duration = Date.now() - start;

  // Record metrics
  loginLatency.add(duration);
  loginSuccessRate.add(res.status === 200);

  check(res, {
    'login successful': (r) => r.status === 200,
    'response has access_token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.access_token;
      } catch (e) {
        return false;
      }
    },
  }) || console.log(`Login failed: ${res.status} - ${res.body}`);

  // Small pause between requests to simulate realistic traffic
  sleep(Math.random() * 2);
}
