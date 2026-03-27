/**
 * CMS Analytics — content usage stats + teacher contribution stats.
 *
 * Phase 10A — displays content metrics (views, downloads, ratings)
 * and teacher submission/approval stats.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';

interface ContentStats {
  total_items: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_subject: Record<string, number>;
  by_level: Record<string, number>;
  by_origin: Record<string, number>;
}

interface SubmissionStats {
  total_submissions: number;
  by_status: Record<string, number>;
  top_contributors: Array<{ submitter_name: string; count: number }>;
  avg_review_time_hours: number | null;
}

interface QuizStats {
  total_quizzes: number;
  published: number;
  total_attempts: number;
  avg_score: number | null;
}

export function CmsAnalyticsPage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contentStats, setContentStats] = useState<ContentStats | null>(null);
  const [submissionStats, setSubmissionStats] = useState<SubmissionStats | null>(null);
  const [quizStats, setQuizStats] = useState<QuizStats | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      // Fetch content stats — derive from content list
      const contentResp = await api.list<{
        id: string; status: string; content_type: string;
        subject: string | null; level_band: string | null; origin: string;
      }>('/cms/content', { limit: 200 });

      const items = contentResp.data;
      const cStats: ContentStats = {
        total_items: items.length,
        by_status: {},
        by_type: {},
        by_subject: {},
        by_level: {},
        by_origin: {},
      };
      for (const item of items) {
        cStats.by_status[item.status] = (cStats.by_status[item.status] || 0) + 1;
        cStats.by_type[item.content_type] = (cStats.by_type[item.content_type] || 0) + 1;
        if (item.subject) cStats.by_subject[item.subject] = (cStats.by_subject[item.subject] || 0) + 1;
        if (item.level_band) cStats.by_level[item.level_band] = (cStats.by_level[item.level_band] || 0) + 1;
        cStats.by_origin[item.origin] = (cStats.by_origin[item.origin] || 0) + 1;
      }
      setContentStats(cStats);

      // Fetch submission stats — derive from submissions list
      const subResp = await api.list<{
        id: string; status: string; submitter_name: string | null;
        submitted_by: string; submitted_at: string; reviewed_at: string | null;
      }>('/cms/submissions', { limit: 200 });

      const subs = subResp.data;
      const sStats: SubmissionStats = {
        total_submissions: subs.length,
        by_status: {},
        top_contributors: [],
        avg_review_time_hours: null,
      };

      const contributorMap: Record<
        string,
        { submitter_name: string; count: number }
      > = {};
      let totalReviewMs = 0;
      let reviewCount = 0;

      for (const sub of subs) {
        sStats.by_status[sub.status] = (sStats.by_status[sub.status] || 0) + 1;
        const key = sub.submitted_by;
        if (!contributorMap[key]) {
          contributorMap[key] = {
            submitter_name: sub.submitter_name || key,
            count: 0,
          };
        }
        contributorMap[key].count++;

        if (sub.reviewed_at && sub.submitted_at) {
          const diff = new Date(sub.reviewed_at).getTime() - new Date(sub.submitted_at).getTime();
          if (diff > 0) { totalReviewMs += diff; reviewCount++; }
        }
      }

      sStats.top_contributors = Object.values(contributorMap)
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

      if (reviewCount > 0) {
        sStats.avg_review_time_hours = Math.round((totalReviewMs / reviewCount / 3600000) * 10) / 10;
      }
      setSubmissionStats(sStats);

      // Fetch quiz stats
      const quizResp = await api.list<{
        id: string; status: string;
      }>('/quizzes', { limit: 200 });

      const quizzes = quizResp.data;
      setQuizStats({
        total_quizzes: quizzes.length,
        published: quizzes.filter((q) => q.status === 'published').length,
        total_attempts: 0,
        avg_score: null,
      });

      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchAnalytics().finally(() => setLoading(false));
  }, [fetchAnalytics]);

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('cms.analytics.title')}</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchAnalytics} />

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <StatCard label={t('cms.analytics.totalContent')} value={contentStats?.total_items ?? 0} />
        <StatCard label={t('cms.analytics.published')} value={contentStats?.by_status?.published ?? 0} />
        <StatCard label={t('cms.analytics.totalSubmissions')} value={submissionStats?.total_submissions ?? 0} />
        <StatCard label={t('cms.analytics.pendingReview')} value={submissionStats?.by_status?.PENDING ?? 0} accent />
        <StatCard label={t('cms.analytics.totalQuizzes')} value={quizStats?.total_quizzes ?? 0} />
        <StatCard label={t('cms.analytics.avgReviewTime')} value={submissionStats?.avg_review_time_hours != null ? `${submissionStats.avg_review_time_hours}h` : '—'} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Content by type */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.byType')}</h3>
          {contentStats && Object.entries(contentStats.by_type).map(([key, val]) => (
            <BarRow key={key} label={t(`cms.contentTypes.${key}`, key)} value={val} total={contentStats.total_items} />
          ))}
        </div>

        {/* Content by subject */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.bySubject')}</h3>
          {contentStats && Object.entries(contentStats.by_subject).map(([key, val]) => (
            <BarRow key={key} label={t(`cms.subjects.${key}`, key)} value={val} total={contentStats.total_items} />
          ))}
          {contentStats && Object.keys(contentStats.by_subject).length === 0 && (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('cms.analytics.noData')}</p>
          )}
        </div>

        {/* Content by status */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.byStatus')}</h3>
          {contentStats && Object.entries(contentStats.by_status).map(([key, val]) => (
            <BarRow key={key} label={t(`cms.statuses.${key}`, key)} value={val} total={contentStats.total_items} />
          ))}
        </div>

        {/* Content by origin */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.byOrigin')}</h3>
          {contentStats && Object.entries(contentStats.by_origin).map(([key, val]) => (
            <BarRow key={key} label={t(`cms.origins.${key}`, key)} value={val} total={contentStats.total_items} />
          ))}
        </div>

        {/* Submission status */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.submissionStatus')}</h3>
          {submissionStats && Object.entries(submissionStats.by_status).map(([key, val]) => (
            <BarRow key={key} label={t(`cms.reviewStatuses.${key}`, key)} value={val} total={submissionStats.total_submissions} />
          ))}
          {submissionStats && submissionStats.total_submissions === 0 && (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('cms.analytics.noData')}</p>
          )}
        </div>

        {/* Top contributors */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.topContributors')}</h3>
          {submissionStats && submissionStats.top_contributors.length > 0 ? (
            <table style={{ width: '100%', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--color-border)' }}>
                  <th style={{ padding: '4px 0' }}>{t('cms.analytics.teacher')}</th>
                  <th style={{ padding: '4px 0', textAlign: 'right' }}>{t('cms.analytics.submissions')}</th>
                </tr>
              </thead>
              <tbody>
                {submissionStats.top_contributors.map((c, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '6px 0' }}>{c.submitter_name}</td>
                    <td style={{ padding: '6px 0', textAlign: 'right', fontWeight: 600 }}>{c.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('cms.analytics.noData')}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="card" style={{ padding: 16, textAlign: 'center' }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: accent ? 'var(--color-warning)' : 'var(--color-primary)' }}>
        {value}
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 4 }}>{label}</div>
    </div>
  );
}

function BarRow({ label, value, total }: { label: string; value: number; total: number }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 2 }}>
        <span>{label}</span>
        <span style={{ fontWeight: 600 }}>{value} ({pct}%)</span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: 'var(--color-bg-secondary)' }}>
        <div style={{ height: '100%', borderRadius: 3, background: 'var(--color-primary)', width: `${pct}%`, transition: 'width 0.3s' }} />
      </div>
    </div>
  );
}
