import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { rewardsQueryKeys } from '@/features/rewards/useRewards';
import { rewardsService, type Badge as RewardBadge } from '@/services/rewards.service';
import { Badge, EmptyState, ErrorBanner, LoadingState, space } from '@/shared/ui';
import { BadgeEditor } from './BadgeEditor';

function getLocalizedBadgeTitle(badge: RewardBadge, language: string) {
  if (language.startsWith('ar')) {
    return badge.titleAr || badge.titleEn || badge.titleFr || badge.code;
  }

  if (language.startsWith('fr')) {
    return badge.titleFr || badge.titleEn || badge.titleAr || badge.code;
  }

  return badge.titleEn || badge.titleFr || badge.titleAr || badge.code;
}

function isImageLike(icon: string | null) {
  if (!icon) {
    return false;
  }

  return (
    icon.startsWith('data:image/') ||
    icon.startsWith('http://') ||
    icon.startsWith('https://') ||
    icon.startsWith('/')
  );
}

export function BadgesPage() {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [pageError, setPageError] = useState<string | null>(null);
  const [editingBadge, setEditingBadge] = useState<RewardBadge | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [orderDrafts, setOrderDrafts] = useState<Record<string, number>>({});

  const badgesQuery = useQuery({
    queryKey: rewardsQueryKeys.badges(),
    queryFn: async () => rewardsService.getBadges(),
  });

  useEffect(() => {
    if (!badgesQuery.data) {
      return;
    }

    setOrderDrafts(
      Object.fromEntries(badgesQuery.data.map((badge) => [badge.id, badge.displayOrder])),
    );
  }, [badgesQuery.data]);

  const updateMutation = useMutation({
    mutationFn: async ({ badgeId, data }: { badgeId: string; data: Partial<RewardBadge> }) =>
      rewardsService.updateBadge(badgeId, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: rewardsQueryKeys.badges() });
      setPageError(null);
    },
    onError: (error) => {
      setPageError(error instanceof Error ? error.message : t('app.error'));
    },
  });

  const badges = useMemo(
    () =>
      [...(badgesQuery.data ?? [])].sort(
        (left, right) =>
          left.displayOrder - right.displayOrder || left.code.localeCompare(right.code),
      ),
    [badgesQuery.data],
  );

  if (badgesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('admin.badges.title')}</h1>
          <p className="page-subtitle">{t('admin.badges.subtitle')}</p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => {
            setIsCreating(true);
            setEditingBadge(null);
          }}
        >
          {t('admin.badges.create')}
        </button>
      </div>

      <ErrorBanner
        error={pageError ?? (badgesQuery.error instanceof Error ? badgesQuery.error.message : null)}
        onDismiss={() => setPageError(null)}
        onRetry={badgesQuery.error ? () => void badgesQuery.refetch() : undefined}
      />

      {badges.length === 0 ? (
        <EmptyState message={t('admin.badges.empty')} icon="🏅" />
      ) : (
        <div className="data-table__scroll">
          <table className="data-table" aria-label={t('admin.badges.title')}>
            <thead className="data-table__head">
              <tr className="data-table__header-row">
                <th className="data-table__header" scope="col">
                  {t('admin.badges.columns.icon')}
                </th>
                <th className="data-table__header" scope="col">
                  {t('admin.badges.columns.code')}
                </th>
                <th className="data-table__header" scope="col">
                  {t('admin.badges.columns.title')}
                </th>
                <th className="data-table__header" scope="col">
                  {t('admin.badges.columns.criteria')}
                </th>
                <th className="data-table__header" scope="col">
                  {t('admin.badges.columns.displayOrder')}
                </th>
                <th className="data-table__header" scope="col">
                  {t('admin.badges.columns.active')}
                </th>
                <th className="data-table__header" scope="col">
                  {t('app.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="data-table__body">
              {badges.map((badge) => {
                const orderDraft = orderDrafts[badge.id] ?? badge.displayOrder;
                const orderChanged = orderDraft !== badge.displayOrder;

                return (
                  <tr key={badge.id} className="data-table__row">
                    <td className="data-table__cell">
                      {badge.icon ? (
                        isImageLike(badge.icon) ? (
                          <img
                            src={badge.icon}
                            alt={badge.code}
                            style={{
                              width: 44,
                              height: 44,
                              objectFit: 'cover',
                              borderRadius: 12,
                              border: '1px solid var(--color-border)',
                            }}
                          />
                        ) : (
                          <span style={{ fontSize: 28 }}>{badge.icon}</span>
                        )
                      ) : (
                        <span style={{ fontSize: 28 }}>🏅</span>
                      )}
                    </td>
                    <td className="data-table__cell">
                      <code>{badge.code}</code>
                    </td>
                    <td className="data-table__cell">
                      <div style={{ fontWeight: 600 }}>
                        {getLocalizedBadgeTitle(badge, i18n.language)}
                      </div>
                    </td>
                    <td className="data-table__cell">
                      {t(`admin.badges.criteriaTypes.${badge.criteriaType}`, {
                        defaultValue: badge.criteriaType,
                      })}
                      {`: ${badge.criteriaValue}`}
                    </td>
                    <td className="data-table__cell">
                      <div
                        style={{
                          display: 'flex',
                          gap: space.sm,
                          alignItems: 'center',
                          flexWrap: 'wrap',
                        }}
                      >
                        <input
                          type="number"
                          className="filter-input"
                          min="0"
                          style={{ width: 92 }}
                          value={orderDraft}
                          onChange={(event) => {
                            const parsed = Number(event.target.value);
                            setOrderDrafts((current) => ({
                              ...current,
                              [badge.id]: Number.isNaN(parsed) ? badge.displayOrder : parsed,
                            }));
                          }}
                        />
                        {orderChanged ? (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            disabled={updateMutation.isPending}
                            onClick={() =>
                              void updateMutation.mutateAsync({
                                badgeId: badge.id,
                                data: { displayOrder: orderDraft },
                              })
                            }
                          >
                            {t('admin.badges.saveOrder')}
                          </button>
                        ) : null}
                      </div>
                    </td>
                    <td className="data-table__cell">
                      <div
                        style={{
                          display: 'flex',
                          gap: space.sm,
                          alignItems: 'center',
                          flexWrap: 'wrap',
                        }}
                      >
                        <Badge variant={badge.isActive ? 'success' : 'neutral'}>
                          {t(
                            badge.isActive
                              ? 'admin.badges.status.active'
                              : 'admin.badges.status.inactive',
                          )}
                        </Badge>
                        <label className="switch-field">
                          <input
                            type="checkbox"
                            checked={badge.isActive}
                            disabled={updateMutation.isPending}
                            onChange={(event) =>
                              void updateMutation.mutateAsync({
                                badgeId: badge.id,
                                data: { isActive: event.target.checked },
                              })
                            }
                          />
                          <span>{t('admin.badges.toggle')}</span>
                        </label>
                      </div>
                    </td>
                    <td className="data-table__cell">
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setEditingBadge(badge);
                          setIsCreating(false);
                        }}
                      >
                        {t('app.edit')}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {(isCreating || editingBadge) && (
        <div
          className="modal-overlay"
          onClick={() => {
            setIsCreating(false);
            setEditingBadge(null);
          }}
        >
          <div
            className="modal-card"
            onClick={(event) => event.stopPropagation()}
            style={{ maxWidth: 760 }}
          >
            <BadgeEditor
              badge={editingBadge}
              onCancel={() => {
                setIsCreating(false);
                setEditingBadge(null);
              }}
              onSaved={() => {
                setIsCreating(false);
                setEditingBadge(null);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
