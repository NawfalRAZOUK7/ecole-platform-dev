import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge } from '@/shared/ui/Badge';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import {
  useHolidays,
  useCreateHoliday,
  useUpdateHoliday,
  useDeleteHoliday,
} from '../model/useCalendar';
import type { Holiday, HolidayPayload, HolidayType } from '../api/calendar.api';

const TYPE_VARIANT: Record<HolidayType, 'info' | 'success'> = {
  national: 'info',
  school: 'success',
};

interface HolidayForm {
  name: string;
  start_date: string;
  end_date: string;
  type: HolidayType;
  description: string;
}

const EMPTY_FORM: HolidayForm = {
  name: '',
  start_date: '',
  end_date: '',
  type: 'school',
  description: '',
};

export function HolidayManagerPage() {
  const { t, i18n } = useTranslation();
  const holidaysQuery = useHolidays();
  const createMutation = useCreateHoliday();
  const updateMutation = useUpdateHoliday();
  const deleteMutation = useDeleteHoliday();

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<HolidayForm>(EMPTY_FORM);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const holidays = holidaysQuery.data ?? [];
  const saving = createMutation.isPending || updateMutation.isPending;

  function openCreate() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setShowForm(true);
    setError(null);
  }

  function openEdit(holiday: Holiday) {
    setForm({
      name: holiday.name,
      start_date: holiday.start_date,
      end_date: holiday.end_date,
      type: holiday.type,
      description: holiday.description ?? '',
    });
    setEditingId(holiday.id);
    setShowForm(true);
    setError(null);
  }

  async function handleSave() {
    setError(null);
    const payload: HolidayPayload = {
      name: form.name,
      start_date: form.start_date,
      end_date: form.end_date,
      type: form.type,
      description: form.description || undefined,
    };
    try {
      if (editingId) {
        await updateMutation.mutateAsync({ id: editingId, payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      setShowForm(false);
      setForm(EMPTY_FORM);
      setEditingId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      await deleteMutation.mutateAsync(id);
      setConfirmDeleteId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (holidaysQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {t('calendar.holidays.title')}
        </h1>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + {t('calendar.holidays.create')}
        </button>
      </div>

      <ErrorBanner
        error={error || (holidaysQuery.error instanceof Error ? holidaysQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void holidaysQuery.refetch()}
      />

      {holidays.length === 0 ? (
        <EmptyState message={t('calendar.holidays.empty')} icon="🗓️" />
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('calendar.holidays.name')}</th>
                <th>{t('calendar.holidays.startDate')}</th>
                <th>{t('calendar.holidays.endDate')}</th>
                <th>{t('calendar.holidays.type')}</th>
                <th>{t('app.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {holidays.map((holiday) => (
                <tr key={holiday.id}>
                  <td>
                    <div>
                      <strong>{holiday.name}</strong>
                      {holiday.description && (
                        <p
                          style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: 0 }}
                        >
                          {holiday.description}
                        </p>
                      )}
                    </div>
                  </td>
                  <td>{formatDate(holiday.start_date, i18n.language)}</td>
                  <td>{formatDate(holiday.end_date, i18n.language)}</td>
                  <td>
                    <Badge variant={TYPE_VARIANT[holiday.type]}>
                      {t(`calendar.holidays.types.${holiday.type}`)}
                    </Badge>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => openEdit(holiday)}
                      >
                        {t('app.edit')}
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        style={{ color: 'var(--color-error)' }}
                        onClick={() => setConfirmDeleteId(holiday.id)}
                      >
                        {t('app.delete')}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div
            className="modal-card"
            style={{ maxWidth: 520 }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginBottom: 16 }}>
              {editingId ? t('calendar.holidays.edit') : t('calendar.holidays.create')}
            </h2>

            <div className="form-field">
              <label>{t('calendar.holidays.name')}</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('calendar.holidays.startDate')}</label>
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                />
              </div>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('calendar.holidays.endDate')}</label>
                <input
                  type="date"
                  value={form.end_date}
                  min={form.start_date}
                  onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                />
              </div>
            </div>

            <div className="form-field">
              <label>{t('calendar.holidays.type')}</label>
              <select
                className="filter-select"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value as HolidayType })}
              >
                <option value="national">{t('calendar.holidays.types.national')}</option>
                <option value="school">{t('calendar.holidays.types.school')}</option>
              </select>
            </div>

            <div className="form-field">
              <label>{t('calendar.holidays.description')}</label>
              <input
                type="text"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder={t('app.optional')}
              />
            </div>

            {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={saving || !form.name || !form.start_date || !form.end_date}
                onClick={() => void handleSave()}
              >
                {saving ? t('app.loading') : t('app.save')}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowForm(false)}
              >
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDeleteId && (
        <div className="modal-overlay" onClick={() => setConfirmDeleteId(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 12 }}>{t('calendar.holidays.confirmDeleteTitle')}</h2>
            <p style={{ marginBottom: 20 }}>{t('calendar.holidays.confirmDeleteBody')}</p>
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                type="button"
                className="btn btn-primary"
                style={{ background: 'var(--color-error)' }}
                disabled={deleteMutation.isPending}
                onClick={() => void handleDelete(confirmDeleteId)}
              >
                {deleteMutation.isPending ? t('app.loading') : t('app.delete')}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmDeleteId(null)}
              >
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
