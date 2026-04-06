import { useTranslation } from 'react-i18next';
import type { SchoolInfoStepProps } from './register.types';

export function SchoolInfoStep({
  classLevel,
  dateOfBirth,
  loading,
  qualification,
  relationshipType,
  relationshipTypes,
  subjectSpecialty,
  onBack,
  onChangeClassLevel,
  onChangeDateOfBirth,
  onChangeQualification,
  onChangeRelationshipType,
  onChangeSubjectSpecialty,
  onSubmit,
}: SchoolInfoStepProps) {
  const { t } = useTranslation();

  return (
    <form onSubmit={onSubmit} className="login-form">
      <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16, textAlign: 'center' }}>
        {t('register.step3')}
      </p>

      <div>
        <h4 style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
          {t('register.roleFieldsHint')}
        </h4>

        <label className="form-field" htmlFor="reg-dob">
          <span>{t('register.dateOfBirth')}</span>
          <input id="reg-dob" type="date" value={dateOfBirth} onChange={(event) => onChangeDateOfBirth(event.target.value)} disabled={loading} />
        </label>
        <label className="form-field" htmlFor="reg-class">
          <span>{t('register.classLevel')}</span>
          <input id="reg-class" type="text" value={classLevel} onChange={(event) => onChangeClassLevel(event.target.value)} disabled={loading} maxLength={50} />
        </label>
        <label className="form-field" htmlFor="reg-relation">
          <span>{t('register.relationshipType')}</span>
          <select id="reg-relation" value={relationshipType} onChange={(event) => onChangeRelationshipType(event.target.value)} disabled={loading} className="filter-select">
            <option value="">{t('register.selectOptional')}</option>
            {relationshipTypes.map((relationship) => (
              <option key={relationship} value={relationship}>
                {t(`register.relationship_${relationship}`)}
              </option>
            ))}
          </select>
        </label>
        <label className="form-field" htmlFor="reg-subject">
          <span>{t('register.subjectSpecialty')}</span>
          <input id="reg-subject" type="text" value={subjectSpecialty} onChange={(event) => onChangeSubjectSpecialty(event.target.value)} disabled={loading} maxLength={200} />
        </label>
        <label className="form-field" htmlFor="reg-qual">
          <span>{t('register.qualification')}</span>
          <input id="reg-qual" type="text" value={qualification} onChange={(event) => onChangeQualification(event.target.value)} disabled={loading} maxLength={200} />
        </label>
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <button type="button" className="btn btn-secondary" onClick={onBack} style={{ flex: 1 }}>
          {t('app.back')}
        </button>
        <button type="submit" className="login-submit" style={{ flex: 2 }} disabled={loading}>
          {loading ? t('app.loading') : t('register.submit')}
        </button>
      </div>
    </form>
  );
}
