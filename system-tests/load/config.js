/// Shared configuration for k6 load tests.
///
/// Reference: Phase 6A — Load testing

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api/v1';
export const IS_CI = __ENV.CI === 'true' || __ENV.CI === '1';
export const SCHOOL_ID = '00000000-0000-4000-8000-000000000001';
export const STUDENT_ID = '10000000-0000-4000-8000-000000000007';

const LOCAL_DEV_TARGET_RE = /^(https?|wss?):\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]):8000(?:\/|$)/i;

function allowsDirtyDevDb() {
  const value = String(__ENV.K6_ALLOW_DEV_DB || '').toLowerCase();
  return value === '1' || value === 'true' || value === 'yes';
}

export function assertSafeLoadTarget(url, label = 'target') {
  if (LOCAL_DEV_TARGET_RE.test(url) && !allowsDirtyDevDb() && !IS_CI) {
    throw new Error(
      `${label} points at ${url}. Refusing to run k6 against the normal dev DB. ` +
        'Use BASE_URL=http://localhost:8010/api/v1 after make api-test-up, ' +
        'or set K6_ALLOW_DEV_DB=1 for an intentional destructive run.',
    );
  }
}

assertSafeLoadTarget(BASE_URL, 'BASE_URL');

function getSeedPassword(role) {
  const override = __ENV[`${role.toUpperCase()}_PASSWORD`];
  if (override) {
    return override;
  }

  return `${role}123`;
}

export const users = {
  admin: { email: 'admin@ecole-benani.ma', password: getSeedPassword('admin') },
  teacher: { email: 'prof.math@ecole-benani.ma', password: getSeedPassword('teacher') },
  parent: { email: 'parent.alaoui@gmail.com', password: getSeedPassword('parent') },
  student: { email: 'yassine.alaoui@ecole-benani.ma', password: getSeedPassword('student') },
};

/**
 * Authenticate and return an access token.
 */
export function getToken(http, role) {
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

  if (res.status !== 200) {
    console.error(`Login failed for ${role}: ${res.status} ${res.body}`);
    return null;
  }

  return res.json().data.access_token;
}

/**
 * Return standard auth headers.
 */
export function authHeaders(token) {
  return {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
}

/**
 * Return a CI-friendly smoke profile, while preserving the heavier
 * load profile for explicit local/manual performance runs.
 */
export function selectProfile(ciProfile, fullProfile) {
  return IS_CI ? ciProfile : fullProfile;
}
