/**
 * Profile page — user info, edit name/language, change password with policy feedback.
 *
 * Reference: S-081 — Profile / /me page
 * Phase 4C (from 2A) — Password change with policy feedback
 * Phase 4D — Role-specific profile sections (student, parent, teacher)
 * Calls POST /auth/change-password with current + new password.
 * Calls GET/PUT /me/profile for role-specific profile fields.
 */

import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthContext';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { AvatarUpload } from './AvatarUpload';
import { ProfileForm } from './ProfileForm';
import { ProfileInfo } from './ProfileInfo';
import { SecuritySettings } from './SecuritySettings';
import {
  useAdminUserProfile,
  useChangePassword,
  useProfileChildren,
  useProfileData,
  useSaveProfileData,
} from '../model/useProfile';
import type { ChildEntry, ProfileResponse } from '../api/profile.api';

const PASSWORD_RULES = [
  { key: 'minLength', test: (password: string) => password.length >= 12 },
  { key: 'uppercase', test: (password: string) => /[A-Z]/.test(password) },
  { key: 'lowercase', test: (password: string) => /[a-z]/.test(password) },
  { key: 'digit', test: (password: string) => /\d/.test(password) },
  { key: 'special', test: (password: string) => /[^A-Za-z0-9]/.test(password) },
];

export function ProfilePage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [profileForm, setProfileForm] = useState<Record<string, string>>({});
  const viewedUserId = searchParams.get('userId');
  const adminViewMode = Boolean(viewedUserId && ['ADM', 'SYS'].includes(user?.role || ''));
  const profileQuery = useProfileData();
  const adminProfileQuery = useAdminUserProfile(viewedUserId, adminViewMode);
  const saveProfileMutation = useSaveProfileData();
  const childrenQuery = useProfileChildren(user?.role === 'PAR');
  const changePasswordMutation = useChangePassword();
  const profileData: ProfileResponse | null = profileQuery.data ?? null;
  const profileLoading =
    profileQuery.isLoading || saveProfileMutation.isPending || adminProfileQuery.isLoading;
  const children: ChildEntry[] = childrenQuery.data ?? [];
  const childrenLoading = childrenQuery.isLoading;

  useEffect(() => {
    const profile =
      profileData?.student_profile ||
      profileData?.parent_profile ||
      profileData?.teacher_profile ||
      {};
    const nextForm: Record<string, string> = {};
    for (const [key, value] of Object.entries(profile)) {
      if (value !== null && value !== undefined && typeof value !== 'object') {
        nextForm[key] = String(value);
      }
    }
    setProfileForm(nextForm);
  }, [profileData]);

  function updateProfileField(key: string, value: string) {
    setProfileForm((current) => ({ ...current, [key]: value }));
  }

  async function handleProfileSave(event: FormEvent) {
    event.preventDefault();
    setProfileError(null);
    setProfileSuccess(false);

    try {
      const payload: Record<string, string | null> = {};
      for (const [key, value] of Object.entries(profileForm)) {
        if (!['id', 'user_id', 'school_id', 'created_at', 'updated_at'].includes(key)) {
          payload[key] = value || null;
        }
      }
      await saveProfileMutation.mutateAsync(payload);
      setProfileSuccess(true);
      await profileQuery.refetch();
      setShowProfileEdit(false);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : t('app.error'));
    }
  }

  async function handlePasswordChange(event: FormEvent) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (newPassword !== confirmPassword) {
      setPasswordError(t('profile.passwordMismatch'));
      return;
    }

    if (PASSWORD_RULES.some((rule) => !rule.test(newPassword))) {
      setPasswordError(t('profile.passwordPolicyFail'));
      return;
    }

    try {
      await changePasswordMutation.mutateAsync({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      setPasswordError(error instanceof Error ? error.message : t('app.error'));
    }
  }

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  if (!user) {
    return null;
  }

  const policyResults = PASSWORD_RULES.map((rule) => ({
    key: rule.key,
    passed: newPassword.length > 0 ? rule.test(newPassword) : null,
  }));

  return (
    <div className="page">
      <h1 className="page-title">
        {t(adminViewMode ? 'profile.adminView.title' : 'profile.title')}
      </h1>

      <div className="card profile-card">
        <AvatarUpload fullName={user.full_name} />
        <ProfileInfo children={children} childrenLoading={childrenLoading} user={user} />
        <ErrorBanner
          error={
            adminViewMode && adminProfileQuery.error instanceof Error
              ? adminProfileQuery.error.message
              : null
          }
        />
        {adminViewMode && adminProfileQuery.data ? (
          <div
            style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}
          >
            <h3 style={{ marginBottom: 12 }}>{t('profile.adminView.subtitle')}</h3>
            <div className="profile-fields">
              <div className="profile-field">
                <label>{t('profile.name')}</label>
                <span>{adminProfileQuery.data.full_name}</span>
              </div>
              <div className="profile-field">
                <label>{t('profile.email')}</label>
                <span>{adminProfileQuery.data.email}</span>
              </div>
              <div className="profile-field">
                <label>{t('profile.role')}</label>
                <span className="role-badge">
                  {t(`roles.${adminProfileQuery.data.role}`, adminProfileQuery.data.role)}
                </span>
              </div>
              <div className="profile-field">
                <label>{t('profile.phone')}</label>
                <span>{adminProfileQuery.data.phone || '—'}</span>
              </div>
            </div>
          </div>
        ) : null}
        {!adminViewMode ? (
          <>
            <ProfileForm
              loading={profileLoading}
              profileData={profileData}
              profileError={profileError}
              profileForm={profileForm}
              profileSuccess={profileSuccess}
              showProfileEdit={showProfileEdit}
              userRole={user.role}
              onDismissError={() => setProfileError(null)}
              onSubmit={handleProfileSave}
              onToggleEdit={(value) => {
                setShowProfileEdit(value);
                if (!value) {
                  setProfileError(null);
                  setProfileSuccess(false);
                }
              }}
              onUpdateField={updateProfileField}
            />
            <SecuritySettings
              confirmPassword={confirmPassword}
              currentPassword={currentPassword}
              isPending={changePasswordMutation.isPending}
              newPassword={newPassword}
              passwordError={passwordError}
              passwordSuccess={passwordSuccess}
              policyResults={policyResults}
              showPasswordForm={showPasswordForm}
              onCancel={() => {
                setShowPasswordForm(false);
                setPasswordError(null);
                setPasswordSuccess(false);
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
              }}
              onChangeConfirmPassword={setConfirmPassword}
              onChangeCurrentPassword={setCurrentPassword}
              onChangeNewPassword={setNewPassword}
              onDismissError={() => setPasswordError(null)}
              onSubmit={handlePasswordChange}
              onToggle={setShowPasswordForm}
            />
          </>
        ) : null}

        <button
          className="btn btn-danger logout-button"
          onClick={handleLogout}
          style={{ marginTop: 16 }}
        >
          {t('profile.logout')}
        </button>
      </div>
    </div>
  );
}
