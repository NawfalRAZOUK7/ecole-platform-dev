/**
 * Stress test — 500 simultaneous logins + first dashboard load.
 *
 * Validates BNF-PERF-02: platform must handle peak morning load.
 *
 * Run: k6 run tests/load/stress/peak_school_morning.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 500 },
    { duration: '2m', target: 500 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.05'],
    'login_duration': ['p(95)<1500'],
    'dashboard_duration': ['p(95)<3000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Simulate login
  const loginPayload = JSON.stringify({
    email: `user_${__VU}@school.ma`,
    password: 'password123',
    school_id: '00000000-0000-0000-0000-000000000001',
  });

  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'login' },
  });

  check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login has token': (r) => r.json('data.access_token') !== '',
  });

  const token = loginRes.json('data.access_token');

  // Load dashboard
  const dashRes = http.get(`${BASE_URL}/api/v1/me`, {
    headers: { Authorization: `Bearer ${token}` },
    tags: { name: 'dashboard' },
  });

  check(dashRes, {
    'dashboard status is 200': (r) => r.status === 200,
  });

  sleep(1);
}
