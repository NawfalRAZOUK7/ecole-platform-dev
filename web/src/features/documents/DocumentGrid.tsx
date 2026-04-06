import { useTranslation } from 'react-i18next';
import { formatDate } from '@/shared/i18n';
import type { DocumentItem } from './documents.service';
import type { DocumentViewMode } from './documents.types';
import { humanSize, isImage, isPdf } from './documents.utils';

interface DocumentGridProps {
  documents: DocumentItem[];
  onDelete: (documentId: string) => void;
  onDownload: (url: string | null) => void;
  onPreview: (item: DocumentItem) => void;
  onToggleSelection: (documentId: string) => void;
  selectedDocumentIds: string[];
  viewMode: DocumentViewMode;
}

export function DocumentGrid({ documents, onDelete, onDownload, onPreview, onToggleSelection, selectedDocumentIds, viewMode }: DocumentGridProps) {
  const { t, i18n } = useTranslation();

  return (
    <div className={`documents-collection documents-collection--${viewMode}`}>
      {documents.map((item) => (
        <article key={item.id} className="documents-card">
          <label className="documents-card__select"><input type="checkbox" checked={selectedDocumentIds.includes(item.id)} onChange={() => onToggleSelection(item.id)} /></label>
          <button type="button" className="documents-card__preview" onClick={() => onPreview(item)}>
            {item.thumbnail_url ? <img src={item.thumbnail_url} alt={item.original_filename} loading="lazy" /> : <span>{isPdf(item.mime_type) ? '📕' : isImage(item.mime_type) ? '🖼️' : '📄'}</span>}
          </button>
          <div className="documents-card__body">
            <strong>{item.original_filename}</strong>
            <p>{humanSize(item.size_bytes)} · {item.mime_type}</p>
            <div className="documents-card__meta">
              <span className="status-badge">{t(`documents.categories.${item.category}`)}</span>
              {item.is_expired && <span className="status-badge status-expired">{t('documents.expired')}</span>}
              {!item.is_expired && item.is_expiring_soon && <span className="status-badge status-warning">{t('documents.expiringSoon')}</span>}
            </div>
            <span>{formatDate(item.created_at, i18n.language, { dateStyle: 'medium', timeStyle: 'short' })}</span>
          </div>
          <div className="documents-card__actions">
            {item.preview_url && <button type="button" className="dropdown-link" onClick={() => onPreview(item)}>{t('documents.preview')}</button>}
            <button type="button" className="dropdown-link" onClick={() => onDownload(item.download_url)}>{t('documents.download')}</button>
            {item.can_delete && <button type="button" className="dropdown-link" onClick={() => onDelete(item.id)}>{t('documents.delete')}</button>}
          </div>
        </article>
      ))}
    </div>
  );
}
