import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, SCHOOL_ID as DEFAULT_SCHOOL_ID, assertSafeLoadTarget, selectProfile } from '../config.js';

// Custom metrics
const recoveryRequestRate = new Rate('recovery_request_rate');
const recoveryRequestLatency = new Trend('recovery_request_latency');
const recoveryVerifyRate = new Rate('recovery_verify_rate');
const recoveryVerifyLatency = new Trend('recovery_verify_latency');

// Configuration
export const options = {
  stages: selectProfile(
    [
      { duration: '5s', target: 1 },
      { duration: '10s', target: 2 },
      { duration: '5s', target: 0 },
    ],
    [
      { duration: '1m', target: 5 },    // Ramp up to 5 RPS
      { duration: '3m', target: 20 },   // Ramp up to 20 RPS
      { duration: '5m', target: 20 },   // Stay at 20 RPS
      { duration: '1m', target: 0 },    // Ramp down to 0
    ],
  ),
  thresholds: selectProfile(
    {
      http_req_duration: ['p(95)<10000', 'p(99)<20000'],
      recovery_request_rate: ['rate>0.95'],
      recovery_verify_rate: ['rate>0.95'],
    },
    {
      http_req_duration: ['p(95)<400', 'p(99)<800'], // 95% of requests under 400ms, 99% under 800ms
      recovery_request_rate: ['rate>0.95'], // 95% success rate
      recovery_verify_rate: ['rate>0.95'], // 95% success rate
    },
  ),
};

// Test configuration
assertSafeLoadTarget(BASE_URL, 'BASE_URL');

const SCHOOL_ID = __ENV.SCHOOL_ID || DEFAULT_SCHOOL_ID;
const TEST_EMAIL = __ENV.TEST_EMAIL || 'admin@ecole-benani.ma';

// In dev mode, OTP is returned in response
let lastOtp = null;
let lastRequestId = null;

export default function () {
  // Step 1: Request password reset
  const requestPayload = JSON.stringify({
    email: TEST_EMAIL,
    school_id: SCHOOL_ID,
  });

  const start = Date.now();
  const requestRes = http.post(`${BASE_URL}/recovery/request`, requestPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  const requestDuration = Date.now() - start;

  // Record metrics
  recoveryRequestLatency.add(requestDuration);
  recoveryRequestRate.add(requestRes.status === 200);

  check(requestRes, {
    'recovery request successful': (r) => r.status === 200,
    'response has request_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        const hasRequestId = body.data && body.data.request_id;
        if (hasRequestId) {
          lastRequestId = body.data.request_id;
          // In dev mode, OTP is returned in response
          if (body.data.otp) {
            lastOtp = body.data.otp;
          }
        }
        return hasRequestId;
      } catch (e) {
        return false;
      }
    },
  }) || console.log(`Recovery request failed: ${requestRes.status} - ${requestRes.body}`);

  // Step 2: Verify OTP (if we have request_id and otp)
  if (lastRequestId && lastOtp) {
    sleep(0.5); // Small delay between request and verify

    const verifyPayload = JSON.stringify({
      request_id: lastRequestId,
      otp: lastOtp,
    });

    const verifyStart = Date.now();
    const verifyRes = http.post(`${BASE_URL}/recovery/verify`, verifyPayload, {
      headers: { 'Content-Type': 'application/json' },
    });
    const verifyDuration = Date.now() - verifyStart;

    // Record metrics
    recoveryVerifyLatency.add(verifyDuration);
    recoveryVerifyRate.add(verifyRes.status === 200);

    check(verifyRes, {
      'OTP verification successful': (r) => r.status === 200,
      'response has success message': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.data && body.data.message;
        } catch (e) {
          return false;
        }
      },
    }) || console.log(`OTP verification failed: ${verifyRes.status} - ${verifyRes.body}`);
  }

  // Pause between iterations
  sleep(Math.random() * 3);
}
