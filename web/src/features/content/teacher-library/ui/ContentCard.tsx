import { useTranslation } from 'react-i18next';
import type { ContentCardProps } from '../model/content-library.types';

export function ContentCard({
  item,
  reviewPending,
  onAssign,
  onSubmitForReview,
}: ContentCardProps) {
  const { t } = useTranslation();

  return (
    <div className="card" style={{ padding: 16 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 8,
        }}
      >
        <h4 style={{ margin: 0, fontSize: 14 }}>{item.title}</h4>
        <span className="badge" style={{ fontSize: 11 }}>
          {item.content_type}
        </span>
      </div>
      {item.description && (
        <p
          style={{
            fontSize: 12,
            color: 'var(--color-text-secondary)',
            margin: '0 0 8px',
            lineHeight: 1.4,
          }}
        >
          {item.description.length > 100
            ? `${item.description.slice(0, 100)}...`
            : item.description}
        </p>
      )}
      <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
        {item.subject && (
          <span style={{ marginRight: 8 }}>{t(`cms.subjects.${item.subject}`, item.subject)}</span>
        )}
        {item.level_band && <span style={{ marginRight: 8 }}>{item.level_band}</span>}
        <span>{t(`cms.origins.${item.origin}`, item.origin)}</span>
      </div>
      <div style={{ display: 'flex', gap: 6 }}>
        {onAssign && (
          <button
            className="btn btn-primary"
            style={{ fontSize: 12, padding: '4px 10px' }}
            onClick={() => onAssign(item)}
          >
            {t('teacherContent.assignToClass')}
          </button>
        )}
        {item.school_id && (
          <button
            className="btn btn-secondary"
            style={{ fontSize: 12, padding: '4px 10px' }}
            onClick={() => onSubmitForReview(item.id)}
            disabled={reviewPending}
          >
            {reviewPending ? t('app.loading') : t('teacherContent.submitForReview')}
          </button>
        )}
      </div>
    </div>
  );
}
