import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, SCHOOL_ID as DEFAULT_SCHOOL_ID, assertSafeLoadTarget } from '../config.js';

// Custom metrics
const twoFaSuccessRate = new Rate('2fa_success_rate');
const twoFaLatency = new Trend('2fa_latency');

// Configuration
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up to 10 RPS
    { duration: '3m', target: 50 },   // Ramp up to 50 RPS
    { duration: '5m', target: 50 },    // Stay at 50 RPS
    { duration: '1m', target: 0 },    // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<300', 'p(99)<500'], // 95% of requests under 300ms, 99% under 500ms
    twoFa_success_rate: ['rate>0.95'], // 95% success rate
  },
};

// Test configuration
assertSafeLoadTarget(BASE_URL, 'BASE_URL');

const SCHOOL_ID = __ENV.SCHOOL_ID || DEFAULT_SCHOOL_ID;
const TEST_EMAIL = __ENV.TEST_EMAIL || 'admin@ecole-benani.ma';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || 'admin123';
const TOTP_CODE = __ENV.TOTP_CODE || '123456';

export function setup() {
  // Login to get token
  const loginPayload = JSON.stringify({
    email: TEST_EMAIL,
    password: TEST_PASSWORD,
    school_id: SCHOOL_ID,
  });

  const loginRes = http.post(`${BASE_URL}/auth/login`, loginPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  if (loginRes.status !== 200) {
    console.error(`Setup failed: Login returned ${loginRes.status}`);
    return null;
  }

  const body = JSON.parse(loginRes.body);
  return body.data.access_token;
}

export default function (token) {
  if (!token) {
    console.error('No token available from setup');
    return;
  }

  const payload = JSON.stringify({
    code: TOTP_CODE,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  };

  const start = Date.now();
  const res = http.post(`${BASE_URL}/auth/2fa/verify`, payload, params);
  const duration = Date.now() - start;

  // Record metrics
  twoFaLatency.add(duration);
  twoFaSuccessRate.add(res.status === 200);

  check(res, {
    '2FA verification successful': (r) => r.status === 200,
    'response has success flag': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.success === true;
      } catch (e) {
        return false;
      }
    },
  }) || console.log(`2FA verification failed: ${res.status} - ${res.body}`);

  // Small pause between requests
  sleep(Math.random() * 2);
}
