/**
 * Admin batch registration page — CSV upload for bulk account creation.
 *
 * Reference: Phase 4D — Registration & Profile UI (Web)
 * Cascading from Phase 2C (POST /admin/register-batch).
 * ADM-only route. Parses CSV, shows preview table, submits to backend.
 */

import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';

interface CsvRow {
  email: string;
  full_name: string;
  role: string;
  phone?: string;
  class_code?: string;
}

interface BatchResult {
  created: Array<{ user_id: string; email: string; full_name: string; role: string; temp_password: string }>;
  errors: Array<{ email: string; error: string }>;
  total_created: number;
  total_errors: number;
}

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
  for (let i = 1; i < lines.length; i++) {
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

  const [rows, setRows] = useState<CsvRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BatchResult | null>(null);
  const [fileName, setFileName] = useState('');

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    setError(null);
    setResult(null);
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError(t('register.csvInvalidFormat'));
      return;
    }

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const parsed = parseCsv(text);
      if (parsed.length === 0) {
        setError(t('register.csvEmpty'));
        return;
      }
      if (parsed.length > 100) {
        setError(t('register.csvTooMany'));
        return;
      }
      setRows(parsed);
    };
    reader.readAsText(file);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (rows.length === 0) return;
    setError(null);
    setLoading(true);

    try {
      const res = await api.post<BatchResult>('/admin/register-batch', { users: rows });
      setResult(res.data);
      setRows([]);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('register.batchTitle')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {/* CSV Upload */}
      <div className="card" style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
          {t('register.batchInstructions')}
        </p>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 12, fontFamily: 'monospace' }}>
          email,full_name,role,phone,class_code
        </p>

        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          style={{ marginBottom: 12 }}
        />
        {fileName && <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{fileName}</span>}
      </div>

      {/* Preview Table */}
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
                {rows.map((row, i) => (
                  <tr key={i}>
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
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? t('app.loading') : t('register.batchSubmit')}
            </button>
          </form>
        </div>
      )}

      {loading && <LoadingState />}

      {/* Results */}
      {result && (
        <div className="card">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
            {t('register.batchResults')}
          </h3>

          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <div style={{ padding: 12, background: '#ecfdf5', borderRadius: 'var(--radius)', flex: 1 }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-success)' }}>{result.total_created}</div>
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('register.batchCreated')}</div>
            </div>
            {result.total_errors > 0 && (
              <div style={{ padding: 12, background: '#fef2f2', borderRadius: 'var(--radius)', flex: 1 }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-danger)' }}>{result.total_errors}</div>
                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('register.batchErrors')}</div>
              </div>
            )}
          </div>

          {/* Created accounts with temp passwords */}
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
                  {result.created.map((u) => (
                    <tr key={u.user_id}>
                      <td>{u.email}</td>
                      <td>{u.full_name}</td>
                      <td><span className="role-badge">{u.role}</span></td>
                      <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{u.temp_password}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Errors */}
          {result.errors.length > 0 && (
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--color-danger)' }}>
                {t('register.batchErrorList')}
              </h4>
              {result.errors.map((err, i) => (
                <div key={i} style={{ fontSize: 13, color: 'var(--color-danger)', marginBottom: 4 }}>
                  {err.email}: {err.error}
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
