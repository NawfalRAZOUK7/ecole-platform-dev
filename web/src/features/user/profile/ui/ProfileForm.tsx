import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import type { ProfileFormProps } from '../model/profile.types';

interface FieldDescriptor {
  key: string;
  label: string;
  type: 'text' | 'date' | 'tel' | 'textarea' | 'select';
  disabled?: boolean;
  options?: Array<{ label: string; value: string }>;
}

function getSectionTitle(userRole: string, t: (key: string) => string) {
  if (userRole === 'STD') return t('register.studentSection');
  if (userRole === 'PAR') return t('register.parentSection');
  return t('register.teacherSection');
}

function getViewFields(
  userRole: string,
  profileData: ProfileFormProps['profileData'],
  t: (key: string) => string,
) {
  if (userRole === 'STD' && profileData?.student_profile) {
    return [
      {
        label: t('register.studentNumber'),
        value: profileData.student_profile.student_number || '—',
      },
      { label: t('register.dateOfBirth'), value: profileData.student_profile.date_of_birth || '—' },
      { label: t('register.classLevel'), value: profileData.student_profile.class_level || '—' },
      { label: t('register.nationality'), value: profileData.student_profile.nationality || '—' },
    ];
  }
  if (userRole === 'PAR' && profileData?.parent_profile) {
    return [
      {
        label: t('register.relationshipType'),
        value: profileData.parent_profile.relationship_type || '—',
      },
      { label: t('register.cin'), value: profileData.parent_profile.cin_number || '—' },
      { label: t('register.address'), value: profileData.parent_profile.address || '—' },
      { label: t('register.profession'), value: profileData.parent_profile.profession || '—' },
      {
        label: t('register.emergencyPhone'),
        value: profileData.parent_profile.emergency_phone || '—',
      },
    ];
  }
  if (userRole === 'TCH' && profileData?.teacher_profile) {
    return [
      { label: t('register.employeeId'), value: profileData.teacher_profile.employee_id || '—' },
      {
        label: t('register.subjectSpecialty'),
        value: profileData.teacher_profile.subject_specialty || '—',
      },
      {
        label: t('register.qualification'),
        value: profileData.teacher_profile.qualification || '—',
      },
      { label: t('profile.rewardPoints'), value: profileData.teacher_profile.reward_points ?? 0 },
    ];
  }
  return [];
}

function getEditFields(userRole: string, t: (key: string) => string): FieldDescriptor[] {
  if (userRole === 'STD') {
    return [
      { key: 'student_number', label: t('register.studentNumber'), type: 'text', disabled: true },
      { key: 'date_of_birth', label: t('register.dateOfBirth'), type: 'date' },
      { key: 'class_level', label: t('register.classLevel'), type: 'text' },
      { key: 'nationality', label: t('register.nationality'), type: 'text' },
    ];
  }
  if (userRole === 'PAR') {
    return [
      {
        key: 'relationship_type',
        label: t('register.relationshipType'),
        type: 'select',
        options: [
          { label: '—', value: '' },
          { label: t('register.relationship_father'), value: 'father' },
          { label: t('register.relationship_mother'), value: 'mother' },
          { label: t('register.relationship_guardian'), value: 'guardian' },
          { label: t('register.relationship_other'), value: 'other' },
        ],
      },
      { key: 'cin_number', label: t('register.cin'), type: 'text' },
      { key: 'address', label: t('register.address'), type: 'textarea' },
      { key: 'profession', label: t('register.profession'), type: 'text' },
      { key: 'emergency_phone', label: t('register.emergencyPhone'), type: 'tel' },
    ];
  }
  return [
    { key: 'employee_id', label: t('register.employeeId'), type: 'text', disabled: true },
    { key: 'subject_specialty', label: t('register.subjectSpecialty'), type: 'text' },
    { key: 'qualification', label: t('register.qualification'), type: 'text' },
  ];
}

export function ProfileForm({
  loading,
  profileData,
  profileError,
  profileForm,
  profileSuccess,
  showProfileEdit,
  userRole,
  onDismissError,
  onSubmit,
  onToggleEdit,
  onUpdateField,
}: ProfileFormProps) {
  const { t } = useTranslation();

  if (!['STD', 'PAR', 'TCH'].includes(userRole)) {
    return null;
  }

  const viewFields = getViewFields(userRole, profileData, t);
  const editFields = getEditFields(userRole, t);
  const hasProfile = Boolean(
    profileData?.student_profile || profileData?.parent_profile || profileData?.teacher_profile,
  );

  return (
    <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
        {getSectionTitle(userRole, t)}
      </h3>
      <ErrorBanner error={profileError} onDismiss={onDismissError} />
      {profileSuccess && (
        <div
          style={{
            padding: 12,
            background: 'var(--color-surface-success)',
            border: '1px solid var(--color-success)',
            borderRadius: 'var(--radius)',
            marginBottom: 12,
            fontSize: 14,
            color: 'var(--color-success)',
          }}
        >
          {t('register.profileSaved')}
        </div>
      )}

      {!showProfileEdit ? (
        <div>
          {viewFields.length > 0 ? (
            <div className="profile-fields">
              {viewFields.map((field) => (
                <div key={field.label} className="profile-field">
                  <label>{field.label}</label>
                  <span
                    style={
                      field.label === t('profile.rewardPoints')
                        ? { fontWeight: 700, color: 'var(--color-primary)' }
                        : undefined
                    }
                  >
                    {field.value}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            !loading && (
              <p style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
                {t('register.noProfile')}
              </p>
            )
          )}
          <button
            className="btn btn-secondary"
            onClick={() => onToggleEdit(true)}
            style={{ marginTop: 8 }}
          >
            {t('register.editProfile')}
          </button>
        </div>
      ) : (
        <form onSubmit={onSubmit}>
          {editFields.map((field) => (
            <label key={field.key} className="form-field" style={{ marginBottom: 12 }}>
              <span>{field.label}</span>
              {field.type === 'textarea' ? (
                <textarea
                  className="filter-input"
                  value={profileForm[field.key] || ''}
                  onChange={(event) => onUpdateField(field.key, event.target.value)}
                  style={{ width: '100%', minHeight: 60 }}
                />
              ) : field.type === 'select' ? (
                <select
                  className="filter-select"
                  value={profileForm[field.key] || ''}
                  onChange={(event) => onUpdateField(field.key, event.target.value)}
                  style={{ width: '100%' }}
                >
                  {field.options?.map((option) => (
                    <option key={option.value || option.label} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type}
                  className="filter-input"
                  value={profileForm[field.key] || ''}
                  onChange={(event) => onUpdateField(field.key, event.target.value)}
                  disabled={field.disabled}
                  style={{
                    width: '100%',
                    background: field.disabled ? 'var(--color-surface)' : undefined,
                  }}
                />
              )}
            </label>
          ))}
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? t('app.loading') : t('app.save')}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => onToggleEdit(false)}>
              {t('app.cancel')}
            </button>
          </div>
        </form>
      )}

      {!hasProfile && !loading && !showProfileEdit && (
        <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginTop: 12 }}>
          {t('register.noProfile')}
        </p>
      )}
    </div>
  );
}
