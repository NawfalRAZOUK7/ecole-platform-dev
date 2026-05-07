/**
 * Soak test — 24h steady traffic to detect memory leaks and connection pool exhaustion.
 *
 * Low constant load (10 VUs) over a long duration.
 *
 * Run: k6 run tests/load/soak/24h_steady_traffic.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '5m', target: 10 },
    { duration: '24h', target: 10 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const endpoints = [
    '/api/v1/health',
    '/api/v1/public/schools',
    '/api/v1/content/items',
  ];

  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(`${BASE_URL}${endpoint}`);

  check(res, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
  });

  sleep(Math.random() * 3 + 1);
}
