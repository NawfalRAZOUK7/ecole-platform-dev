import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { adminService } from '@/features/admin/api/admin.api';
import { featuresService } from '@/features/admin/api/features.api';
import { complianceService } from '@/features/admin/compliance/api/compliance.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

// ── adminService ──────────────────────────────────────────────────────────────

describe('adminService', () => {
  it('getDashboard returns dashboard data', async () => {
    server.use(
      http.get('/api/v1/admin/dashboard', () =>
        HttpResponse.json({
          data: {
            users: 50,
            active_sessions: 5,
            active_invitations: 2,
            audit_events_24h: 100,
            pending_justifications: 3,
            users_by_role: {},
          },
          meta,
        }),
      ),
    );
    const result = await adminService.getDashboard();
    expect(result.data.users).toBe(50);
  });

  it('getKpis returns KPIs', async () => {
    server.use(
      http.get('/api/v1/kpis', () =>
        HttpResponse.json({
          data: { kpis: [], period: '30', computed_at: new Date().toISOString() },
          meta,
        }),
      ),
    );
    const result = await adminService.getKpis(30);
    expect(result.data.kpis).toEqual([]);
  });

  it('listAuditLogs returns audit entries', async () => {
    server.use(
      http.get('/api/v1/admin/audit-logs', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await adminService.listAuditLogs({});
    expect(result.data).toEqual([]);
  });

  it('listUsers returns users', async () => {
    server.use(
      http.get('/api/v1/admin/users', () =>
        HttpResponse.json({
          data: [
            {
              id: 'user-1',
              email: 'test@school.ma',
              full_name: 'Test',
              status: 'active',
              role: 'teacher',
              created_at: null,
              email_verified: true,
              totp_enabled: false,
            },
          ],
          meta: listMeta,
        }),
      ),
    );
    const result = await adminService.listUsers({});
    expect(result.data).toHaveLength(1);
  });

  it('suspendUser puts suspend', async () => {
    server.use(
      http.put('/api/v1/admin/users/user-1/suspend', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await adminService.suspendUser('user-1');
    expect(result).toBeDefined();
  });

  it('activateUser puts activate', async () => {
    server.use(
      http.put('/api/v1/admin/users/user-1/activate', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await adminService.activateUser('user-1');
    expect(result).toBeDefined();
  });

  it('changeUserRole puts role change', async () => {
    server.use(
      http.put('/api/v1/admin/users/user-1/role', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await adminService.changeUserRole('user-1', 'admin');
    expect(result).toBeDefined();
  });

  it('registerBatch posts batch registration', async () => {
    server.use(
      http.post('/api/v1/admin/register-batch', () =>
        HttpResponse.json({
          data: { created: [], errors: [], total_created: 0, total_errors: 0 },
          meta,
        }),
      ),
    );
    const result = await adminService.registerBatch([
      { email: 'new@school.ma', full_name: 'New User', role: 'teacher' },
    ]);
    expect(result.data.total_created).toBe(0);
  });

  it('listInvitations returns invitations', async () => {
    server.use(
      http.get('/api/v1/admin/invitations', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await adminService.listInvitations({});
    expect(result.data).toEqual([]);
  });

  it('createInvitation posts invitation', async () => {
    server.use(
      http.post('/api/v1/invites/create', () =>
        HttpResponse.json({ data: { code: 'invite-code-123' }, meta }),
      ),
    );
    const result = await adminService.createInvitation({
      role_target: 'teacher',
      expires_in_hours: 48,
    });
    expect(result.data.code).toBe('invite-code-123');
  });

  it('revokeInvitation posts revoke', async () => {
    server.use(
      http.post('/api/v1/invites/revoke', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await adminService.revokeInvitation('invite-1');
    expect(result).toBeDefined();
  });

  it('listJustifications returns justifications', async () => {
    server.use(
      http.get('/api/v1/admin/justifications', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await adminService.listJustifications({});
    expect(result.data).toEqual([]);
  });

  it('reviewJustification posts review decision', async () => {
    server.use(
      http.post('/api/v1/attendance/justifications/just-1/review', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await adminService.reviewJustification('just-1', { decision: 'justified' });
    expect(result).toBeDefined();
  });

  it('listParentChildLinks returns links', async () => {
    server.use(
      http.get('/api/v1/admin/parent-child-links', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await adminService.listParentChildLinks({});
    expect(result.data).toEqual([]);
  });

  it('getUserProfile returns user profile', async () => {
    server.use(
      http.get('/api/v1/admin/users/user-1/profile', () =>
        HttpResponse.json({
          data: { email: 'test@school.ma', full_name: 'Test User', role: 'teacher' },
          meta,
        }),
      ),
    );
    const result = await adminService.getUserProfile('user-1');
    expect(result.data.email).toBe('test@school.ma');
  });

  it('createParentChildLink posts link', async () => {
    server.use(
      http.post('/api/v1/admin/parent-child-links', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await adminService.createParentChildLink('parent-1', 'child-1');
    expect(result).toBeDefined();
  });

  it('revokeParentChildLink deletes link', async () => {
    server.use(
      http.delete('/api/v1/admin/parent-child-links/link-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await adminService.revokeParentChildLink('link-1');
    expect(result).toBeDefined();
  });

  it('impersonateUser posts impersonation', async () => {
    server.use(
      http.post('/api/v1/admin/impersonate/user-1', () =>
        HttpResponse.json({
          data: { access_token: 'imp-tok', user_id: 'user-1', role: 'teacher' },
          meta,
        }),
      ),
    );
    const result = await adminService.impersonateUser('user-1');
    expect(result.data.access_token).toBe('imp-tok');
  });

  it('stopImpersonation posts stop', async () => {
    server.use(
      http.post('/api/v1/admin/stop-impersonation', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await adminService.stopImpersonation();
    expect(result).toBeDefined();
  });

  it('getUserLoginHistory returns login history', async () => {
    server.use(
      http.get('/api/v1/admin/users/user-1/login-history', () =>
        HttpResponse.json({ data: [], meta }),
      ),
    );
    const result = await adminService.getUserLoginHistory('user-1');
    expect(result.data).toEqual([]);
  });

  it('createSchool posts school creation', async () => {
    const school = {
      id: 'school-2',
      name: 'New School',
      code: 'NS',
      address: null,
      city: null,
      phone: null,
      email: null,
      timezone: 'UTC',
      default_language: 'fr',
    };
    server.use(http.post('/api/v1/schools', () => HttpResponse.json({ data: school, meta })));
    const result = await adminService.createSchool({ name: 'New School', code: 'NS' });
    expect(result.data.name).toBe('New School');
  });

  it('listSchools returns schools', async () => {
    server.use(http.get('/api/v1/schools', () => HttpResponse.json({ data: [], meta: listMeta })));
    const result = await adminService.listSchools();
    expect(result.data).toEqual([]);
  });
});

// ── featuresService ───────────────────────────────────────────────────────────

describe('featuresService', () => {
  const toggle = {
    id: 'feat-1',
    feature_key: 'new_dashboard',
    display_name: 'New Dashboard',
    description: null,
    enabled_globally: false,
    enabled_school_ids: [],
    enabled_role_codes: [],
    created_at: new Date().toISOString(),
    updated_at: null,
  };

  it('listActiveFeatures returns active features', async () => {
    server.use(
      http.get('/api/v1/features/active', () =>
        HttpResponse.json({ data: { features: ['new_dashboard'] }, meta }),
      ),
    );
    const result = await featuresService.listActiveFeatures();
    expect(result.data.features).toContain('new_dashboard');
  });

  it('listFeatures returns feature toggles', async () => {
    server.use(
      http.get('/api/v1/features', () => HttpResponse.json({ data: [toggle], meta: listMeta })),
    );
    const result = await featuresService.listFeatures();
    expect(result.data).toHaveLength(1);
  });

  it('getFeature returns single toggle', async () => {
    server.use(
      http.get('/api/v1/features/feat-1', () => HttpResponse.json({ data: toggle, meta })),
    );
    const result = await featuresService.getFeature('feat-1');
    expect(result.data.feature_key).toBe('new_dashboard');
  });

  it('createFeature posts new toggle', async () => {
    server.use(http.post('/api/v1/features', () => HttpResponse.json({ data: toggle, meta })));
    const result = await featuresService.createFeature({
      feature_key: 'new_dashboard',
      display_name: 'New Dashboard',
    });
    expect(result.data.id).toBe('feat-1');
  });

  it('updateFeature puts toggle', async () => {
    server.use(
      http.put('/api/v1/features/feat-1', () =>
        HttpResponse.json({ data: { ...toggle, enabled_globally: true }, meta }),
      ),
    );
    const result = await featuresService.updateFeature('feat-1', { enabled_globally: true });
    expect(result.data.enabled_globally).toBe(true);
  });

  it('deleteFeature deletes toggle', async () => {
    server.use(
      http.delete('/api/v1/features/feat-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await featuresService.deleteFeature('feat-1');
    expect(result).toBeDefined();
  });
});

// ── complianceService ─────────────────────────────────────────────────────────

describe('complianceService', () => {
  it('listCurricula returns curricula', async () => {
    server.use(
      http.get('/api/v1/compliance/curricula', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await complianceService.listCurricula();
    expect(result.data).toEqual([]);
  });

  it('createCurriculum posts new curriculum', async () => {
    const curr = {
      id: 'curr-1',
      level: 'primary',
      grade: '5',
      subject: 'Math',
      academic_year: '2025-2026',
      total_objectives: 30,
      mapped_objectives: 0,
      is_active: true,
    };
    server.use(
      http.post('/api/v1/compliance/curricula', () => HttpResponse.json({ data: curr, meta })),
    );
    const result = await complianceService.createCurriculum({
      level: 'primary',
      grade: '5',
      subject: 'Math',
      academic_year: '2025-2026',
      title: 'Math Curriculum',
    });
    expect(result.data.id).toBe('curr-1');
  });

  it('listObjectives returns objectives', async () => {
    server.use(
      http.get('/api/v1/compliance/curricula/curr-1/objectives', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await complianceService.listObjectives('curr-1');
    expect(result.data).toEqual([]);
  });

  it('createMapping posts curriculum mapping', async () => {
    server.use(
      http.post('/api/v1/compliance/mappings', () =>
        HttpResponse.json({
          data: {
            id: 'map-1',
            curriculum_id: 'curr-1',
            objective_id: 'obj-1',
            course_id: null,
            content_item_id: null,
          },
          meta,
        }),
      ),
    );
    const result = await complianceService.createMapping({
      curriculum_id: 'curr-1',
      objective_id: 'obj-1',
      course_id: null,
      content_item_id: null,
    });
    expect(result.data.id).toBe('map-1');
  });

  it('listMappings returns mappings', async () => {
    server.use(
      http.get('/api/v1/compliance/mappings', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await complianceService.listMappings();
    expect(result.data).toEqual([]);
  });

  it('deleteMapping deletes mapping', async () => {
    server.use(
      http.delete('/api/v1/compliance/mappings/map-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await complianceService.deleteMapping('map-1');
    expect(result).toBeDefined();
  });

  it('getDashboard returns compliance dashboard', async () => {
    server.use(
      http.get('/api/v1/compliance/dashboard', () =>
        HttpResponse.json({
          data: {
            school_id: 'school-1',
            academic_year_id: 'year-1',
            curriculum_count: 5,
            total_objectives: 100,
            mapped_objectives: 80,
            overall_compliance_percent: 80,
            items: [],
          },
          meta,
        }),
      ),
    );
    const result = await complianceService.getDashboard({ academic_year_id: 'year-1' });
    expect(result.data.overall_compliance_percent).toBe(80);
  });

  it('generateReport posts report generation', async () => {
    server.use(
      http.post('/api/v1/compliance/reports/generate', () =>
        HttpResponse.json({
          data: {
            id: 'rep-1',
            status: 'pending',
            curriculum_id: 'curr-1',
            academic_year_id: 'year-1',
            generated_at: null,
            download_url: null,
          },
          meta,
        }),
      ),
    );
    const result = await complianceService.generateReport({
      curriculum_id: 'curr-1',
      academic_year_id: 'year-1',
    });
    expect(result.data.id).toBe('rep-1');
  });

  it('listReports returns reports', async () => {
    server.use(
      http.get('/api/v1/compliance/reports', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await complianceService.listReports();
    expect(result.data).toEqual([]);
  });

  it('downloadReport returns download url', async () => {
    server.use(
      http.get('/api/v1/compliance/reports/rep-1/download', () =>
        HttpResponse.json({ data: { download_url: 'https://example.com/report.pdf' }, meta }),
      ),
    );
    const result = await complianceService.downloadReport('rep-1');
    expect(result.data.download_url).toBeTruthy();
  });
});
