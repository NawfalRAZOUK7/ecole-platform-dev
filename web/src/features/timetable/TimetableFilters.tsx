import { useTranslation } from 'react-i18next';
import type { TimetableFiltersProps } from './timetable.types';

export function TimetableFilters({
  classes,
  isAdmin,
  selectedClassId,
  weekStart,
  weekEnd,
  onChangeClass,
}: TimetableFiltersProps) {
  const { t } = useTranslation();

  return (
    <>
      {weekStart && weekEnd && (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginBottom: 16 }}>
          {t('timetable.weekOf')} {weekStart} — {weekEnd}
        </p>
      )}

      {isAdmin && classes.length > 0 && (
        <div className="filters-bar">
          <select
            className="filter-select"
            value={selectedClassId}
            onChange={(event) => onChangeClass(event.target.value)}
          >
            {classes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.code} — {item.name}
              </option>
            ))}
          </select>
        </div>
      )}
    </>
  );
}
