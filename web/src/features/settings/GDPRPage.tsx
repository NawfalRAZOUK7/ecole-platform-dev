import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { formatDate } from '@/shared/i18n';
import { Badge, ConfirmDialog, EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { gdprService, type CurrentConsentEntry } from './gdpr.service';

function downloadExport(payload: Record<string, unknown>, userId: string) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `gdpr-export-${userId}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function getConsentVariant(status: CurrentConsentEntry['status']) {
  return status === 'opted_in' ? 'success' : 'warning';
}

export function GDPRPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [exportedAt, setExportedAt] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  const consentLogQuery = useQuery({
    queryKey: ['gdpr', user?.id],
    queryFn: async () => (await gdprService.getConsentLog(user!.id)).data,
    enabled: Boolean(user?.id),
  });

  const exportMutation = useMutation({
    mutationFn: async () => (await gdprService.getDataExport(user!.id)).data,
    onSuccess: (payload) => {
      downloadExport(payload, user!.id);
      setExportedAt(new Date().toISOString());
    },
    onError: (error) => setPageError(error instanceof Error ? error.message : t('app.error')),
  });

  const deleteMutation = useMutation({
    mutationFn: async () => (await gdprService.requestDataDeletion(user!.id)).data,
    onSuccess: () => setDeleteOpen(false),
    onError: (error) => {
      setDeleteOpen(false);
      setPageError(error instanceof Error ? error.message : t('app.error'));
    },
  });

  const consentRows = consentLogQuery.data?.current_consents ?? [];
  const recentHistory = useMemo(
    () => (consentLogQuery.data?.change_history ?? []).slice(0, 5),
    [consentLogQuery.data]
  );

  if (!user) {
    return null;
  }

  if (consentLogQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('gdpr.title')}</h1>
        <p className="page-subtitle">{t('gdpr.subtitle')}</p>
      </div>

      <ErrorBanner
        error={pageError ?? (consentLogQuery.error instanceof Error ? consentLogQuery.error.message : null)}
        onDismiss={() => setPageError(null)}
        onRetry={consentLogQuery.error ? () => void consentLogQuery.refetch() : undefined}
      />

      <section className="card settings-card">
        <div className="settings-card__header">
          <h2>{t('gdpr.export.title')}</h2>
          <p>{t('gdpr.export.description')}</p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => void exportMutation.mutateAsync()}
          disabled={exportMutation.isPending}
        >
          {exportMutation.isPending ? t('app.loading') : t('gdpr.export.action')}
        </button>
        {exportedAt && (
          <p className="save-state save-state--success">
            {t('gdpr.export.success', { date: formatDate(exportedAt) })}
          </p>
        )}
      </section>

      <section className="card settings-card">
        <div className="settings-card__header">
          <h2>{t('gdpr.deletion.title')}</h2>
          <p>{t('gdpr.deletion.description')}</p>
        </div>
        {deleteMutation.data ? (
          <p className="save-state save-state--success">
            {t('gdpr.deletion.success', { message: deleteMutation.data.message })}
          </p>
        ) : null}
        <button type="button" className="btn btn-danger" onClick={() => setDeleteOpen(true)}>
          {t('gdpr.deletion.action')}
        </button>
      </section>

      <section className="card settings-card">
        <div className="settings-card__header">
          <h2>{t('gdpr.consent.title')}</h2>
          <p>{t('gdpr.consent.subtitle')}</p>
        </div>

        {consentRows.length === 0 ? (
          <EmptyState message={t('gdpr.consent.empty')} />
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('gdpr.consent.topic')}</th>
                  <th>{t('gdpr.consent.channel')}</th>
                  <th>{t('gdpr.consent.scope')}</th>
                  <th>{t('gdpr.consent.status')}</th>
                </tr>
              </thead>
              <tbody>
                {consentRows.map((consent) => (
                  <tr key={consent.id}>
                    <td>{consent.topic}</td>
                    <td>{consent.channel}</td>
                    <td>{consent.scope_type}</td>
                    <td>
                      <Badge variant={getConsentVariant(consent.status)}>
                        {t(`gdpr.status.${consent.status}`)}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <h3 style={{ marginTop: 20, marginBottom: 12 }}>{t('gdpr.history.title')}</h3>
        {recentHistory.length === 0 ? (
          <EmptyState message={t('gdpr.history.empty')} />
        ) : (
          <div style={{ display: 'grid', gap: 12 }}>
            {recentHistory.map((entry) => (
              <div key={entry.id} className="card" style={{ padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 6 }}>
                  <strong>{entry.action_type}</strong>
                  <Badge variant={entry.outcome === 'success' ? 'success' : 'warning'}>{entry.outcome}</Badge>
                </div>
                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                  {t('gdpr.history.meta', {
                    actor: entry.actor_id || 'system',
                    ip: entry.ip_address || 'n/a',
                    date: formatDate(entry.created_at),
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <ConfirmDialog
        open={deleteOpen}
        title="gdpr.deletion.confirmTitle"
        message="gdpr.deletion.confirmBody"
        confirmLabel="gdpr.deletion.confirmAction"
        variant="danger"
        loading={deleteMutation.isPending}
        onCancel={() => setDeleteOpen(false)}
        onConfirm={() => void deleteMutation.mutateAsync()}
      />
    </div>
  );
}
