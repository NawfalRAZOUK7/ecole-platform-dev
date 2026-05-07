/// Scenario 1: 100 concurrent logins — verify <500ms p95
///
/// Reference: Phase 6A, F2 SLO targets

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, IS_CI, SCHOOL_ID, selectProfile, users } from './config.js';

const loginDuration = new Trend('login_duration', true);
const loginFailRate = new Rate('login_failures');

export const options = {
  scenarios: {
    concurrent_logins: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: selectProfile(
        [
          { duration: '5s', target: 5 },
          { duration: '10s', target: 10 },
          { duration: '5s', target: 10 },
          { duration: '5s', target: 0 },
        ],
        [
          { duration: '10s', target: 50 },
          { duration: '20s', target: 100 },
          { duration: '10s', target: 100 },
          { duration: '10s', target: 0 },
        ],
      ),
    },
  },
  thresholds: selectProfile(
    {
      login_duration: ['p(95)<5000'],
      login_failures: ['rate<0.10'],
      http_req_failed: ['rate<0.30'],
    },
    {
      login_duration: ['p(95)<500'],
      login_failures: ['rate<0.05'],
      http_req_failed: ['rate<0.05'],
    },
  ),
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

  const acceptsRateLimit = IS_CI;
  const success = check(res, {
    'login responded as expected': (r) => r.status === 200 || (acceptsRateLimit && r.status === 429),
    'has access_token or rate_limit': (r) => {
      if (acceptsRateLimit && r.status === 429) {
        return true;
      }
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
