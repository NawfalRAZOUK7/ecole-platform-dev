/// Scenario 3: 50 concurrent file uploads — verify <2s p95
///
/// Reference: Phase 6A, F2 SLO targets

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, STUDENT_ID, getToken, selectProfile } from './config.js';

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

// Generate a tiny valid PDF-like payload. The document service validates MIME
// from content, so random bytes labelled as PDF are intentionally rejected.
function generatePayload() {
  const pdf = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 0 >>
endobj
trailer
<< /Root 1 0 R >>
%%EOF
% k6 ${__VU}-${__ITER}-${Date.now()}
`;
  return http.file(pdf, `test-upload-${__VU}-${__ITER}.pdf`, 'application/pdf');
}

export function setup() {
  const token = getToken(http, 'admin');
  return { token };
}

export default function (data) {
  const file = generatePayload();

  const res = http.post(
    `${BASE_URL}/documents/upload`,
    {
      category: 'other',
      linked_student_id: STUDENT_ID,
      file: file,
    },
    {
      headers: {
        Authorization: `Bearer ${data.token}`,
      },
    },
  );

  const success = check(res, {
    'upload created document': (r) => r.status === 201,
    'upload under 2s': (r) => r.timings.duration < 2000,
  });

  uploadDuration.add(res.timings.duration);
  uploadFailRate.add(!success);

  sleep(1);
}
