/// Scenario 1: 100 concurrent logins — verify <500ms p95
///
/// Reference: Phase 6A, F2 SLO targets

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, SCHOOL_ID, users } from './config.js';

const loginDuration = new Trend('login_duration', true);
const loginFailRate = new Rate('login_failures');

export const options = {
  scenarios: {
    concurrent_logins: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 50 },
        { duration: '20s', target: 100 },
        { duration: '10s', target: 100 },
        { duration: '10s', target: 0 },
      ],
    },
  },
  thresholds: {
    login_duration: ['p(95)<500'],
    login_failures: ['rate<0.05'],
    http_req_failed: ['rate<0.05'],
  },
};

const roles = Object.keys(users);

export default function () {
  const role = roles[Math.floor(Math.random() * roles.length)];
  const cred = users[role];

  const res = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({
      email: cred.email,
      password: cred.password,
      school_id: SCHOOL_ID,
    }),
    { headers: { 'Content-Type': 'application/json' } },
  );

  const success = check(res, {
    'login status 200': (r) => r.status === 200,
    'has access_token': (r) => {
      try {
        return !!r.json().data.access_token;
      } catch {
        return false;
      }
    },
  });

  loginDuration.add(res.timings.duration);
  loginFailRate.add(!success);

  sleep(0.5);
}
