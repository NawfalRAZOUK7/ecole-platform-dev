/**
 * Tests for shared utilities:
 * - shared/validation/schemas.ts
 * - shared/constants/roles.ts
 * - shared/lib/levels.ts
 * - shared/types/index.ts (import test)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ---------------------------------------------------------------------------
// Validation schemas
// ---------------------------------------------------------------------------

describe('validation schemas', () => {
  it('emailSchema accepts valid emails', async () => {
    const { emailSchema } = await import('@/shared/validation/schemas');
    expect(emailSchema.safeParse('user@example.com').success).toBe(true);
    expect(emailSchema.safeParse('teacher@ecole.ma').success).toBe(true);
  });

  it('emailSchema rejects invalid emails', async () => {
    const { emailSchema } = await import('@/shared/validation/schemas');
    expect(emailSchema.safeParse('not-an-email').success).toBe(false);
    expect(emailSchema.safeParse('').success).toBe(false);
  });

  it('phoneSchema accepts valid phone numbers', async () => {
    const { phoneSchema } = await import('@/shared/validation/schemas');
    expect(phoneSchema.safeParse('+212600000000').success).toBe(true);
    expect(phoneSchema.safeParse('0600000000').success).toBe(true);
  });

  it('phoneSchema rejects invalid phones', async () => {
    const { phoneSchema } = await import('@/shared/validation/schemas');
    expect(phoneSchema.safeParse('abc').success).toBe(false);
    expect(phoneSchema.safeParse('12').success).toBe(false);
  });

  it('gradeSchema accepts valid grades 0-20', async () => {
    const { gradeSchema } = await import('@/shared/validation/schemas');
    expect(gradeSchema.safeParse(0).success).toBe(true);
    expect(gradeSchema.safeParse(20).success).toBe(true);
    expect(gradeSchema.safeParse(14.5).success).toBe(true);
  });

  it('gradeSchema rejects out-of-range grades', async () => {
    const { gradeSchema } = await import('@/shared/validation/schemas');
    expect(gradeSchema.safeParse(-1).success).toBe(false);
    expect(gradeSchema.safeParse(21).success).toBe(false);
  });

  it('currencySchema accepts valid amounts', async () => {
    const { currencySchema } = await import('@/shared/validation/schemas');
    expect(currencySchema.safeParse(100).success).toBe(true);
    expect(currencySchema.safeParse(0).success).toBe(true);
    expect(currencySchema.safeParse(99.99).success).toBe(true);
  });

  it('currencySchema rejects negative amounts', async () => {
    const { currencySchema } = await import('@/shared/validation/schemas');
    expect(currencySchema.safeParse(-1).success).toBe(false);
  });

  it('requiredString accepts non-empty strings', async () => {
    const { requiredString } = await import('@/shared/validation/schemas');
    expect(requiredString.safeParse('hello').success).toBe(true);
  });

  it('requiredString rejects empty strings', async () => {
    const { requiredString } = await import('@/shared/validation/schemas');
    expect(requiredString.safeParse('').success).toBe(false);
  });

  it('paginationSchema validates correctly', async () => {
    const { paginationSchema } = await import('@/shared/validation/schemas');
    expect(paginationSchema.safeParse({ page: 1, pageSize: 10 }).success).toBe(true);
    expect(paginationSchema.safeParse({ page: 0, pageSize: 10 }).success).toBe(false);
    expect(paginationSchema.safeParse({ page: 1, pageSize: 101 }).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Role constants
// ---------------------------------------------------------------------------

describe('role constants', () => {
  it('ROLE_CODES contains expected roles', async () => {
    const { ROLE_CODES } = await import('@/shared/constants/roles');
    expect(ROLE_CODES).toContain('ADM');
    expect(ROLE_CODES).toContain('TCH');
    expect(ROLE_CODES).toContain('STD');
    expect(ROLE_CODES).toContain('PAR');
    expect(ROLE_CODES).toContain('DIR');
  });

  it('ADMIN_ROLES contains only ADM', async () => {
    const { ADMIN_ROLES } = await import('@/shared/constants/roles');
    expect(ADMIN_ROLES).toEqual(['ADM']);
  });

  it('MANAGEMENT_ROLES contains ADM and DIR', async () => {
    const { MANAGEMENT_ROLES } = await import('@/shared/constants/roles');
    expect(MANAGEMENT_ROLES).toContain('ADM');
    expect(MANAGEMENT_ROLES).toContain('DIR');
    expect(MANAGEMENT_ROLES).toHaveLength(2);
  });

  it('STAFF_ROLES contains ADM, DIR, TCH', async () => {
    const { STAFF_ROLES } = await import('@/shared/constants/roles');
    expect(STAFF_ROLES).toContain('ADM');
    expect(STAFF_ROLES).toContain('DIR');
    expect(STAFF_ROLES).toContain('TCH');
    expect(STAFF_ROLES).toHaveLength(3);
  });

  it('ALL_ROLES contains all 5 roles', async () => {
    const { ALL_ROLES } = await import('@/shared/constants/roles');
    expect(ALL_ROLES).toHaveLength(5);
  });
});

// ---------------------------------------------------------------------------
// Levels library
// ---------------------------------------------------------------------------

describe('levels library', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({
          data: [
            {
              level: 'ps',
              min_age_months: 36,
              max_age_months: 48,
              default_age_min: 3,
              default_age_max: 4,
              display_label: 'PS',
            },
            {
              level: 'ms',
              min_age_months: 48,
              max_age_months: 60,
              default_age_min: 4,
              default_age_max: 5,
              display_label: 'MS',
            },
          ],
          meta: { timestamp: '', version: '' },
        }),
      }),
    );
    vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid' });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('fetchLevelMappings returns level mappings from API', async () => {
    const { fetchLevelMappings } = await import('@/shared/lib/levels');
    const mappings = await fetchLevelMappings();
    expect(mappings).toHaveLength(2);
    expect(mappings[0].level).toBe('ps');
    expect(mappings[0].display_label).toBe('PS');
  });

  it('fetchLevelMappings fills in default ages from months when missing', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({
          data: [
            {
              level: 'gs',
              min_age_months: 60,
              max_age_months: 72,
              default_age_min: null,
              default_age_max: null,
              display_label: 'GS',
            },
          ],
          meta: { timestamp: '', version: '' },
        }),
      }),
    );
    const { fetchLevelMappings } = await import('@/shared/lib/levels');
    const mappings = await fetchLevelMappings();
    // default_age_min computed from min_age_months / 12 (floor)
    expect(mappings[0].default_age_min).toBe(5); // floor(60/12) = 5
    expect(mappings[0].default_age_max).toBe(6); // ceil(72/12) = 6
  });

  it('buildLevelMap creates a record keyed by level', async () => {
    const { buildLevelMap } = await import('@/shared/lib/levels');
    const mappings = [
      {
        level: 'ps',
        min_age_months: 36,
        max_age_months: 48,
        default_age_min: 3,
        default_age_max: 4,
        display_label: 'PS',
      },
      {
        level: 'ms',
        min_age_months: 48,
        max_age_months: 60,
        default_age_min: 4,
        default_age_max: 5,
        display_label: 'MS',
      },
    ];
    const map = buildLevelMap(mappings);
    expect(map['ps'].display_label).toBe('PS');
    expect(map['ms'].display_label).toBe('MS');
    expect(Object.keys(map)).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// App routes
// ---------------------------------------------------------------------------

describe('routes', () => {
  it('ROUTES contains expected keys', async () => {
    const { ROUTES } = await import('@/app/routes');
    expect(ROUTES.LOGIN).toBe('/login');
    expect(ROUTES.DASHBOARD).toBe('/dashboard');
    expect(ROUTES.ADMIN).toBe('/admin');
    expect(ROUTES.ATTENDANCE).toBe('/attendance');
    expect(ROUTES.GRADEBOOK).toBe('/gradebook');
  });
});

// ---------------------------------------------------------------------------
// ROLE_REDIRECT
// ---------------------------------------------------------------------------

describe('roleRedirects', () => {
  it('maps each role to a path', async () => {
    const { ROLE_REDIRECT } = await import('@/app/roleRedirects');
    expect(ROLE_REDIRECT['ADM']).toBe('/admin');
    expect(ROLE_REDIRECT['TCH']).toBe('/teacher');
    expect(ROLE_REDIRECT['STD']).toBe('/student/home');
    expect(ROLE_REDIRECT['PAR']).toBe('/feed');
  });
});
