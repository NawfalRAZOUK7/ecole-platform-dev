import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import { EVENT_TYPES, eventTitle, eventTypeColor } from './calendar.utils';
import type { CalendarFiltersProps } from './calendar.types';

export function CalendarFilters({
  availableClasses,
  copyState,
  icalUrl,
  selectedClassId,
  selectedDate,
  selectedDayItems,
  selectedTypes,
  onChangeClassId,
  onCopyIcal,
  onOpenDetails,
  onToggleType,
}: CalendarFiltersProps) {
  const { t, i18n } = useTranslation();

  return (
    <aside className="calendar-sidebar card">
      <h2>{t('calendar.filters.title')}</h2>
      <label className="form-field">
        <span>{t('calendar.form.class')}</span>
        <select value={selectedClassId} onChange={(event) => onChangeClassId(event.target.value)}>
          <option value="">{t('calendar.filters.allClasses')}</option>
          {availableClasses.map((item) => <option key={item.id} value={item.id}>{[item.code, item.name].filter(Boolean).join(' · ')}</option>)}
        </select>
      </label>
      <div className="calendar-filter-list">
        {EVENT_TYPES.map((type) => (
          <label key={type} className="form-checkbox">
            <input type="checkbox" checked={selectedTypes.includes(type)} onChange={() => onToggleType(type)} />
            <span>{t(`calendar.types.${type}`)}</span>
          </label>
        ))}
      </div>
      <div className="calendar-sidebar__section">
        <h3>{t('calendar.subscribeTitle')}</h3>
        <p>{t('calendar.subscribeHint')}</p>
        <div className="calendar-subscribe-box">
          <input readOnly value={icalUrl} />
          <button className="btn btn-secondary" type="button" onClick={onCopyIcal}>{t('calendar.copyIcal')}</button>
        </div>
        {copyState && <span className="calendar-copy-state">{copyState}</span>}
      </div>
      <div className="calendar-sidebar__section">
        <h3>{t('calendar.selectedDay')}</h3>
        <p>{selectedDate.toLocaleDateString(i18n.language, { dateStyle: 'full' })}</p>
        {selectedDayItems.length === 0 ? (
          <EmptyState message={t('calendar.noEvents')} icon="📅" />
        ) : (
          <div className="calendar-day-list">
            {selectedDayItems.map((item) => (
              <button key={item.instance_id} type="button" className={`calendar-day-list__item ${eventTypeColor(item.type)}`} onClick={() => onOpenDetails(item)}>
                <strong>{eventTitle(item, i18n.language)}</strong>
                <span>{new Date(item.start_at).toLocaleTimeString(i18n.language, { hour: '2-digit', minute: '2-digit' })}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
