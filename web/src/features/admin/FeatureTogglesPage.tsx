import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { Badge, DataTable, EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { featuresService, type FeatureToggle } from './features.service';

type FeatureToggleRow = FeatureToggle & Record<string, unknown>;

const QUERY_KEY = ['admin', 'feature-toggles'] as const;

export function FeatureTogglesPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<FeatureToggle | null>(null);
  const [draft, setDraft] = useState({ display_name: '', description: '', roleCodes: '', schoolIds: '' });
  const [pageError, setPageError] = useState<string | null>(null);

  const togglesQuery = useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => (await featuresService.listFeatures()).data,
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      toggleId,
      payload,
    }: {
      toggleId: string;
      payload: Parameters<typeof featuresService.updateFeature>[1];
    }) => (await featuresService.updateFeature(toggleId, payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      setEditing(null);
    },
    onError: (error) => setPageError(error instanceof Error ? error.message : t('app.error')),
  });

  const columns: ColumnDef<FeatureToggleRow>[] = useMemo(
    () => [
      {
        key: 'feature_key',
        header: 'featureToggles.columns.key',
        render: (value) => <code>{String(value)}</code>,
      },
      { key: 'display_name', header: 'featureToggles.columns.name' },
      {
        key: 'description',
        header: 'featureToggles.columns.description',
        render: (value) => String(value || '—'),
      },
      {
        key: 'enabled_globally',
        header: 'featureToggles.columns.status',
        render: (value) => (
          <Badge variant={value ? 'success' : 'neutral'}>
            {t(value ? 'featureToggles.enabled' : 'featureToggles.disabled')}
          </Badge>
        ),
      },
      {
        key: 'id',
        header: 'app.actions',
        sortable: false,
        render: (_value, row) => (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <label className="switch-field">
              <input
                type="checkbox"
                checked={row.enabled_globally}
                aria-label={t('featureToggles.toggleAria', { name: row.display_name })}
                onChange={(event) =>
                  void updateMutation.mutateAsync({
                    toggleId: row.id,
                    payload: { enabled_globally: event.target.checked },
                  })
                }
              />
              <span>{row.enabled_globally ? t('featureToggles.on') : t('featureToggles.off')}</span>
            </label>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setEditing(row);
                setDraft({
                  display_name: row.display_name,
                  description: row.description || '',
                  roleCodes: row.enabled_role_codes.join(', '),
                  schoolIds: row.enabled_school_ids.join(', '),
                });
              }}
            >
              {t('app.edit')}
            </button>
          </div>
        ),
      },
    ],
    [t, updateMutation]
  );

  if (togglesQuery.isLoading) {
    return <LoadingState />;
  }

  const toggles = togglesQuery.data ?? [];

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('featureToggles.title')}</h1>
        <p className="page-subtitle">{t('featureToggles.subtitle')}</p>
      </div>

      <ErrorBanner
        error={pageError ?? (togglesQuery.error instanceof Error ? togglesQuery.error.message : null)}
        onDismiss={() => setPageError(null)}
        onRetry={togglesQuery.error ? () => void togglesQuery.refetch() : undefined}
      />

      {toggles.length === 0 ? (
        <EmptyState message={t('featureToggles.empty')} />
      ) : (
        <DataTable
          columns={columns}
          data={toggles as FeatureToggleRow[]}
          loading={false}
          emptyMessage="featureToggles.empty"
          ariaLabel={t('featureToggles.title')}
        />
      )}

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()} style={{ maxWidth: 520 }}>
            <h2 style={{ marginBottom: 16 }}>{t('featureToggles.editTitle')}</h2>
            <label className="form-field">
              <span>{t('featureToggles.columns.name')}</span>
              <input className="input" value={draft.display_name} onChange={(event) => setDraft((current) => ({ ...current, display_name: event.target.value }))} />
            </label>
            <label className="form-field">
              <span>{t('featureToggles.columns.description')}</span>
              <textarea className="input" rows={3} value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} />
            </label>
            <label className="form-field">
              <span>{t('featureToggles.columns.roles')}</span>
              <input className="input" value={draft.roleCodes} onChange={(event) => setDraft((current) => ({ ...current, roleCodes: event.target.value }))} placeholder="ADM, TCH" />
            </label>
            <label className="form-field">
              <span>{t('featureToggles.columns.schools')}</span>
              <input className="input" value={draft.schoolIds} onChange={(event) => setDraft((current) => ({ ...current, schoolIds: event.target.value }))} placeholder="school-1, school-2" />
            </label>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button type="button" className="btn btn-secondary" onClick={() => setEditing(null)}>
                {t('app.cancel')}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={updateMutation.isPending}
                onClick={() =>
                  void updateMutation.mutateAsync({
                    toggleId: editing.id,
                    payload: {
                      display_name: draft.display_name.trim(),
                      description: draft.description.trim() || null,
                      enabled_role_codes: draft.roleCodes.split(',').map((value) => value.trim()).filter(Boolean),
                      enabled_school_ids: draft.schoolIds.split(',').map((value) => value.trim()).filter(Boolean),
                    },
                  })
                }
              >
                {updateMutation.isPending ? t('app.loading') : t('app.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
