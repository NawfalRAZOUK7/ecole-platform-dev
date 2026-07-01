import { useTranslation } from 'react-i18next';
import type { AssignContentModalProps } from '../model/content-library.types';

export function AssignContentModal({
  assignClassId,
  assignItem,
  assignNotes,
  classes,
  isPending,
  onChangeClassId,
  onChangeNotes,
  onClose,
  onSubmit,
}: AssignContentModalProps) {
  const { t } = useTranslation();

  if (!assignItem) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(15, 23, 42, 0.55)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <form
        className="card"
        style={{ padding: 24, maxWidth: 400, width: '100%' }}
        onSubmit={onSubmit}
      >
        <h3 style={{ margin: '0 0 16px' }}>{t('teacherContent.assignTitle')}</h3>
        <p style={{ fontSize: 13, marginBottom: 12 }}>
          <strong>{assignItem.title}</strong>
        </p>
        <label className="form-field" style={{ marginBottom: 12 }}>
          <span>{t('teacherContent.selectClass')}</span>
          <select
            className="filter-select"
            value={assignClassId}
            onChange={(event) => onChangeClassId(event.target.value)}
            required
            style={{ width: '100%' }}
          >
            <option value="">{t('teacherContent.choosePlaceholder')}</option>
            {classes.map((classItem) => (
              <option key={classItem.id} value={classItem.id}>
                {classItem.name}
              </option>
            ))}
          </select>
        </label>
        <label className="form-field" style={{ marginBottom: 16 }}>
          <span>{t('teacherContent.notes')}</span>
          <input
            className="filter-input"
            value={assignNotes}
            onChange={(event) => onChangeNotes(event.target.value)}
            placeholder={t('teacherContent.notesPlaceholder')}
            style={{ width: '100%' }}
          />
        </label>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" className="btn btn-primary" disabled={isPending}>
            {isPending ? t('app.loading') : t('teacherContent.assign')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            {t('app.cancel')}
          </button>
        </div>
      </form>
    </div>
  );
}
