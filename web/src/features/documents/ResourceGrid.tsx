import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import type { ResourceItem } from './documents.service';

interface ResourceGridProps {
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  onFetchNextPage: () => void;
  onSelectResource: (resourceId: string) => void;
  resources: ResourceItem[];
}

export function ResourceGrid({ hasNextPage, isFetchingNextPage, onFetchNextPage, onSelectResource, resources }: ResourceGridProps) {
  const { t } = useTranslation();

  return (
    <>
      {resources.length === 0 ? (
        <EmptyState message={t('documents.resources.empty')} icon="📚" />
      ) : (
        <div className="documents-resource-grid">
          {resources.map((resource) => (
            <button key={resource.id} type="button" className="documents-resource-card" onClick={() => onSelectResource(resource.id)}>
              {resource.thumbnail_url ? <img src={resource.thumbnail_url} alt={resource.title} className="documents-resource-card__thumb" /> : <div className="documents-resource-card__thumb documents-resource-card__thumb--empty">📄</div>}
              <div>
                <strong>{resource.title}</strong>
                <p>{[resource.subject, resource.level].filter(Boolean).join(' · ')}</p>
                <span>{t('documents.resources.rating', { rating: resource.avg_rating.toFixed(1), count: resource.rating_count })}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {hasNextPage && (
        <button type="button" className="btn btn-secondary" onClick={onFetchNextPage} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? t('documents.uploading') : t('documents.resources.loadMore')}
        </button>
      )}
    </>
  );
}
