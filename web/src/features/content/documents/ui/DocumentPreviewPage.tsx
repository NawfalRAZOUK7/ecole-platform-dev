import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useDocumentPreview } from '../model/useDocuments';
import { isImage, isPdf, openSignedUrl } from '../lib/documents.utils';

function isText(mimeType: string) {
  return mimeType.startsWith('text/') || mimeType === 'application/json';
}

export function DocumentPreviewPage() {
  const { docId } = useParams<{ docId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const previewQuery = useDocumentPreview(docId);

  if (previewQuery.isLoading) return <LoadingState />;

  const info = previewQuery.data;

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => void navigate('/documents')}
        >
          ← {t('app.back')}
        </button>
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {info?.original_filename ?? t('documents.preview')}
        </h1>
      </div>

      <ErrorBanner
        error={previewQuery.error instanceof Error ? previewQuery.error.message : null}
        onRetry={() => void previewQuery.refetch()}
      />

      {info && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          {info.download_url && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => openSignedUrl(info.download_url)}
            >
              {t('documents.download')}
            </button>
          )}
          <Link to={`/documents/${docId}/versions`} className="btn btn-secondary">
            {t('documents.versions.title')}
          </Link>
        </div>
      )}

      <div className="card" style={{ minHeight: 400 }}>
        {!info ? (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--color-text-secondary)' }}>
            {t('documents.previewEmpty')}
          </div>
        ) : !info.preview_url ? (
          <div style={{ padding: 32, textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📄</div>
            <p>{t('documents.versions.noPreview')}</p>
            {info.download_url && (
              <button
                type="button"
                className="btn btn-primary"
                style={{ marginTop: 12 }}
                onClick={() => openSignedUrl(info.download_url)}
              >
                {t('documents.download')}
              </button>
            )}
          </div>
        ) : isPdf(info.mime_type) ? (
          <iframe
            src={info.preview_url}
            title={info.original_filename}
            style={{ width: '100%', height: '70vh', border: 'none', borderRadius: 8 }}
          />
        ) : isImage(info.mime_type) ? (
          <div style={{ textAlign: 'center', padding: 16 }}>
            <img
              src={info.preview_url}
              alt={info.original_filename}
              loading="lazy"
              style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain', borderRadius: 8 }}
            />
          </div>
        ) : isText(info.mime_type) ? (
          <iframe
            src={info.preview_url}
            title={info.original_filename}
            style={{
              width: '100%',
              height: '70vh',
              border: 'none',
              borderRadius: 8,
              fontFamily: 'monospace',
            }}
          />
        ) : (
          <div style={{ padding: 32, textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📄</div>
            <p style={{ color: 'var(--color-text-secondary)' }}>{info.mime_type}</p>
            <p style={{ marginTop: 8 }}>{t('documents.versions.noPreview')}</p>
            {info.download_url && (
              <button
                type="button"
                className="btn btn-primary"
                style={{ marginTop: 12 }}
                onClick={() => openSignedUrl(info.download_url)}
              >
                {t('documents.download')}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
