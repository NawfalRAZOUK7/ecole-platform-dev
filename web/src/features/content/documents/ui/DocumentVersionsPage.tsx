import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';
import { useDocumentVersions, useRestoreVersion } from '../model/useDocuments';
import { humanSize, openSignedUrl } from '../lib/documents.utils';

export function DocumentVersionsPage() {
  const { docId } = useParams<{ docId: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const versionsQuery = useDocumentVersions(docId);
  const restoreMutation = useRestoreVersion();
  const [confirmVersion, setConfirmVersion] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const versions = versionsQuery.data ?? [];

  async function handleRestore(versionNum: number) {
    if (!docId) return;
    setError(null);
    try {
      await restoreMutation.mutateAsync({ docId, versionNum });
      setConfirmVersion(null);
      await versionsQuery.refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (versionsQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => void navigate('/documents')}
        >
          ← {t('app.back')}
        </button>
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {t('documents.versions.title')}
        </h1>
      </div>

      <ErrorBanner
        error={error || (versionsQuery.error instanceof Error ? versionsQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void versionsQuery.refetch()}
      />

      {versions.length === 0 ? (
        <EmptyState message={t('documents.versions.empty')} icon="📄" />
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('documents.versions.version')}</th>
                <th>{t('documents.versions.date')}</th>
                <th>{t('documents.versions.author')}</th>
                <th>{t('documents.versions.size')}</th>
                <th>{t('app.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((version, index) => (
                <tr key={version.version_number}>
                  <td>
                    <strong>v{version.version_number}</strong>
                    {index === 0 && (
                      <span
                        style={{
                          marginLeft: 8,
                          fontSize: 11,
                          background: 'var(--color-primary)',
                          color: 'var(--color-inverse-text)',
                          borderRadius: 4,
                          padding: '1px 6px',
                        }}
                      >
                        {t('documents.versions.current')}
                      </span>
                    )}
                  </td>
                  <td>{formatDate(version.created_at, i18n.language, { dateStyle: 'medium' })}</td>
                  <td>{version.author_name ?? '—'}</td>
                  <td>{humanSize(version.size_bytes)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {version.preview_url && (
                        <Link
                          to={`/documents/${docId}/preview?v=${version.version_number}`}
                          className="btn btn-sm btn-secondary"
                        >
                          {t('documents.preview')}
                        </Link>
                      )}
                      {version.download_url && (
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => openSignedUrl(version.download_url)}
                        >
                          {t('documents.download')}
                        </button>
                      )}
                      {index > 0 && (
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          disabled={restoreMutation.isPending}
                          onClick={() => setConfirmVersion(version.version_number)}
                        >
                          {t('documents.versions.restore')}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {confirmVersion !== null && (
        <div className="modal-overlay" onClick={() => setConfirmVersion(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 12 }}>{t('documents.versions.confirmRestoreTitle')}</h2>
            <p style={{ marginBottom: 20 }}>
              {t('documents.versions.confirmRestoreBody', { version: confirmVersion })}
            </p>
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={restoreMutation.isPending}
                onClick={() => void handleRestore(confirmVersion)}
              >
                {restoreMutation.isPending ? t('app.loading') : t('documents.versions.restore')}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmVersion(null)}
              >
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
