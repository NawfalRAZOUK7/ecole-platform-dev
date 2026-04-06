/**
 * Admin batch registration page — CSV upload for bulk account creation.
 *
 * Reference: Phase 4D — Registration & Profile UI (Web)
 * Cascading from Phase 2C (POST /admin/register-batch).
 * ADM-only route. Parses CSV, shows preview table, submits to backend.
 */

import { useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useAdminBatchRegister } from './useAdmin';
import type { BatchResult, CsvRow } from './admin.service';

function parseCsv(text: string): CsvRow[] {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];

  const header = lines[0].toLowerCase().split(',').map((h) => h.trim());
  const emailIdx = header.indexOf('email');
  const nameIdx = header.findIndex((h) => h === 'full_name' || h === 'name' || h === 'nom');
  const roleIdx = header.findIndex((h) => h === 'role' || h === 'role_code');
  const phoneIdx = header.findIndex((h) => h === 'phone' || h === 'telephone');
  const classIdx = header.findIndex((h) => h === 'class' || h === 'class_code' || h === 'classe');

  if (emailIdx === -1 || nameIdx === -1 || roleIdx === -1) return [];

  const rows: CsvRow[] = [];
  for (let i = 1; i < lines.length; i += 1) {
    const cols = lines[i].split(',').map((c) => c.trim());
    if (!cols[emailIdx] || !cols[nameIdx] || !cols[roleIdx]) continue;
    rows.push({
      email: cols[emailIdx],
      full_name: cols[nameIdx],
      role: cols[roleIdx].toUpperCase(),
      phone: phoneIdx >= 0 ? cols[phoneIdx] : undefined,
      class_code: classIdx >= 0 ? cols[classIdx] : undefined,
    });
  }
  return rows;
}

export function BatchRegisterPage() {
  const { t } = useTranslation();
  const batchRegisterMutation = useAdminBatchRegister();
  const [rows, setRows] = useState<CsvRow[]>([]);
  const [localError, setLocalError] = useState<string | null>(null);
  const [result, setResult] = useState<BatchResult | null>(null);
  const [fileName, setFileName] = useState('');

  const dismissibleError = useDismissibleError(
    useMemo(
      () => localError ?? toBannerError(batchRegisterMutation.error, t('app.error')),
      [batchRegisterMutation.error, localError, t]
    )
  );

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setLocalError(null);
    setResult(null);
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setLocalError(t('register.csvInvalidFormat'));
      return;
    }

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (loadEvent) => {
      const text = loadEvent.target?.result as string;
      const parsed = parseCsv(text);
      if (parsed.length === 0) {
        setLocalError(t('register.csvEmpty'));
        return;
      }
      if (parsed.length > 100) {
        setLocalError(t('register.csvTooMany'));
        return;
      }
      setRows(parsed);
    };
    reader.readAsText(file);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (rows.length === 0) return;

    setLocalError(null);
    const batchResult = await batchRegisterMutation.mutateAsync(rows);
    setResult(batchResult);
    setRows([]);
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('register.batchTitle')}</h1>

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />

      <div className="card" style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
          {t('register.batchInstructions')}
        </p>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 12, fontFamily: 'monospace' }}>
          email,full_name,role,phone,class_code
        </p>

        <input type="file" accept=".csv" onChange={handleFileChange} style={{ marginBottom: 12 }} />
        {fileName && <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{fileName}</span>}
      </div>

      {rows.length > 0 && !result && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
            {t('register.batchPreview')} ({rows.length})
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('register.email')}</th>
                  <th>{t('register.fullName')}</th>
                  <th>{t('admin.users.role')}</th>
                  <th>{t('register.phone')}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={`${row.email}-${index}`}>
                    <td>{row.email}</td>
                    <td>{row.full_name}</td>
                    <td><span className="role-badge">{row.role}</span></td>
                    <td>{row.phone || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <form onSubmit={handleSubmit} style={{ marginTop: 12 }}>
            <button type="submit" className="btn btn-primary" disabled={batchRegisterMutation.isPending}>
              {batchRegisterMutation.isPending ? t('app.loading') : t('register.batchSubmit')}
            </button>
          </form>
        </div>
      )}

      {batchRegisterMutation.isPending && <LoadingState />}

      {result && (
        <div className="card" role="status" aria-live="polite">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
            {t('register.batchResults')}
          </h3>

          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <div style={{ padding: 12, background: 'var(--color-surface-success)', borderRadius: 'var(--radius)', flex: 1 }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-success)' }}>{result.total_created}</div>
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('register.batchCreated')}</div>
            </div>
            {result.total_errors > 0 && (
              <div style={{ padding: 12, background: 'var(--color-surface-error)', borderRadius: 'var(--radius)', flex: 1 }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-danger)' }}>{result.total_errors}</div>
                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('register.batchErrors')}</div>
              </div>
            )}
          </div>

          {result.created.length > 0 && (
            <div style={{ overflowX: 'auto', marginBottom: 12 }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('register.email')}</th>
                    <th>{t('register.fullName')}</th>
                    <th>{t('admin.users.role')}</th>
                    <th>{t('register.tempPassword')}</th>
                  </tr>
                </thead>
                <tbody>
                  {result.created.map((user) => (
                    <tr key={user.user_id}>
                      <td>{user.email}</td>
                      <td>{user.full_name}</td>
                      <td><span className="role-badge">{user.role}</span></td>
                      <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{user.temp_password}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.errors.length > 0 && (
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--color-danger)' }}>
                {t('register.batchErrorList')}
              </h4>
              {result.errors.map((item, index) => (
                <div key={`${item.email}-${index}`} style={{ fontSize: 13, color: 'var(--color-danger)', marginBottom: 4 }}>
                  {item.email}: {item.error}
                </div>
              ))}
            </div>
          )}

          <button
            className="btn btn-secondary"
            onClick={() => { setResult(null); setFileName(''); }}
            style={{ marginTop: 12 }}
          >
            {t('register.batchAnother')}
          </button>
        </div>
      )}
    </div>
  );
}
