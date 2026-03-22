/**
 * Profile page — user info, edit name/language, change password with policy feedback.
 *
 * Reference: S-081 — Profile / /me page
 * Phase 4C (from 2A) — Password change with policy feedback
 * Phase 4D — Role-specific profile sections (student, parent, teacher)
 * Calls POST /auth/change-password with current + new password.
 * Calls GET/PUT /me/profile for role-specific profile fields.
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { api, ApiClientError } from '@/services/api/client';

/** Password policy rules — mirrors backend app/core/password_policy.py */
const PASSWORD_RULES = [
  { key: 'minLength', test: (p: string) => p.length >= 12 },
  { key: 'uppercase', test: (p: string) => /[A-Z]/.test(p) },
  { key: 'lowercase', test: (p: string) => /[a-z]/.test(p) },
  { key: 'digit', test: (p: string) => /\d/.test(p) },
  { key: 'special', test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

export function ProfilePage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Password change state
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  // Phase 4D — Role-specific profile state
  const [profileData, setProfileData] = useState<Record<string, any> | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [profileForm, setProfileForm] = useState<Record<string, string>>({});

  // Phase 4D-patch: My Children state (PAR only)
  interface ChildEntry {
    user_id: string;
    full_name: string;
    email: string;
    link_id: string;
    linked_at: string | null;
    student_profile: {
      class_level: string | null;
      date_of_birth: string | null;
      student_number: string | null;
      nationality: string | null;
    } | null;
  }
  const [children, setChildren] = useState<ChildEntry[]>([]);
  const [childrenLoading, setChildrenLoading] = useState(false);

  const fetchChildren = useCallback(async () => {
    if (!user || user.role !== 'PAR') return;
    setChildrenLoading(true);
    try {
      const res = await api.get<ChildEntry[]>('/me/children');
      setChildren(res.data);
    } catch { /* Parent may have no children linked */ }
    finally { setChildrenLoading(false); }
  }, [user]);

  const fetchProfile = useCallback(async () => {
    if (!user) return;
    setProfileLoading(true);
    try {
      const res = await api.get<Record<string, any>>('/me/profile');
      setProfileData(res.data);
      // Init form from profile data
      const p = res.data.student_profile || res.data.parent_profile || res.data.teacher_profile || {};
      const form: Record<string, string> = {};
      for (const [k, v] of Object.entries(p)) {
        if (v !== null && v !== undefined && typeof v !== 'object') form[k] = String(v);
      }
      setProfileForm(form);
    } catch {
      // Profile may not exist yet — that's OK
    } finally {
      setProfileLoading(false);
    }
  }, [user]);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);
  useEffect(() => { fetchChildren(); }, [fetchChildren]);

  async function handleProfileSave(e: FormEvent) {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(false);
    setProfileLoading(true);
    try {
      const body: Record<string, string | null> = {};
      for (const [k, v] of Object.entries(profileForm)) {
        if (!['id', 'user_id', 'school_id', 'created_at', 'updated_at'].includes(k)) {
          body[k] = v || null;
        }
      }
      await api.put('/me/profile', body);
      setProfileSuccess(true);
      await fetchProfile();
      setShowProfileEdit(false);
    } catch (err) {
      setProfileError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setProfileLoading(false);
    }
  }

  function updateProfileField(key: string, value: string) {
    setProfileForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  async function handlePasswordChange(e: FormEvent) {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (newPassword !== confirmPassword) {
      setPasswordError(t('profile.passwordMismatch'));
      return;
    }

    // Client-side policy check
    const failedRules = PASSWORD_RULES.filter((r) => !r.test(newPassword));
    if (failedRules.length > 0) {
      setPasswordError(t('profile.passwordPolicyFail'));
      return;
    }

    setPasswordLoading(true);
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setPasswordLoading(false);
    }
  }

  if (!user) return null;

  const policyResults = PASSWORD_RULES.map((r) => ({
    key: r.key,
    passed: newPassword.length > 0 ? r.test(newPassword) : null,
  }));

  return (
    <div className="page">
      <h1 className="page-title">{t('profile.title')}</h1>

      <div className="card profile-card">
        <div className="profile-avatar">
          <span style={{ fontSize: '48px' }}>👤</span>
        </div>

        <div className="profile-fields">
          <div className="profile-field">
            <label>{t('profile.name')}</label>
            <span>{user.full_name}</span>
          </div>

          <div className="profile-field">
            <label>{t('profile.email')}</label>
            <span>{user.email}</span>
          </div>

          <div className="profile-field">
            <label>{t('profile.role')}</label>
            <span className="role-badge">{t(`roles.${user.role}`, user.role)}</span>
          </div>

          <div className="profile-field">
            <label>{t('profile.school')}</label>
            <span>{user.school_id}</span>
          </div>

          {user.permissions && user.permissions.length > 0 && (
            <div className="profile-field">
              <label>{t('profile.permissions')}</label>
              <div className="permissions-list">
                {user.permissions.map((perm) => (
                  <span key={perm} className="permission-badge">{perm}</span>
                ))}
              </div>
            </div>
          )}

          <div className="profile-field">
            <label>{t('profile.language')}</label>
            <LanguageSwitcher />
          </div>
        </div>

        {/* Phase 4D — Role-Specific Profile Section */}
        {user.role && ['STD', 'PAR', 'TCH'].includes(user.role) && (
          <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
              {user.role === 'STD' && t('register.studentSection')}
              {user.role === 'PAR' && t('register.parentSection')}
              {user.role === 'TCH' && t('register.teacherSection')}
            </h3>

            <ErrorBanner error={profileError} onDismiss={() => setProfileError(null)} />
            {profileSuccess && (
              <div style={{ padding: 12, background: '#ecfdf5', border: '1px solid var(--color-success)', borderRadius: 'var(--radius)', marginBottom: 12, fontSize: 14, color: 'var(--color-success)' }}>
                {t('register.profileSaved')}
              </div>
            )}

            {!showProfileEdit ? (
              <div>
                {/* Display current profile fields */}
                {user.role === 'STD' && profileData?.student_profile && (
                  <div className="profile-fields">
                    <div className="profile-field"><label>{t('register.studentNumber')}</label><span>{profileData.student_profile.student_number || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.dateOfBirth')}</label><span>{profileData.student_profile.date_of_birth || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.classLevel')}</label><span>{profileData.student_profile.class_level || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.nationality')}</label><span>{profileData.student_profile.nationality || '—'}</span></div>
                  </div>
                )}
                {user.role === 'PAR' && profileData?.parent_profile && (
                  <div className="profile-fields">
                    <div className="profile-field"><label>{t('register.relationshipType')}</label><span>{profileData.parent_profile.relationship_type || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.cin')}</label><span>{profileData.parent_profile.cin_number || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.address')}</label><span>{profileData.parent_profile.address || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.profession')}</label><span>{profileData.parent_profile.profession || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.emergencyPhone')}</label><span>{profileData.parent_profile.emergency_phone || '—'}</span></div>
                  </div>
                )}
                {user.role === 'TCH' && profileData?.teacher_profile && (
                  <div className="profile-fields">
                    <div className="profile-field"><label>{t('register.employeeId')}</label><span>{profileData.teacher_profile.employee_id || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.subjectSpecialty')}</label><span>{profileData.teacher_profile.subject_specialty || '—'}</span></div>
                    <div className="profile-field"><label>{t('register.qualification')}</label><span>{profileData.teacher_profile.qualification || '—'}</span></div>
                    {/* Phase 10B — reward points from content promotion */}
                    <div className="profile-field">
                      <label>{t('profile.rewardPoints')}</label>
                      <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
                        {profileData.teacher_profile.reward_points ?? 0}
                      </span>
                    </div>
                  </div>
                )}
                {!profileData?.student_profile && !profileData?.parent_profile && !profileData?.teacher_profile && !profileLoading && (
                  <p style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>{t('register.noProfile')}</p>
                )}
                <button className="btn btn-secondary" onClick={() => setShowProfileEdit(true)} style={{ marginTop: 8 }}>
                  {t('register.editProfile')}
                </button>
              </div>
            ) : (
              <form onSubmit={handleProfileSave}>
                {/* Student edit form */}
                {user.role === 'STD' && (
                  <>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.studentNumber')}</label>
                      <input type="text" className="filter-input" value={profileForm.student_number || ''} disabled style={{ width: '100%', background: 'var(--color-surface)' }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.dateOfBirth')}</label>
                      <input type="date" className="filter-input" value={profileForm.date_of_birth || ''} onChange={(e) => updateProfileField('date_of_birth', e.target.value)} style={{ width: '100%' }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.classLevel')}</label>
                      <input type="text" className="filter-input" value={profileForm.class_level || ''} onChange={(e) => updateProfileField('class_level', e.target.value)} style={{ width: '100%' }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.nationality')}</label>
                      <input type="text" className="filter-input" value={profileForm.nationality || ''} onChange={(e) => updateProfileField('nationality', e.target.value)} style={{ width: '100%' }} />
                    </div>
                  </>
                )}
                {/* Parent edit form */}
                {user.role === 'PAR' && (
                  <>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.relationshipType')}</label>
                      <select className="filter-select" value={profileForm.relationship_type || ''} onChange={(e) => updateProfileField('relationship_type', e.target.value)} style={{ width: '100%' }}>
                        <option value="">—</option>
                        <option value="father">{t('register.relationship_father')}</option>
                        <option value="mother">{t('register.relationship_mother')}</option>
                        <option value="guardian">{t('register.relationship_guardian')}</option>
                        <option value="other">{t('register.relationship_other')}</option>
                      </select>
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.cin')}</label>
                      <input type="text" className="filter-input" value={profileForm.cin_number || ''} onChange={(e) => updateProfileField('cin_number', e.target.value)} style={{ width: '100%' }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.address')}</label>
                      <textarea className="filter-input" value={profileForm.address || ''} onChange={(e) => updateProfileField('address', e.target.value)} style={{ width: '100%', minHeight: 60 }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.profession')}</label>
                      <input type="text" className="filter-input" value={profileForm.profession || ''} onChange={(e) => updateProfileField('profession', e.target.value)} style={{ width: '100%' }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.emergencyPhone')}</label>
                      <input type="tel" className="filter-input" value={profileForm.emergency_phone || ''} onChange={(e) => updateProfileField('emergency_phone', e.target.value)} style={{ width: '100%' }} />
                    </div>
                  </>
                )}
                {/* Teacher edit form */}
                {user.role === 'TCH' && (
                  <>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.employeeId')}</label>
                      <input type="text" className="filter-input" value={profileForm.employee_id || ''} disabled style={{ width: '100%', background: 'var(--color-surface)' }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.subjectSpecialty')}</label>
                      <input type="text" className="filter-input" value={profileForm.subject_specialty || ''} onChange={(e) => updateProfileField('subject_specialty', e.target.value)} style={{ width: '100%' }} />
                    </div>
                    <div className="form-field" style={{ marginBottom: 12 }}>
                      <label>{t('register.qualification')}</label>
                      <input type="text" className="filter-input" value={profileForm.qualification || ''} onChange={(e) => updateProfileField('qualification', e.target.value)} style={{ width: '100%' }} />
                    </div>
                  </>
                )}
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="submit" className="btn btn-primary" disabled={profileLoading}>
                    {profileLoading ? t('app.loading') : t('app.save')}
                  </button>
                  <button type="button" className="btn btn-secondary" onClick={() => { setShowProfileEdit(false); setProfileError(null); setProfileSuccess(false); }}>
                    {t('app.cancel')}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Phase 4D-patch: My Children Section (PAR only) */}
        {user.role === 'PAR' && (
          <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
              {t('profile.myChildren.title')}
            </h3>
            {childrenLoading ? (
              <p style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>{t('app.loading')}</p>
            ) : children.length === 0 ? (
              <p style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>{t('profile.myChildren.empty')}</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {children.map((child) => (
                  <Link
                    key={child.user_id}
                    to="/results"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: '12px 16px',
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius)',
                      textDecoration: 'none',
                      color: 'inherit',
                      cursor: 'pointer',
                    }}
                  >
                    <span style={{ fontSize: 28 }}>👧</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{child.full_name}</div>
                      <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{child.email}</div>
                      {child.student_profile?.class_level && (
                        <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                          {t('register.classLevel')}: {child.student_profile.class_level}
                        </div>
                      )}
                    </div>
                    <span style={{ fontSize: 18, color: 'var(--color-text-secondary)' }}>›</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Password Change Section */}
        <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}>
          {!showPasswordForm ? (
            <button
              className="btn btn-secondary"
              onClick={() => setShowPasswordForm(true)}
            >
              {t('profile.changePassword')}
            </button>
          ) : (
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
                {t('profile.changePassword')}
              </h3>

              <ErrorBanner error={passwordError} onDismiss={() => setPasswordError(null)} />

              {passwordSuccess && (
                <div style={{ padding: 12, background: '#ecfdf5', border: '1px solid var(--color-success)', borderRadius: 'var(--radius)', marginBottom: 12, fontSize: 14, color: 'var(--color-success)' }}>
                  {t('profile.passwordChanged')}
                </div>
              )}

              <form onSubmit={handlePasswordChange}>
                <div className="form-field" style={{ marginBottom: 12 }}>
                  <label>{t('profile.currentPassword')}</label>
                  <input
                    type="password"
                    className="filter-input"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    disabled={passwordLoading}
                    style={{ width: '100%' }}
                  />
                </div>

                <div className="form-field" style={{ marginBottom: 8 }}>
                  <label>{t('profile.newPassword')}</label>
                  <input
                    type="password"
                    className="filter-input"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={12}
                    autoComplete="new-password"
                    disabled={passwordLoading}
                    style={{ width: '100%' }}
                  />
                </div>

                {/* Password policy feedback */}
                {newPassword.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    {policyResults.map((r) => (
                      <div
                        key={r.key}
                        style={{
                          fontSize: 12,
                          color: r.passed ? 'var(--color-success)' : 'var(--color-danger)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '1px 0',
                        }}
                      >
                        <span>{r.passed ? '\u2713' : '\u2717'}</span>
                        <span>{t(`profile.policy.${r.key}`)}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="form-field" style={{ marginBottom: 12 }}>
                  <label>{t('profile.confirmPassword')}</label>
                  <input
                    type="password"
                    className="filter-input"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    disabled={passwordLoading}
                    style={{ width: '100%' }}
                  />
                  {confirmPassword.length > 0 && newPassword !== confirmPassword && (
                    <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>
                      {t('profile.passwordMismatch')}
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={passwordLoading || !currentPassword || !newPassword || newPassword !== confirmPassword}
                  >
                    {passwordLoading ? t('app.loading') : t('profile.changePassword')}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowPasswordForm(false);
                      setPasswordError(null);
                      setPasswordSuccess(false);
                      setCurrentPassword('');
                      setNewPassword('');
                      setConfirmPassword('');
                    }}
                  >
                    {t('app.cancel')}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        <button className="btn btn-danger logout-button" onClick={handleLogout} style={{ marginTop: 16 }}>
          {t('profile.logout')}
        </button>
      </div>
    </div>
  );
}
