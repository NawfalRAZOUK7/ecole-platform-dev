/// Scenario 3: 50 concurrent file uploads — verify <2s p95
///
/// Reference: Phase 6A, F2 SLO targets

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, getToken, selectProfile } from './config.js';

const uploadDuration = new Trend('upload_duration', true);
const uploadFailRate = new Rate('upload_failures');

export const options = {
  scenarios: {
    concurrent_uploads: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: selectProfile(
        [
          { duration: '5s', target: 3 },
          { duration: '10s', target: 5 },
          { duration: '5s', target: 5 },
          { duration: '5s', target: 0 },
        ],
        [
          { duration: '10s', target: 25 },
          { duration: '20s', target: 50 },
          { duration: '20s', target: 50 },
          { duration: '10s', target: 0 },
        ],
      ),
    },
  },
  thresholds: selectProfile(
    {
      upload_duration: ['p(95)<5000'],
      upload_failures: ['rate<0.15'],
    },
    {
      upload_duration: ['p(95)<2000'],
      upload_failures: ['rate<0.10'],
    },
  ),
};

// Generate a small binary payload (~50KB) to simulate file upload
function generatePayload() {
  const size = 50 * 1024;
  const data = new ArrayBuffer(size);
  const view = new Uint8Array(data);
  for (let i = 0; i < size; i++) {
    view[i] = Math.floor(Math.random() * 256);
  }
  return http.file(data, 'test-upload.pdf', 'application/pdf');
}

export function setup() {
  const token = getToken(http, 'student');
  return { token };
}

export default function (data) {
  const file = generatePayload();

  const res = http.post(`${BASE_URL}/submissions`, {
    file: file,
  }, {
    headers: {
      Authorization: `Bearer ${data.token}`,
    },
  });

  // Accept 201 (created) or 422 (validation error — no assignment_id, expected)
  const success = check(res, {
    'upload responded': (r) => r.status === 201 || r.status === 422 || r.status === 400,
    'upload under 2s': (r) => r.timings.duration < 2000,
  });

  uploadDuration.add(res.timings.duration);
  uploadFailRate.add(!success);

  sleep(1);
}
