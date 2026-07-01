/**
 * Smoke test — minimal load to verify the API is alive.
 *
 * Run: k6 run system-tests/load/smoke/healthcheck.js
 */

import http from 'k6/http';
import { check } from 'k6';
import { BASE_URL as API_BASE_URL, assertSafeLoadTarget } from '../config.js';

export const options = {
  vus: 1,
  duration: '10s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = (__ENV.BASE_URL || API_BASE_URL).replace(/\/api\/v1\/?$/, '');
assertSafeLoadTarget(BASE_URL, 'BASE_URL');

export default function () {
  const res = http.get(`${BASE_URL}/api/v1/health`);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
