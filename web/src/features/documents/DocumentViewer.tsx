import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import type { DocumentItem, ResourceItem } from './documents.service';
import { humanSize, isImage, isPdf } from './documents.utils';

interface DocumentViewerProps {
  isResourceLoading: boolean;
  previewItem: DocumentItem | null;
  selectedResource: ResourceItem | null;
  onCloseResource: () => void;
  onDownload: (url: string | null) => void;
  onRateResource: (resourceId: string, rating: number) => void;
}

export function DocumentViewer({
  isResourceLoading,
  previewItem,
  selectedResource,
  onCloseResource,
  onDownload,
  onRateResource,
}: DocumentViewerProps) {
  const { t, i18n } = useTranslation();

  return (
    <>
      <aside className="card documents-preview-card">
        <h2>{t('documents.previewPanelTitle')}</h2>
        {!previewItem ? (
          <EmptyState message={t('documents.previewEmpty')} icon="🔎" />
        ) : (
          <div className="documents-preview-card__content">
            <strong>{previewItem.original_filename}</strong>
            {previewItem.preview_url && isImage(previewItem.mime_type) && <img src={previewItem.preview_url} alt={previewItem.original_filename} className="documents-preview-card__image" />}
            {previewItem.preview_url && isPdf(previewItem.mime_type) && <iframe src={previewItem.preview_url} title={previewItem.original_filename} className="documents-preview-card__frame" />}
            {!previewItem.preview_url && <div className="documents-preview-card__fallback">📄</div>}
            <p>{previewItem.mime_type}</p>
            <p>{humanSize(previewItem.size_bytes)}</p>
            {previewItem.expires_at && <p>{t('documents.expiresAt')}: {formatDate(previewItem.expires_at, i18n.language, { dateStyle: 'medium' })}</p>}
            <button type="button" className="btn btn-primary" onClick={() => onDownload(previewItem.download_url)}>{t('documents.download')}</button>
          </div>
        )}
      </aside>

      {selectedResource && (
        <div className="calendar-modal-shell" role="dialog" aria-modal="true">
          <div className="calendar-modal-card documents-resource-modal">
            <div className="calendar-modal-card__header">
              <h2>{selectedResource.title}</h2>
              <button type="button" className="btn btn-secondary" onClick={onCloseResource}>{t('app.close')}</button>
            </div>
            {isResourceLoading ? (
              <LoadingState />
            ) : (
              <>
                {selectedResource.preview_url && selectedResource.document && 'mime_type' in selectedResource.document && isImage(selectedResource.document.mime_type) && <img src={selectedResource.preview_url} alt={selectedResource.title} className="documents-resource-modal__image" />}
                {selectedResource.preview_url && selectedResource.document && 'mime_type' in selectedResource.document && isPdf(selectedResource.document.mime_type) && <iframe src={selectedResource.preview_url} title={selectedResource.title} className="documents-resource-modal__frame" />}
                <p>{selectedResource.description || '—'}</p>
                <p>{[selectedResource.subject, selectedResource.level].filter(Boolean).join(' · ') || '—'}</p>
                <p>{selectedResource.author || '—'}</p>
                <p>{selectedResource.tags.join(', ') || '—'}</p>
                <p>{t('documents.resources.rating', { rating: selectedResource.avg_rating.toFixed(1), count: selectedResource.rating_count })}</p>
                <p>{t('documents.download', 'Download')} · {selectedResource.download_count}</p>
                <p>{formatDate(selectedResource.created_at, i18n.language, { dateStyle: 'medium' })}</p>
                {selectedResource.document && 'mime_type' in selectedResource.document && <p>{selectedResource.document.mime_type} · {humanSize(selectedResource.document.size_bytes)}</p>}
                <div className="calendar-modal-card__actions">
                  <button type="button" className="btn btn-primary" onClick={() => onDownload(selectedResource.download_url)}>{t('documents.download')}</button>
                  {selectedResource.can_rate && (
                    <div className="documents-rating-group">
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <button key={rating} type="button" className={`btn ${selectedResource.my_rating === rating ? 'btn-primary' : 'btn-secondary'}`} onClick={() => onRateResource(selectedResource.id, rating)}>
                          {rating}★
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
