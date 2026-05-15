import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ErrorBanner, LoadingState } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { SyncConflict } from '../model/sync.types';
import { useResolveSyncConflict, useSyncConflicts } from '../model/useSync';

export function SyncConflictsPage() {
  const { t } = useTranslation();
  const [selectedConflict, setSelectedConflict] = useState<SyncConflict | null>(null);
  const [manualMergeNotes, setManualMergeNotes] = useState('');
  const conflictsQuery = useSyncConflicts();
  const resolveMutation = useResolveSyncConflict();

  async function handleResolve(resolution: 'client_wins' | 'server_wins' | 'manual') {
    if (!selectedConflict) {
      return;
    }

    await resolveMutation.mutateAsync({
      conflictId: selectedConflict.id,
      payload: {
        resolution,
      },
    });
    setSelectedConflict(null);
    setManualMergeNotes('');
  }

  if (conflictsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('sync.conflictsTitle')}</h1>
        <p className="page-subtitle">{t('sync.conflictsSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(conflictsQuery.error ?? resolveMutation.error, t('app.error'))}
      />

      <div className="card-list">
        {(conflictsQuery.data ?? []).map((conflict) => (
          <div key={conflict.id} className="card">
            <div className="page-header page-header--split">
              <div>
                <h2>{conflict.entity_type}</h2>
                <p>{conflict.entity_id}</p>
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setSelectedConflict(conflict)}
              >
                {t('sync.resolve')}
              </button>
            </div>
            <div className="card-list">
              <div className="card">
                <strong>{t('sync.keepLocal')}</strong>
                <pre style={{ whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(conflict.client_payload, null, 2)}
                </pre>
              </div>
              <div className="card">
                <strong>{t('sync.keepRemote')}</strong>
                <pre style={{ whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(conflict.server_payload, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedConflict ? (
        <div className="card">
          <h2>{t('sync.manualMerge')}</h2>
          <textarea
            className="filter-input"
            rows={6}
            value={manualMergeNotes}
            onChange={(event) => setManualMergeNotes(event.target.value)}
            placeholder={t('sync.manualMergePlaceholder')}
          />
          <div className="page-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => void handleResolve('client_wins')}
            >
              {t('sync.keepLocal')}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => void handleResolve('server_wins')}
            >
              {t('sync.keepRemote')}
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void handleResolve('manual')}
            >
              {t('sync.manualMerge')}
            </button>
          </div>
          {manualMergeNotes ? <p>{manualMergeNotes}</p> : null}
        </div>
      ) : null}
    </div>
  );
}
