/// Shared configuration for k6 load tests.
///
/// Reference: Phase 6A — Load testing

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api/v1';
export const SCHOOL_ID = '00000000-0000-4000-8000-000000000001';

export const users = {
  admin: { email: 'admin@ecole-benani.ma', password: 'admin123' },
  teacher: { email: 'prof.math@ecole-benani.ma', password: 'teacher123' },
  parent: { email: 'parent.alaoui@gmail.com', password: 'parent123' },
  student: { email: 'yassine.alaoui@ecole-benani.ma', password: 'student123' },
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
