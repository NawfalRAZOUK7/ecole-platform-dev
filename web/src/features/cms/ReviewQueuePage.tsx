import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import { useCmsSubmissions, useReviewCmsSubmission } from './useCms';
import type { CmsSubmission } from './cms.service';

const STATUS_OPTIONS = ['PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED'];
const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english', 'islamic_studies', 'art', 'sport'];
const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];

export function CmsReviewQueuePage() {
  const { t } = useTranslation();
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [subjectFilter, setSubjectFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [selectedItem, setSelectedItem] = useState<CmsSubmission | null>(null);
  const [reviewAction, setReviewAction] = useState<'APPROVED' | 'REJECTED' | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [rewardPoints, setRewardPoints] = useState(10);
  const [error, setError] = useState<string | null>(null);
  const [statusOverrides, setStatusOverrides] = useState<Record<string, string>>({});
  const submissionsQuery = useCmsSubmissions({
    status: statusFilter || undefined,
    subject: subjectFilter || undefined,
    level_band: levelFilter || undefined,
  });
  const reviewSubmissionMutation = useReviewCmsSubmission();

  const items = useMemo(
    () => submissionsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [submissionsQuery.data]
  );

  if (submissionsQuery.isLoading && items.length === 0) {
    return <LoadingState />;
  }

  async function handleReview() {
    if (!selectedItem || !reviewAction) return;
    if (reviewAction === 'REJECTED' && !reviewNotes.trim()) return;

    setError(null);

    try {
      await reviewSubmissionMutation.mutateAsync({
        submissionId: selectedItem.id,
        payload: {
          decision: reviewAction,
          review_notes: reviewNotes || undefined,
          reward_points: reviewAction === 'APPROVED' ? rewardPoints : 0,
        },
      });
      setSelectedItem(null);
      setReviewAction(null);
      setReviewNotes('');
      setRewardPoints(10);
      setStatusOverrides((previous) => {
        const next = { ...previous };
        delete next[selectedItem.id];
        return next;
      });
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : t('app.error'));
    }
  }

  function handleMarkUnderReview(item: CmsSubmission) {
    setStatusOverrides((previous) => ({
      ...previous,
      [item.id]: 'UNDER_REVIEW',
    }));
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('cms.review.title')}</h1>
      <ErrorBanner
        error={error || (submissionsQuery.error instanceof Error ? submissionsQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void submissionsQuery.refetch()}
      />

      <div className="filter-bar" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <select className="filter-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="">{t('cms.review.allStatuses')}</option>
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>{t(`cms.reviewStatuses.${status}`, status)}</option>
          ))}
        </select>
        <select className="filter-select" value={subjectFilter} onChange={(event) => setSubjectFilter(event.target.value)}>
          <option value="">{t('cms.content.allSubjects')}</option>
          {SUBJECTS.map((subject) => (
            <option key={subject} value={subject}>{t(`cms.subjects.${subject}`, subject)}</option>
          ))}
        </select>
        <select className="filter-select" value={levelFilter} onChange={(event) => setLevelFilter(event.target.value)}>
          <option value="">{t('cms.content.allLevels')}</option>
          {LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
        </select>
      </div>

      {items.length === 0 ? (
        <p className="empty-state">{t('cms.review.empty')}</p>
      ) : (
        <div className="card-list">
          {items.map((item) => {
            const displayStatus = statusOverrides[item.id] || item.status;

            return (
              <div key={item.id} className="card" style={{ padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 8 }}>
                  <div>
                    <h3 style={{ margin: '0 0 4px' }}>{item.content_title || t('cms.review.untitled')}</h3>
                    <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {item.submitter_name || item.submitted_by} • {item.school_id}
                    </div>
                  </div>
                  <span className={`badge badge--${displayStatus.toLowerCase()}`}>
                    {t(`cms.reviewStatuses.${displayStatus}`, displayStatus)}
                  </span>
                </div>

                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
                  {formatDate(item.submitted_at)}
                </div>

                {item.review_notes ? (
                  <p style={{ fontSize: 13, marginBottom: 12 }}>{item.review_notes}</p>
                ) : null}

                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button className="btn btn-sm btn-secondary" onClick={() => setSelectedItem(item)}>
                    {t('cms.review.view')}
                  </button>
                  {displayStatus === 'PENDING' ? (
                    <>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => {
                          setSelectedItem(item);
                          setReviewAction('APPROVED');
                        }}
                      >
                        {t('cms.review.approve')}
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => {
                          setSelectedItem(item);
                          setReviewAction('REJECTED');
                        }}
                      >
                        {t('cms.review.reject')}
                      </button>
                      <button className="btn btn-sm" onClick={() => handleMarkUnderReview(item)}>
                        {t('cms.review.markUnderReview')}
                      </button>
                    </>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {submissionsQuery.hasNextPage ? (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button className="btn" onClick={() => void submissionsQuery.fetchNextPage()} disabled={submissionsQuery.isFetchingNextPage}>
            {submissionsQuery.isFetchingNextPage ? t('app.loading') : t('cms.content.loadMore')}
          </button>
        </div>
      ) : null}

      {selectedItem ? (
        <div
          className="modal-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 24,
          }}
        >
          <div className="card" style={{ padding: 24, maxWidth: 600, width: '100%', maxHeight: '80vh', overflow: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ margin: 0 }}>{selectedItem.content_title || t('cms.review.untitled')}</h2>
              <button
                className="btn btn-sm"
                onClick={() => {
                  setSelectedItem(null);
                  setReviewAction(null);
                  setReviewNotes('');
                }}
              >
                {t('app.close')}
              </button>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, marginBottom: 4 }}>
                <strong>{t('cms.review.teacher')}:</strong> {selectedItem.submitter_name || selectedItem.submitted_by}
              </div>
              <div style={{ fontSize: 13, marginBottom: 4 }}>
                <strong>{t('cms.review.school')}:</strong> {selectedItem.school_id}
              </div>
              <div style={{ fontSize: 13, marginBottom: 4 }}>
                <strong>{t('cms.review.submittedAt')}:</strong> {formatDate(selectedItem.submitted_at)}
              </div>
              <div style={{ fontSize: 13 }}>
                <strong>{t('cms.review.status')}:</strong> {t(`cms.reviewStatuses.${statusOverrides[selectedItem.id] || selectedItem.status}`, statusOverrides[selectedItem.id] || selectedItem.status)}
              </div>
            </div>

            {reviewAction ? (
              <>
                <div className="form-field">
                  <label>{t('cms.review.notes')}</label>
                  <textarea
                    value={reviewNotes}
                    onChange={(event) => setReviewNotes(event.target.value)}
                    rows={4}
                    className="filter-input"
                    style={{ width: '100%' }}
                  />
                </div>

                {reviewAction === 'APPROVED' ? (
                  <div className="form-field">
                    <label>{t('cms.review.rewardPoints')}</label>
                    <input
                      type="number"
                      min="0"
                      value={rewardPoints}
                      onChange={(event) => setRewardPoints(Number(event.target.value))}
                    />
                  </div>
                ) : null}

                <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                  <button className="btn btn-primary" onClick={() => void handleReview()} disabled={reviewSubmissionMutation.isPending}>
                    {reviewSubmissionMutation.isPending ? t('app.loading') : t('app.confirm')}
                  </button>
                  <button className="btn btn-secondary" onClick={() => setReviewAction(null)}>
                    {t('app.cancel')}
                  </button>
                </div>
              </>
            ) : (
              selectedItem.status === 'PENDING' ? (
                <div style={{ display: 'flex', gap: 12 }}>
                  <button className="btn btn-primary" onClick={() => setReviewAction('APPROVED')}>
                    {t('cms.review.approve')}
                  </button>
                  <button className="btn btn-danger" onClick={() => setReviewAction('REJECTED')}>
                    {t('cms.review.reject')}
                  </button>
                </div>
              ) : null
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
