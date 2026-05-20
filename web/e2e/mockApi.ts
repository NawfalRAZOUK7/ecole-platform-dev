import type { Page, Route } from '@playwright/test';
import { SCHOOL_ID } from './helpers';

export type MockRole = 'admin' | 'teacher' | 'parent' | 'student' | 'director' | 'content_manager';

export interface MockUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  school_id: string;
  totp_enabled?: boolean;
  permissions: string[];
  memberships: Array<{
    school_id: string;
    role: string;
    status: string;
  }>;
}

const META = {
  timestamp: '2026-04-06T10:00:00.000Z',
  version: '0.1.0',
} as const;

const SESSION_COOKIE = 'csrf_token=mock-csrf; Path=/; SameSite=Lax';

const USERS: Record<MockRole, MockUser> = {
  admin: {
    id: 'admin-1',
    email: 'admin@ecole-benani.ma',
    full_name: 'Admin Benani',
    role: 'ADM',
    school_id: SCHOOL_ID,
    permissions: ['*'],
    memberships: [{ school_id: SCHOOL_ID, role: 'ADM', status: 'active' }],
  },
  teacher: {
    id: 'teacher-1',
    email: 'prof.math@ecole-benani.ma',
    full_name: 'Professeur Math',
    role: 'TCH',
    school_id: SCHOOL_ID,
    permissions: ['attendance.write', 'gradebook.write'],
    memberships: [{ school_id: SCHOOL_ID, role: 'TCH', status: 'active' }],
  },
  parent: {
    id: 'parent-1',
    email: 'parent.alaoui@gmail.com',
    full_name: 'Parent Alaoui',
    role: 'PAR',
    school_id: SCHOOL_ID,
    permissions: ['invoices.read'],
    memberships: [{ school_id: SCHOOL_ID, role: 'PAR', status: 'active' }],
  },
  student: {
    id: 'student-1',
    email: 'yassine.alaoui@ecole-benani.ma',
    full_name: 'Yassine Alaoui',
    role: 'STD',
    school_id: SCHOOL_ID,
    permissions: ['gradebook.read'],
    memberships: [{ school_id: SCHOOL_ID, role: 'STD', status: 'active' }],
  },
  director: {
    id: 'director-1',
    email: 'director@ecole-benani.ma',
    full_name: 'Directrice Benani',
    role: 'DIR',
    school_id: SCHOOL_ID,
    permissions: ['budgets.review'],
    memberships: [{ school_id: SCHOOL_ID, role: 'DIR', status: 'active' }],
  },
  content_manager: {
    id: 'content-manager-1',
    email: 'cms.manager@ecole-benani.ma',
    full_name: 'Gestionnaire CMS',
    role: 'CONTENT_MGR',
    school_id: SCHOOL_ID,
    permissions: ['cms.content.write', 'cms.content.review'],
    memberships: [{ school_id: SCHOOL_ID, role: 'CONTENT_MGR', status: 'active' }],
  },
};

const ROLE_BY_EMAIL: Record<string, MockRole> = Object.fromEntries(
  Object.entries(USERS).map(([role, user]) => [user.email, role as MockRole]),
);

export function apiResponse<T>(data: T) {
  return {
    data,
    meta: META,
  };
}

export function apiListResponse<T>(data: T[]) {
  return {
    data,
    meta: {
      ...META,
      next_cursor: null,
      has_more: false,
    },
  };
}

async function fulfillJson(
  route: Route,
  body: unknown,
  options: {
    status?: number;
    headers?: Record<string, string>;
  } = {},
) {
  await route.fulfill({
    status: options.status ?? 200,
    contentType: 'application/json',
    headers: options.headers,
    body: JSON.stringify(body),
  });
}

function getRoleFromLoginEmail(email: string | undefined, fallbackRole: MockRole) {
  return ROLE_BY_EMAIL[email ?? ''] ?? fallbackRole;
}

