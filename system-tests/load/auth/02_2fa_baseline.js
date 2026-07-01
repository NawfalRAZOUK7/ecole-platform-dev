import http from 'k6/http';
import { check, sleep } from 'k6';
import crypto from 'k6/crypto';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, SCHOOL_ID as DEFAULT_SCHOOL_ID, assertSafeLoadTarget, selectProfile } from '../config.js';

// Custom metrics
const twoFaSuccessRate = new Rate('two_fa_success_rate');
const twoFaLatency = new Trend('two_fa_latency');

// Configuration
export const options = {
  stages: selectProfile(
    [
      { duration: '5s', target: 1 },
      { duration: '10s', target: 3 },
      { duration: '5s', target: 0 },
    ],
    [
      { duration: '1m', target: 10 },   // Ramp up to 10 RPS
      { duration: '3m', target: 50 },   // Ramp up to 50 RPS
      { duration: '5m', target: 50 },    // Stay at 50 RPS
      { duration: '1m', target: 0 },    // Ramp down to 0
    ],
  ),
  thresholds: selectProfile(
    {
      http_req_duration: ['p(95)<10000', 'p(99)<20000'],
      two_fa_success_rate: ['rate>0.95'],
    },
    {
      http_req_duration: ['p(95)<300', 'p(99)<500'], // 95% of requests under 300ms, 99% under 500ms
      two_fa_success_rate: ['rate>0.95'], // 95% success rate
    },
  ),
};

// Test configuration
assertSafeLoadTarget(BASE_URL, 'BASE_URL');

const SCHOOL_ID = __ENV.SCHOOL_ID || DEFAULT_SCHOOL_ID;
const TEST_EMAIL = __ENV.TEST_EMAIL || 'admin@ecole-benani.ma';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || 'admin123';

const BASE32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

function bytesToBinaryString(bytes) {
  return String.fromCharCode(...bytes);
}

function base32ToBytes(secret) {
  let bits = '';
  const cleanSecret = secret.toUpperCase().replace(/=+$/g, '');

  for (const char of cleanSecret) {
    const value = BASE32_ALPHABET.indexOf(char);
    if (value === -1) {
      throw new Error(`Invalid base32 character in TOTP secret: ${char}`);
    }
    bits += value.toString(2).padStart(5, '0');
  }

  const bytes = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) {
    bytes.push(parseInt(bits.slice(i, i + 8), 2));
  }
  return bytes;
}

function counterToBytes(counter) {
  const bytes = new Array(8).fill(0);
  let value = counter;
  for (let i = 7; i >= 0; i -= 1) {
    bytes[i] = value & 0xff;
    value = Math.floor(value / 256);
  }
  return bytes;
}

function generateTotp(secret, timestamp = Date.now()) {
  const key = bytesToBinaryString(base32ToBytes(secret));
  const counter = Math.floor(timestamp / 1000 / 30);
  const message = bytesToBinaryString(counterToBytes(counter));
  const digest = crypto.hmac('sha1', key, message, 'hex');
  const hmac = [];

  for (let i = 0; i < digest.length; i += 2) {
    hmac.push(parseInt(digest.slice(i, i + 2), 16));
  }

  const offset = hmac[hmac.length - 1] & 0x0f;
  const binary = ((hmac[offset] & 0x7f) * (2 ** 24))
    + ((hmac[offset + 1] & 0xff) << 16)
    + ((hmac[offset + 2] & 0xff) << 8)
    + (hmac[offset + 3] & 0xff);

  return String(binary % 1000000).padStart(6, '0');
}

