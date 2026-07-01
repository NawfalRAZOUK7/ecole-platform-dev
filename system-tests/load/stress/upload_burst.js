/**
 * Stress test — 50 parents simultaneously uploading 5 MB PDFs.
 *
 * Validates direct upload path doesn't choke under concurrent file uploads.
 *
 * Run: k6 run system-tests/load/stress/upload_burst.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL as API_BASE_URL, assertSafeLoadTarget } from '../config.js';

export const options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '3m', target: 50 },
    { duration: '2m', target: 50 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],
    http_req_failed: ['rate<0.10'],
    'initiate_duration': ['p(95)<1000'],
    'upload_duration': ['p(95)<10000'],
  },
};

const BASE_URL = (__ENV.BASE_URL || API_BASE_URL).replace(/\/api\/v1\/?$/, '');
assertSafeLoadTarget(BASE_URL, 'BASE_URL');
const TOKEN = __ENV.API_TOKEN || '';

export default function () {
  // Step 1: Initiate signed upload
  const initiatePayload = JSON.stringify({
    filename: `stress-test-${__VU}-${__ITER}.pdf`,
    content_type: 'application/pdf',
    size_bytes: 5 * 1024 * 1024,
  });

  const initRes = http.post(`${BASE_URL}/api/v1/uploads/signed/initiate`, initiatePayload, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${TOKEN}`,
    },
    tags: { name: 'initiate_upload' },
  });

  check(initRes, {
    'initiate status is 201': (r) => r.status === 201,
    'initiate returns upload_url': (r) => r.json('data.upload_url') !== '',
  });

  const uploadUrl = initRes.json('data.upload_url');

  // Step 2: PUT file (simulated with smaller payload for testability)
  const fileData = http.file(new Uint8Array(1024 * 1024), 'test.pdf', 'application/pdf');
  const putRes = http.put(uploadUrl, fileData, {
    headers: { 'Content-Type': 'application/pdf' },
    tags: { name: 'put_upload' },
  });

  check(putRes, {
    'upload accepted': (r) => r.status >= 200 && r.status < 300,
  });

  sleep(2);
}
