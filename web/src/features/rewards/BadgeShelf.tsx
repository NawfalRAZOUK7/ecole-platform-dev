import { useTranslation } from 'react-i18next';
import { EmptyState, space } from '@/shared/ui';
import type { Badge } from './rewards.service';

interface BadgeShelfProps {
  earnedCodes: string[];
  badges: Badge[];
}

function getLocalizedTitle(badge: Badge, language: string) {
  if (language.startsWith('ar')) {
    return badge.titleAr || badge.titleEn || badge.titleFr || badge.code;
  }

  if (language.startsWith('fr')) {
    return badge.titleFr || badge.titleEn || badge.titleAr || badge.code;
  }

  return badge.titleEn || badge.titleFr || badge.titleAr || badge.code;
}

function getLocalizedDescription(badge: Badge, language: string) {
  if (language.startsWith('ar')) {
    return badge.descriptionAr || badge.descriptionEn || badge.descriptionFr || null;
  }

  if (language.startsWith('fr')) {
    return badge.descriptionFr || badge.descriptionEn || badge.descriptionAr || null;
  }

  return badge.descriptionEn || badge.descriptionFr || badge.descriptionAr || null;
}

export function BadgeShelf({ earnedCodes, badges }: BadgeShelfProps) {
  const { t, i18n } = useTranslation();

  if (earnedCodes.length === 0) {
    return <EmptyState message={t('rewards.badgesEmpty')} icon="🏅" />;
  }

  const earnedBadges = earnedCodes.map((code) => {
    const match = badges.find((badge) => badge.code === code);
    return (
      match ?? {
        id: code,
        code,
        titleEn: code,
        titleFr: code,
        titleAr: code,
        descriptionEn: null,
        descriptionFr: null,
        descriptionAr: null,
        icon: null,
        criteriaType: 'manual',
        criteriaValue: 0,
        displayOrder: 0,
        isActive: true,
      }
    );
  });

  return (
    <section className="card" style={{ padding: 20 }}>
      <div style={{ marginBottom: space.base }}>
        <h2 style={{ margin: 0 }}>{t('rewards.badgesEarned')}</h2>
        <p style={{ margin: '6px 0 0', color: 'var(--color-text-secondary)' }}>
          {t('rewards.badgesSubtitle')}
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: space.base,
        }}
      >
        {earnedBadges.map((badge) => (
          <article
            key={badge.id}
            className="card"
            style={{
              padding: space.base,
              display: 'grid',
              gap: space.sm,
              background:
                'linear-gradient(180deg, color-mix(in srgb, var(--kids-star-gold) 18%, transparent) 0%, transparent 100%)',
            }}
          >
            <div style={{ fontSize: 28 }}>{badge.icon || '🏅'}</div>
            <strong>{getLocalizedTitle(badge, i18n.language)}</strong>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>{badge.code}</span>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {getLocalizedDescription(badge, i18n.language) || t('rewards.badgesNoDescription')}
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}
