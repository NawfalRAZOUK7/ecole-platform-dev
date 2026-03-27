/// Scenario 2: 500 concurrent GET requests on list endpoints — verify <200ms p95
///
/// Reference: Phase 6A, F2 SLO targets

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, getToken, authHeaders, selectProfile } from './config.js';

const getDuration = new Trend('get_duration', true);
const getFailRate = new Rate('get_failures');

export const options = {
  scenarios: {
    concurrent_gets: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: selectProfile(
        [
          { duration: '5s', target: 10 },
          { duration: '10s', target: 25 },
          { duration: '5s', target: 25 },
          { duration: '5s', target: 0 },
        ],
        [
          { duration: '10s', target: 100 },
          { duration: '20s', target: 500 },
          { duration: '20s', target: 500 },
          { duration: '10s', target: 0 },
        ],
      ),
    },
  },
  thresholds: selectProfile(
    {
      get_duration: ['p(95)<3000'],
      get_failures: ['rate<0.10'],
      http_req_failed: ['rate<0.10'],
    },
    {
      get_duration: ['p(95)<200'],
      get_failures: ['rate<0.05'],
      http_req_failed: ['rate<0.05'],
    },
  ),
};

const endpoints = [
  '/feed',
  '/notifications',
  '/content',
  '/results',
  '/invoices',
];

let token = null;

export function setup() {
  token = getToken(http, 'parent');
  return { token };
}

export default function (data) {
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(`${BASE_URL}${endpoint}`, authHeaders(data.token));

  const success = check(res, {
    'GET status 200': (r) => r.status === 200,
    'has data': (r) => {
      try {
        return r.json().data !== undefined;
      } catch {
        return false;
      }
    },
  });

  getDuration.add(res.timings.duration);
  getFailRate.add(!success);

  sleep(0.2);
}
