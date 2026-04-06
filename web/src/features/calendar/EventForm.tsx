import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ROLE_OPTIONS, type EventFormProps } from './calendar.types';
import type { EventFormState } from './types';
import { toEventFormState, toEventPayload } from './calendar.utils';

export function EventForm({ availableClasses, initialEvent, isOpen, onClose, onSubmit, userRole }: EventFormProps) {
  const { t } = useTranslation();
  const [form, setForm] = useState<EventFormState>(toEventFormState(initialEvent, userRole, availableClasses));
  const [saving, setSaving] = useState(false);
  const canSetVisibility = userRole !== 'TCH';

  useEffect(() => {
    setForm(toEventFormState(initialEvent, userRole, availableClasses));
  }, [availableClasses, initialEvent, isOpen, userRole]);

  if (!isOpen) return null;

  async function handleSubmit() {
    setSaving(true);
    try {
      await onSubmit(toEventPayload(form, userRole));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card calendar-modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="calendar-modal-card__header">
          <h2>{t(initialEvent ? 'calendar.editEvent' : 'calendar.createEvent')}</h2>
          <button className="dropdown-link" type="button" onClick={onClose}>{t('app.cancel')}</button>
        </div>
        <label className="form-field"><span>{t('calendar.form.titleFr')}</span><input value={form.title_fr} onChange={(event) => setForm((current) => ({ ...current, title_fr: event.target.value }))} /></label>
        <div className="calendar-form-grid">
          <label className="form-field"><span>{t('calendar.form.titleAr')}</span><input value={form.title_ar} onChange={(event) => setForm((current) => ({ ...current, title_ar: event.target.value }))} /></label>
          <label className="form-field"><span>{t('calendar.form.titleEn')}</span><input value={form.title_en} onChange={(event) => setForm((current) => ({ ...current, title_en: event.target.value }))} /></label>
        </div>
        <div className="calendar-form-grid">
          <label className="form-field"><span>{t('calendar.form.type')}</span><select value={form.type} onChange={(event) => setForm((current) => ({ ...current, type: event.target.value as EventFormState['type'] }))}>{['holiday', 'exam', 'meeting', 'excursion', 'ceremony', 'custom'].map((value) => <option key={value} value={value}>{t(`calendar.types.${value}`)}</option>)}</select></label>
          <label className="form-field"><span>{t('calendar.form.visibility')}</span><select disabled={!canSetVisibility} value={canSetVisibility ? form.visibility : 'class'} onChange={(event) => setForm((current) => ({ ...current, visibility: event.target.value as EventFormState['visibility'] }))}>{['school', 'class', 'role'].map((value) => <option key={value} value={value}>{t(`calendar.visibility.${value}`)}</option>)}</select></label>
        </div>
        <div className="calendar-form-grid">
          <label className="form-field"><span>{t('calendar.form.start')}</span><input type="datetime-local" value={form.start_at} onChange={(event) => setForm((current) => ({ ...current, start_at: event.target.value }))} /></label>
          <label className="form-field"><span>{t('calendar.form.end')}</span><input type="datetime-local" value={form.end_at} onChange={(event) => setForm((current) => ({ ...current, end_at: event.target.value }))} /></label>
        </div>
        <div className="calendar-form-grid">
          <label className="form-field"><span>{t('calendar.form.location')}</span><input value={form.location} onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))} /></label>
          <label className="form-field"><span>{t('calendar.form.capacity')}</span><input type="number" min="1" value={form.capacity} onChange={(event) => setForm((current) => ({ ...current, capacity: event.target.value }))} /></label>
        </div>
        {(userRole === 'TCH' || form.visibility === 'class') && <label className="form-field"><span>{t('calendar.form.class')}</span><select value={form.class_id} onChange={(event) => setForm((current) => ({ ...current, class_id: event.target.value }))}>{availableClasses.map((item) => <option key={item.id} value={item.id}>{[item.code, item.name].filter(Boolean).join(' · ')}</option>)}</select></label>}
        {form.visibility === 'role' && <div className="calendar-role-picker"><span>{t('calendar.form.roles')}</span><div className="calendar-role-picker__list">{ROLE_OPTIONS.map((role) => <label key={role} className="form-checkbox"><input type="checkbox" checked={form.role_codes.includes(role)} onChange={(event) => setForm((current) => ({ ...current, role_codes: event.target.checked ? [...current.role_codes, role] : current.role_codes.filter((item) => item !== role) }))} /><span>{role}</span></label>)}</div></div>}
        <label className="form-field"><span>{t('calendar.form.description')}</span><textarea className="filter-input" rows={4} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></label>
        <div className="calendar-form-grid">
          <label className="form-checkbox"><input type="checkbox" checked={form.is_all_day} onChange={(event) => setForm((current) => ({ ...current, is_all_day: event.target.checked }))} /><span>{t('calendar.form.allDay')}</span></label>
          <label className="form-field"><span>{t('calendar.form.recurrence')}</span><select value={form.recurrence_frequency} onChange={(event) => setForm((current) => ({ ...current, recurrence_frequency: event.target.value as EventFormState['recurrence_frequency'] }))}><option value="">{t('calendar.recurrence.none')}</option><option value="weekly">{t('calendar.recurrence.weekly')}</option><option value="annual">{t('calendar.recurrence.annual')}</option></select></label>
        </div>
        {form.recurrence_frequency && <div className="calendar-form-grid"><label className="form-field"><span>{t('calendar.form.interval')}</span><input type="number" min="1" value={form.recurrence_interval} onChange={(event) => setForm((current) => ({ ...current, recurrence_interval: event.target.value }))} /></label><label className="form-field"><span>{t('calendar.form.until')}</span><input type="datetime-local" value={form.recurrence_until} onChange={(event) => setForm((current) => ({ ...current, recurrence_until: event.target.value }))} /></label></div>}
        <div className="calendar-modal-card__actions"><button className="btn btn-secondary" type="button" onClick={onClose}>{t('app.cancel')}</button><button className="btn btn-primary" type="button" disabled={saving || !form.title_fr.trim()} onClick={() => void handleSubmit()}>{saving ? t('calendar.saving') : t('app.save')}</button></div>
      </div>
    </div>
  );
}
