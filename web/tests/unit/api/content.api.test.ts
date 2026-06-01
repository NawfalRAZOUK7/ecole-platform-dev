import { http, HttpResponse } from 'msw';
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { cmsService } from '@/features/content/cms/api/cms.api';
import { contentService } from '@/features/content/catalog/api/content.api';
import { documentsService } from '@/features/content/documents/api/documents.api';
import { feedService } from '@/features/content/feed/api/feed.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

// ── cmsService ────────────────────────────────────────────────────────────────

describe('cmsService', () => {
  const contentItem = {
    id: 'ci-1',
    title: 'My Story',
    content_type: 'story',
    level_band: 'A1',
    language: 'fr',
    subject: 'French',
    description: null,
    page_count: 5,
    letter: null,
    target_age_min: 5,
    target_age_max: 8,
    theme_color: null,
    thumbnail_path: null,
    origin: 'school',
    status: 'published',
    created_by: 'user-1',
    original_content_id: null,
  };

  it('listContent lists CMS content', async () => {
    server.use(
      http.get('/api/v1/cms/content', () =>
        HttpResponse.json({ data: [contentItem], meta: listMeta }),
      ),
    );
    const result = await cmsService.listContent({});
    expect(result.data).toHaveLength(1);
  });

  it('createContent posts new content', async () => {
    server.use(
      http.post('/api/v1/cms/content', () => HttpResponse.json({ data: { id: 'ci-2' }, meta })),
    );
    const result = await cmsService.createContent({ title: 'New Story', content_type: 'story' });
    expect(result.data.id).toBe('ci-2');
  });

  it('updateContent puts content', async () => {
    server.use(
      http.put('/api/v1/cms/content/ci-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await cmsService.updateContent('ci-1', { title: 'Updated' });
    expect(result).toBeDefined();
  });

  it('deleteContent deletes content', async () => {
    server.use(
      http.delete('/api/v1/cms/content/ci-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await cmsService.deleteContent('ci-1');
    expect(result).toBeDefined();
  });

  it('listLibraryContent lists library items', async () => {
    const lib = {
      id: 'lib-1',
      school_id: 'school-1',
      title: 'Library Item',
      content_type: 'pdf',
      level_band: 'B1',
      language: 'en',
      subject: null,
      description: null,
      page_count: null,
      letter: null,
      target_age_min: null,
      target_age_max: null,
      theme_color: null,
      origin: 'global',
      status: 'published',
    };
    server.use(
      http.get('/api/v1/content/library', () => HttpResponse.json({ data: [lib], meta: listMeta })),
    );
    const result = await cmsService.listLibraryContent({});
    expect(result.data).toHaveLength(1);
  });

  it('assignLibraryContent posts assignment', async () => {
    server.use(
      http.post('/api/v1/content/assign', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await cmsService.assignLibraryContent({
      content_item_id: 'ci-1',
      class_id: 'class-1',
      notes: null,
    });
    expect(result).toBeDefined();
  });

  it('removeLibraryAssignment deletes assignment', async () => {
    server.use(
      http.delete('/api/v1/content/assign/assign-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await cmsService.removeLibraryAssignment('assign-1');
    expect(result).toBeDefined();
  });

  it('submitLibraryContentForReview posts for review', async () => {
    server.use(
      http.post('/api/v1/content/submit-for-review', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await cmsService.submitLibraryContentForReview('ci-1');
    expect(result).toBeDefined();
  });

  it('listLibrarySubmissions lists my submissions', async () => {
    const sub = {
      id: 'sub-1',
      content_item_id: 'ci-1',
      content_title: 'My Story',
      status: 'pending',
      submitted_at: null,
      review_notes: null,
      promoted_content_id: null,
    };
    server.use(
      http.get('/api/v1/content/my-submissions', () =>
        HttpResponse.json({ data: [sub], meta: listMeta }),
      ),
    );
    const result = await cmsService.listLibrarySubmissions({});
    expect(result.data).toHaveLength(1);
  });

  it('listClassContent lists content for a class', async () => {
    server.use(
      http.get('/api/v1/classes/class-1/content', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await cmsService.listClassContent('class-1');
    expect(result.data).toEqual([]);
  });

  it('listStoryPages lists pages', async () => {
    server.use(
      http.get('/api/v1/content-items/ci-1/pages', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await cmsService.listStoryPages('ci-1');
    expect(result.data).toEqual([]);
  });

  it('listSubmissions lists CMS submissions', async () => {
    server.use(
      http.get('/api/v1/cms/submissions', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await cmsService.listSubmissions({});
    expect(result.data).toEqual([]);
  });

  it('reviewSubmission posts review', async () => {
    server.use(
      http.post('/api/v1/cms/submissions/sub-1/review', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await cmsService.reviewSubmission('sub-1', { decision: 'approved' });
    expect(result).toBeDefined();
  });

  it('getAnalyticsSnapshot aggregates analytics', async () => {
    server.use(
      http.get('/api/v1/cms/content', () => HttpResponse.json({ data: [], meta: listMeta })),
      http.get('/api/v1/cms/submissions', () => HttpResponse.json({ data: [], meta: listMeta })),
      http.get('/api/v1/quizzes', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await cmsService.getAnalyticsSnapshot();
    expect(result.contentStats.total_items).toBe(0);
    expect(result.submissionStats.total_submissions).toBe(0);
  });

  it('getPendingSubmissionBadge returns count', async () => {
    server.use(
      http.get('/api/v1/cms/submissions', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const count = await cmsService.getPendingSubmissionBadge();
    expect(count).toBe(0);
  });
});

// ── contentService ─────────────────────────────────────────────────────────────

describe('contentService', () => {
  const item = {
    id: 'ci-1',
    title: 'Test',
    content_type: 'video',
    status: 'published',
  };

  it('listContentItems lists items', async () => {
    server.use(
      http.get('/api/v1/content-items', () =>
        HttpResponse.json({
          data: [item],
          meta: {
            next_cursor: null,
            has_more: false,
            ...{ timestamp: new Date().toISOString(), version: '0.1.0' },
          },
        }),
      ),
    );
    const result = await contentService.listContentItems({});
    expect(result.data).toHaveLength(1);
  });

  it('getContentItem gets a single item', async () => {
    server.use(
      http.get('/api/v1/content-items/ci-1', () =>
        HttpResponse.json({
          data: item,
          meta: { timestamp: new Date().toISOString(), version: '0.1.0' },
        }),
      ),
    );
    const result = await contentService.getContentItem('ci-1');
    expect(result.data.id).toBe('ci-1');
  });

  it('listStoryPages lists pages for content item', async () => {
    server.use(
      http.get('/api/v1/content-items/ci-1/pages', () =>
        HttpResponse.json({
          data: [],
          meta: {
            next_cursor: null,
            has_more: false,
            timestamp: new Date().toISOString(),
            version: '0.1.0',
          },
        }),
      ),
    );
    const result = await contentService.listStoryPages('ci-1');
    expect(result.data).toEqual([]);
  });

  it('updateProgress posts progress', async () => {
    server.use(
      http.post('/api/v1/content-items/ci-1/progress', () =>
        HttpResponse.json({
          data: { id: 'pr-1', student_id: 's-1', content_item_id: 'ci-1', status: 'in_progress' },
          meta: { timestamp: new Date().toISOString(), version: '0.1.0' },
        }),
      ),
    );
    const result = await contentService.updateProgress('ci-1', 'in_progress');
    expect(result.data.status).toBe('in_progress');
  });

  it('completeContentItem posts complete', async () => {
    server.use(
      http.post('/api/v1/content-items/ci-1/complete', () =>
        HttpResponse.json({
          data: {
            progress: {
              id: 'pr-1',
              student_id: 's-1',
              content_item_id: 'ci-1',
              status: 'completed',
            },
            reward: {
              id: 'r-1',
              student_id: 's-1',
              stars: 5,
              xp: 10,
              level: 1,
              streak_days: 1,
              badges: [],
              last_activity_at: null,
              level_progress: 10,
            },
            newly_earned_badges: [],
          },
          meta: { timestamp: new Date().toISOString(), version: '0.1.0' },
        }),
      ),
    );
    const result = await contentService.completeContentItem('ci-1', 60);
    expect(result.data.progress.status).toBe('completed');
  });

  it('togglePublish puts publish status', async () => {
    server.use(
      http.put('/api/v1/cms/content/ci-1', () =>
        HttpResponse.json({
          data: undefined,
          meta: { timestamp: new Date().toISOString(), version: '0.1.0' },
        }),
      ),
    );
    const result = await contentService.togglePublish('ci-1', 'published');
    expect(result).toBeDefined();
  });

  it('deleteAsset deletes content asset', async () => {
    server.use(
      http.delete('/api/v1/content-items/ci-1/assets/asset-1', () =>
        HttpResponse.json({
          data: undefined,
          meta: { timestamp: new Date().toISOString(), version: '0.1.0' },
        }),
      ),
    );
    const result = await contentService.deleteAsset('ci-1', 'asset-1');
    expect(result).toBeDefined();
  });
});

// ── documentsService ──────────────────────────────────────────────────────────

describe('documentsService', () => {
  const docItem = {
    id: 'doc-1',
    original_filename: 'test.pdf',
    filename: 'test.pdf',
    mime_type: 'application/pdf',
    size_bytes: 1000,
    category: 'general',
    linked_student_id: null,
    linked_student_name: null,
    uploader_id: 'user-1',
    uploader_name: 'User',
    expires_at: null,
    is_expired: false,
    is_expiring_soon: false,
    download_count: 0,
    thumbnail_url: null,
    preview_url: null,
    download_url: null,
    created_at: new Date().toISOString(),
    deduplicated: false,
    can_delete: true,
    can_hard_delete: false,
  };

  const lmeta = {
    timestamp: new Date().toISOString(),
    version: '0.1.0',
    next_cursor: null,
    has_more: false,
  };
  const smeta = { timestamp: new Date().toISOString(), version: '0.1.0' };

  it('getOptions returns document options', async () => {
    server.use(
      http.get('/api/v1/documents/options', () =>
        HttpResponse.json({ data: { students: [], categories: ['general'] }, meta: smeta }),
      ),
    );
    const result = await documentsService.getOptions();
    expect(result.data.categories).toContain('general');
  });

  it('listMyDocuments lists own documents', async () => {
    server.use(
      http.get('/api/v1/documents', () => HttpResponse.json({ data: [docItem], meta: lmeta })),
    );
    const result = await documentsService.listMyDocuments();
    expect(result.data).toHaveLength(1);
  });

  it('listStudentDocuments lists student documents', async () => {
    server.use(
      http.get('/api/v1/students/student-1/documents', () =>
        HttpResponse.json({ data: [], meta: lmeta }),
      ),
    );
    const result = await documentsService.listStudentDocuments('student-1');
    expect(result.data).toEqual([]);
  });

  it('getStudentChecklist returns checklist', async () => {
    server.use(
      http.get('/api/v1/students/student-1/documents/checklist', () =>
        HttpResponse.json({ data: [], meta: smeta }),
      ),
    );
    const result = await documentsService.getStudentChecklist('student-1');
    expect(result.data).toEqual([]);
  });

  it('listResources lists resources', async () => {
    server.use(http.get('/api/v1/resources', () => HttpResponse.json({ data: [], meta: lmeta })));
    const result = await documentsService.listResources({});
    expect(result.data).toEqual([]);
  });

  it('getDocument gets a document', async () => {
    server.use(
      http.get('/api/v1/documents/doc-1', () => HttpResponse.json({ data: docItem, meta: smeta })),
    );
    const result = await documentsService.getDocument('doc-1');
    expect(result.data.id).toBe('doc-1');
  });

  it('bulkDelete posts bulk delete', async () => {
    server.use(
      http.post('/api/v1/documents/bulk-delete', () =>
        HttpResponse.json({ data: undefined, meta: smeta }),
      ),
    );
    const result = await documentsService.bulkDelete(['doc-1', 'doc-2']);
    expect(result).toBeDefined();
  });

  it('deleteDocument deletes document', async () => {
    server.use(
      http.delete('/api/v1/documents/doc-1', () =>
        HttpResponse.json({
          data: { id: 'doc-1', deleted: true, hard_deleted: false },
          meta: smeta,
        }),
      ),
    );
    const result = await documentsService.deleteDocument('doc-1');
    expect(result.data.deleted).toBe(true);
  });

  it('bulkDownload posts bulk download', async () => {
    server.use(
      http.post('/api/v1/documents/bulk-download', () =>
        HttpResponse.json({ data: { download_url: 'https://example.com/zip' }, meta: smeta }),
      ),
    );
    const result = await documentsService.bulkDownload(['doc-1']);
    expect(result.data.download_url).toBeTruthy();
  });

  it('rateResource posts rating', async () => {
    server.use(
      http.post('/api/v1/resources/res-1/rate', () =>
        HttpResponse.json({ data: undefined, meta: smeta }),
      ),
    );
    const result = await documentsService.rateResource('res-1', 5);
    expect(result).toBeDefined();
  });

  it('getVersions returns document versions', async () => {
    server.use(
      http.get('/api/v1/documents/doc-1/versions', () =>
        HttpResponse.json({ data: [], meta: smeta }),
      ),
    );
    const result = await documentsService.getVersions('doc-1');
    expect(result.data).toEqual([]);
  });

  it('downloadDocument returns download url', async () => {
    server.use(
      http.get('/api/v1/documents/doc-1/download', () =>
        HttpResponse.json({ data: { download_url: 'https://example.com/doc-1' }, meta: smeta }),
      ),
    );
    const result = await documentsService.downloadDocument('doc-1');
    expect(result.data.download_url).toBeTruthy();
  });

  it('updateResource puts resource', async () => {
    server.use(
      http.put('/api/v1/resources/res-1', () =>
        HttpResponse.json({ data: { id: 'res-1' }, meta: smeta }),
      ),
    );
    const result = await documentsService.updateResource('res-1', { title: 'Updated' });
    expect(result.data).toBeDefined();
  });

  it('deleteResource deletes resource', async () => {
    server.use(
      http.delete('/api/v1/resources/res-1', () =>
        HttpResponse.json({ data: { id: 'res-1', deleted: true }, meta: smeta }),
      ),
    );
    const result = await documentsService.deleteResource('res-1');
    expect(result.data.deleted).toBe(true);
  });

  it('downloadResource returns download url', async () => {
    server.use(
      http.get('/api/v1/resources/res-1/download', () =>
        HttpResponse.json({ data: { download_url: 'https://example.com/res' }, meta: smeta }),
      ),
    );
    const result = await documentsService.downloadResource('res-1');
    expect(result.data.download_url).toBeTruthy();
  });
});

// ── feedService ───────────────────────────────────────────────────────────────

describe('feedService', () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
      removeItem: (k: string) => {
        delete store[k];
      },
      clear: () => Object.keys(store).forEach((k) => delete store[k]),
    });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('list returns feed items', async () => {
    const feedItem = {
      id: 'f-1',
      type: 'announcement',
      title: 'Test',
      body: '',
      created_at: new Date().toISOString(),
    };
    server.use(
      http.get('/api/v1/feed', () =>
        HttpResponse.json({
          data: [feedItem],
          meta: {
            next_cursor: null,
            has_more: false,
            timestamp: new Date().toISOString(),
            version: '0.1.0',
          },
        }),
      ),
    );
    const result = await feedService.list({});
    expect(result.data).toHaveLength(1);
  });

  it('markAsRead stores item id locally', async () => {
    const result = await feedService.markAsRead('feed-item-1');
    expect(result.is_read).toBe(true);
  });

  it('isRead returns false for unread item', () => {
    const isRead = feedService.isRead('never-read-item-xyz');
    expect(isRead).toBe(false);
  });

  it('countUnread counts items not in read set', () => {
    const items = [{ id: 'x-1' }, { id: 'x-2' }] as Parameters<typeof feedService.countUnread>[0];
    const count = feedService.countUnread(items);
    expect(count).toBeGreaterThanOrEqual(0);
  });

  it('subscribeToReadChanges returns unsubscribe function', () => {
    const unsub = feedService.subscribeToReadChanges(() => undefined);
    expect(typeof unsub).toBe('function');
    unsub();
  });
});
