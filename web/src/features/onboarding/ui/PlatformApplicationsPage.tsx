/**
 * PlatformApplicationsPage — SuperAdmin console (SUP only).
 *
 * Reviews onboarding applications: approve (provisions the tenant + returns an
 * invitation code), reject, or request more info.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  applicationsService,
  type ApplicationItem,
  type ApproveResult,
  type ResendActivationResult,
} from '@/features/onboarding/api/applications.api';

const STATUSES = ['pending', 'needs_info', 'approved', 'rejected'] as const;

export function PlatformApplicationsPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [lastApproval, setLastApproval] = useState<ApproveResult | null>(null);
  const [lastResend, setLastResend] = useState<ResendActivationResult | null>(null);

  const listQuery = useQuery({
    queryKey: ['platform-applications', statusFilter],
    queryFn: async () =>
      (await applicationsService.list({ status: statusFilter || undefined })).data,
  });

  const approveMutation = useMutation({
    mutationFn: async (id: string) => (await applicationsService.approve(id)).data,
    onSuccess: (result) => {
      setLastApproval(result);
      void qc.invalidateQueries({ queryKey: ['platform-applications'] });
    },
  });
  const rejectMutation = useMutation({
    mutationFn: async (id: string) => (await applicationsService.reject(id)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['platform-applications'] }),
  });
  const infoMutation = useMutation({
    mutationFn: async (id: string) => (await applicationsService.requestInfo(id)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['platform-applications'] }),
  });
  const resendMutation = useMutation({
    mutationFn: async (id: string) => (await applicationsService.resendActivation(id)).data,
    onSuccess: (result) => {
      setLastResend(result);
      void qc.invalidateQueries({ queryKey: ['platform-applications'] });
    },
  });

  const items = listQuery.data ?? [];

  return (
    <div className="page">
      <h1 className="page-title">Plateforme — Demandes d'inscription</h1>

      {lastApproval && (
        <div
          className="card"
          style={{ padding: 16, marginBottom: 16, borderInlineStart: '4px solid var(--color-success)' }}
        >
          <div>
            <strong>✅ Approuvée.</strong> École créée (<code>{lastApproval.created_school_id}</code>),
            compte propriétaire provisionné, rôle <strong>{lastApproval.role_target}</strong>.
          </div>
          <div style={{ marginTop: 8 }}>
            Un email avec le lien d'activation a été envoyé au demandeur. Lien à communiquer
            si besoin :{' '}
            <a href={lastApproval.activation_url} style={{ wordBreak: 'break-all', fontWeight: 600 }}>
              {lastApproval.activation_url}
            </a>
            <button
              className="btn btn-secondary"
              style={{ marginInlineStart: 12, padding: '2px 10px' }}
              onClick={() => {
                void navigator.clipboard?.writeText(lastApproval.activation_url);
              }}
            >
              Copier
            </button>
          </div>
          <button
            className="btn btn-secondary"
            style={{ marginTop: 8, padding: '2px 10px' }}
            onClick={() => setLastApproval(null)}
          >
            OK
          </button>
        </div>
      )}

      {lastResend && (
        <div
          className="card"
          style={{ padding: 16, marginBottom: 16, borderInlineStart: '4px solid var(--color-primary)' }}
        >
          <div>
            <strong>🔁 Lien d'activation renvoyé.</strong> Un nouvel email a été envoyé ;
            l'ancien lien est désormais invalide.
          </div>
          <div style={{ marginTop: 8 }}>
            Nouveau lien :{' '}
            <a href={lastResend.activation_url} style={{ wordBreak: 'break-all', fontWeight: 600 }}>
              {lastResend.activation_url}
            </a>
            <button
              className="btn btn-secondary"
              style={{ marginInlineStart: 12, padding: '2px 10px' }}
              onClick={() => {
                void navigator.clipboard?.writeText(lastResend.activation_url);
              }}
            >
              Copier
            </button>
          </div>
          <button
            className="btn btn-secondary"
            style={{ marginTop: 8, padding: '2px 10px' }}
            onClick={() => setLastResend(null)}
          >
            OK
          </button>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {STATUSES.map((s) => (
          <button
            key={s}
            className={`btn ${statusFilter === s ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '4px 12px' }}
            onClick={() => setStatusFilter(s)}
          >
            {s}
          </button>
        ))}
      </div>

      {listQuery.isLoading ? (
        <p>Chargement…</p>
      ) : items.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)' }}>Aucune demande.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {items.map((app) => (
            <ApplicationRow
              key={app.id}
              app={app}
              onApprove={() => approveMutation.mutate(app.id)}
              onReject={() => rejectMutation.mutate(app.id)}
              onRequestInfo={() => infoMutation.mutate(app.id)}
              onResendActivation={() => resendMutation.mutate(app.id)}
              busy={
                approveMutation.isPending ||
                rejectMutation.isPending ||
                infoMutation.isPending ||
                resendMutation.isPending
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ApplicationRow({
  app,
  onApprove,
  onReject,
  onRequestInfo,
  onResendActivation,
  busy,
}: {
  app: ApplicationItem;
  onApprove: () => void;
  onReject: () => void;
  onRequestInfo: () => void;
  onResendActivation: () => void;
  busy: boolean;
}) {
  const isFormal = app.application_type === 'formal_school';
  const pending = app.status === 'pending' || app.status === 'needs_info';
  const approved = app.status === 'approved';
  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div>
          <div style={{ fontWeight: 700 }}>
            {isFormal ? '🏫' : '🏡'} {app.org_name}
          </div>
          <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
            {app.applicant_name} · {app.applicant_email}
            {app.applicant_phone ? ` · ${app.applicant_phone}` : ''}
            {app.city ? ` · ${app.city}` : ''}
          </div>
          {app.notes && <p style={{ fontSize: 13, marginBottom: 0 }}>{app.notes}</p>}
        </div>
        <span className="status-badge" style={{ textTransform: 'uppercase' }}>
          {app.status}
        </span>
      </div>

      {pending && (
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button className="btn btn-primary" style={{ padding: '4px 12px' }} disabled={busy} onClick={onApprove}>
            Approuver
          </button>
          <button className="btn btn-secondary" style={{ padding: '4px 12px' }} disabled={busy} onClick={onRequestInfo}>
            Demander infos
          </button>
          <button className="btn btn-danger" style={{ padding: '4px 12px' }} disabled={busy} onClick={onReject}>
            Rejeter
          </button>
        </div>
      )}

      {approved && (
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button
            className="btn btn-secondary"
            style={{ padding: '4px 12px' }}
            disabled={busy}
            onClick={onResendActivation}
            title="Renvoyer le lien d'activation si l'ancien a expiré"
          >
            🔁 Renvoyer le lien d'activation
          </button>
        </div>
      )}
    </div>
  );
}