export function setup() {
  const loginPayload = JSON.stringify({
    email: TEST_EMAIL,
    password: TEST_PASSWORD,
    school_id: SCHOOL_ID,
  });

  const loginRes = http.post(`${BASE_URL}/auth/login`, loginPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  if (loginRes.status !== 200) {
    console.error(`Setup failed: Login returned ${loginRes.status}`);
    return null;
  }

  const loginBody = JSON.parse(loginRes.body);
  const accessToken = loginBody.data && loginBody.data.access_token;
  if (!accessToken) {
    console.error('Setup failed: Login did not return an access token');
    return null;
  }

  const authParams = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
  };
  const setupRes = http.post(`${BASE_URL}/auth/2fa/setup`, null, authParams);

  if (setupRes.status !== 200) {
    console.error(`Setup failed: 2FA setup returned ${setupRes.status} ${setupRes.body}`);
    return null;
  }

  const setupBody = JSON.parse(setupRes.body);
  const secret = setupBody.data && setupBody.data.secret;
  if (!secret) {
    console.error('Setup failed: 2FA setup did not return a secret');
    return null;
  }

  const verifySetupRes = http.post(
    `${BASE_URL}/auth/2fa/verify-setup`,
    JSON.stringify({ code: generateTotp(secret) }),
    authParams,
  );

  if (verifySetupRes.status !== 200) {
    console.error(`Setup failed: 2FA verify-setup returned ${verifySetupRes.status} ${verifySetupRes.body}`);
    return null;
  }

  return { secret };
}

export default function (data) {
  if (!data || !data.secret) {
    console.error('No TOTP secret available from setup');
    return;
  }

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  const loginPayload = JSON.stringify({
    email: TEST_EMAIL,
    password: TEST_PASSWORD,
    school_id: SCHOOL_ID,
  });
  const loginRes = http.post(`${BASE_URL}/auth/login`, loginPayload, params);

  let tempToken = null;
  try {
    const loginBody = JSON.parse(loginRes.body);
    tempToken = loginBody.data && loginBody.data.temp_token;
  } catch (e) {
    // The check below records the failure with the response body.
  }

  const start = Date.now();
  const res = tempToken
    ? http.post(
      `${BASE_URL}/auth/2fa/verify`,
      JSON.stringify({ temp_token: tempToken, code: generateTotp(data.secret) }),
      params,
    )
    : loginRes;
  const duration = Date.now() - start;

  // Record metrics
  twoFaLatency.add(duration);
  twoFaSuccessRate.add(res.status === 200);

  check(res, {
    '2FA verification successful': (r) => r.status === 200,
    'response has success flag': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.success === true;
      } catch (e) {
        return false;
      }
    },
  }) || console.log(`2FA verification failed: ${res.status} - ${res.body}`);

  // Small pause between requests
  sleep(Math.random() * 2);
}

export function teardown(data) {
  if (!data || !data.secret) {
    return;
  }

  const headers = { 'Content-Type': 'application/json' };
  const loginPayload = JSON.stringify({
    email: TEST_EMAIL,
    password: TEST_PASSWORD,
    school_id: SCHOOL_ID,
  });
  const loginRes = http.post(`${BASE_URL}/auth/login`, loginPayload, { headers });

  if (loginRes.status !== 200) {
    console.error(`Teardown skipped: Login returned ${loginRes.status}`);
    return;
  }

  const loginBody = JSON.parse(loginRes.body);
  const tempToken = loginBody.data && loginBody.data.temp_token;
  if (!tempToken) {
    console.error('Teardown skipped: Login did not return a temp token');
    return;
  }

  const verifyRes = http.post(
    `${BASE_URL}/auth/2fa/verify`,
    JSON.stringify({ temp_token: tempToken, code: generateTotp(data.secret) }),
    { headers },
  );

  if (verifyRes.status !== 200) {
    console.error(`Teardown skipped: 2FA verify returned ${verifyRes.status}`);
    return;
  }

  const verifyBody = JSON.parse(verifyRes.body);
  const accessToken = verifyBody.data && verifyBody.data.access_token;
  if (!accessToken) {
    console.error('Teardown skipped: 2FA verify did not return an access token');
    return;
  }

  http.post(
    `${BASE_URL}/auth/2fa/disable`,
    JSON.stringify({ code: generateTotp(data.secret) }),
    { headers: { ...headers, Authorization: `Bearer ${accessToken}` } },
  );
}