export async function installMockSession(page: Page, initialRole: MockRole = 'parent') {
  let currentRole = initialRole;
  let isLoggedIn = false;

  await page.route(/\/api\/v1\/auth\/login$/, async (route) => {
    const payload = route.request().postDataJSON() as
      | { email?: string; school_id?: string }
      | undefined;
    currentRole = getRoleFromLoginEmail(payload?.email, currentRole);
    isLoggedIn = true;

    await fulfillJson(
      route,
      apiResponse({
        access_token: `mock-${currentRole}-token`,
        token_type: 'bearer',
        expires_in: 3600,
      }),
      {
        headers: {
          'set-cookie': SESSION_COOKIE,
        },
      },
    );
  });

  await page.route(/\/api\/v1\/auth\/me$/, async (route) => {
    if (!isLoggedIn) {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' }),
      });
      return;
    }
    await fulfillJson(route, apiResponse(USERS[currentRole]));
  });

  await page.route(/\/api\/v1\/auth\/refresh$/, async (route) => {
    if (!isLoggedIn) {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' }),
      });
      return;
    }
    await fulfillJson(
      route,
      apiResponse({
        access_token: `mock-${currentRole}-refresh-token`,
        token_type: 'bearer',
        expires_in: 3600,
      }),
      {
        headers: {
          'set-cookie': SESSION_COOKIE,
        },
      },
    );
  });

  await page.route(/\/api\/v1\/auth\/logout$/, async (route) => {
    isLoggedIn = false;
    await fulfillJson(route, apiResponse({ success: true }));
  });

  await page.route(/\/api\/v1\/notifications\/unread-count$/, async (route) => {
    await fulfillJson(route, apiResponse({ unread_count: 0 }));
  });

  await page.route(/\/api\/v1\/notifications(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiListResponse([]));
  });

  await page.route(/\/api\/v1\/feed(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiListResponse([]));
  });

  await page.route(/\/api\/v1\/sync\/devices(?:\?.*)?$/, async (route) => {
    await fulfillJson(
      route,
      apiListResponse([{ id: 'device-1', name: 'Browser', is_active: true }]),
    );
  });

  await page.route(/\/api\/v1\/sync\/status(?:\?.*)?$/, async (route) => {
    await fulfillJson(
      route,
      apiResponse({
        device_id: 'device-1',
        last_push_at: '2026-04-06T09:00:00.000Z',
        last_pull_at: '2026-04-06T09:05:00.000Z',
        pending_push_count: 0,
        pending_pull_count: 0,
      }),
    );
  });

  await page.route(/\/api\/v1\/sync\/health(?:\?.*)?$/, async (route) => {
    await fulfillJson(
      route,
      apiResponse({
        device_id: 'device-1',
        is_healthy: true,
        last_success_at: '2026-04-06T09:05:00.000Z',
        error_count: 0,
      }),
    );
  });

  await page.route(/\/api\/v1\/content-items(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiListResponse([]));
  });

  await page.route(/\/api\/v1\/teacher\/classes(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiResponse([]));
  });

  await page.route(/\/api\/v1\/teacher\/periods(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiResponse([]));
  });

  await page.route(/\/api\/v1\/me\/profile(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiResponse(USERS[currentRole]));
  });

  await page.route(/\/api\/v1\/me\/children(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiListResponse([]));
  });

  await page.route(/\/api\/v1\/rewards\/me(?:\?.*)?$/, async (route) => {
    await fulfillJson(
      route,
      apiResponse({
        xp: 0,
        level: 1,
        current_streak: 0,
        longest_streak: 0,
        last_activity_at: null,
      }),
    );
  });

  await page.route(/\/api\/v1\/lms\/levels\/mappings(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiListResponse([]));
  });

  await page.route(/\/api\/v1\/admin\/dashboard(?:\?.*)?$/, async (route) => {
    await fulfillJson(
      route,
      apiResponse({
        user_count: 0,
        student_count: 0,
        teacher_count: 0,
        pending_invitations: 0,
      }),
    );
  });

  await page.route(/\/api\/v1\/programs(?:\?.*)?$/, async (route) => {
    await fulfillJson(route, apiListResponse([]));
  });

  return {
    getCurrentUser: () => USERS[currentRole],
    getUser: (role: MockRole) => USERS[role],
    setCurrentRole: (role: MockRole) => {
      currentRole = role;
    },
  };
}
