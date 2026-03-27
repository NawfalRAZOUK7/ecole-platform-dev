/**
 * Registration page — multi-step: code → personal info → role fields → OTP.
 *
 * Reference: Phase 4D — Registration & Profile UI (Web)
 * Cascading from Phase 1B (profile tables) + Phase 2C (POST /auth/register).
 * Public route (no auth required). After successful registration, user is logged in.
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, setAccessToken } from '@/services/api/client';
// Note: after registration, user navigates and AuthProvider picks up the token on next /me call
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

const ROLE_REDIRECT: Record<string, string> = {
  PAR: '/feed',
  STD: '/content',
  TCH: '/teacher',
  ADM: '/admin',
  DIR: '/admin',
  SUP: '/notifications',
};

const PASSWORD_RULES = [
  { key: 'minLength', test: (p: string) => p.length >= 12 },
  { key: 'uppercase', test: (p: string) => /[A-Z]/.test(p) },
  { key: 'lowercase', test: (p: string) => /[a-z]/.test(p) },
  { key: 'digit', test: (p: string) => /\d/.test(p) },
  { key: 'special', test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

const RELATIONSHIP_TYPES = ['father', 'mother', 'guardian', 'other'] as const;

type Step = 'code' | 'info' | 'role' | 'otp';

export function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  // After registration the token is set; navigating to / triggers RoleRedirect which calls /me

  const [step, setStep] = useState<Step>('code');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Step 1 — code
  const [code, setCode] = useState('');
  const [, setDetectedRole] = useState('');

  // Step 2 — personal info
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Step 3 — role-specific
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [classLevel, setClassLevel] = useState('');
  const [relationshipType, setRelationshipType] = useState('');
  const [subjectSpecialty, setSubjectSpecialty] = useState('');
  const [qualification, setQualification] = useState('');

  // Step 4 — OTP
  const [otp, setOtp] = useState('');
  const [userId, setUserId] = useState('');
  const [schoolId, setSchoolId] = useState('');
  const [registeredRole, setRegisteredRole] = useState('');

  // Step 1: Validate code
  async function handleCodeSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // We validate by attempting a lightweight check.
      // Since there's no dedicated validate endpoint, we store the code
      // and proceed. The backend validates on actual register call.
      // For UX, we check code format and move to step 2.
      if (code.length !== 8) {
        setError(t('register.codeInvalid'));
        return;
      }
      // We'll detect role from the actual register response.
      // For now, move to info step.
      setStep('info');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }

  // Step 2: Validate personal info client-side, move to role fields
  function handleInfoSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError(t('profile.passwordMismatch'));
      return;
    }

    const failedRules = PASSWORD_RULES.filter((r) => !r.test(password));
    if (failedRules.length > 0) {
      setError(t('profile.passwordPolicyFail'));
      return;
    }

    setStep('role');
  }

  // Step 3: Submit registration
  async function handleRoleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const profileData: Record<string, string> = {};
    // We don't know the role yet (backend determines from code), so send all non-empty fields
    if (dateOfBirth) profileData.date_of_birth = dateOfBirth;
    if (classLevel) profileData.class_level = classLevel;
    if (relationshipType) profileData.relationship_type = relationshipType;
    if (subjectSpecialty) profileData.subject_specialty = subjectSpecialty;
    if (qualification) profileData.qualification = qualification;

    try {
      const res = await api.post<{
        access_token: string;
        token_type: string;
        expires_in: number;
        user_id: string;
        school_id: string;
        role: string;
        email_verification_required: boolean;
      }>('/auth/register', {
        code,
        email,
        full_name: fullName,
        phone: phone || null,
        password,
        profile_data: profileData,
      });

      const data = res.data;
      setAccessToken(data.access_token);
      setUserId(data.user_id);
      setSchoolId(data.school_id);
      setRegisteredRole(data.role);
      setDetectedRole(data.role);

      if (data.email_verification_required) {
        setStep('otp');
      } else {
        navigate(ROLE_REDIRECT[data.role] || '/');
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }

  // Step 4: Verify OTP
  async function handleOtpSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.post('/auth/verify-email', {
        user_id: userId,
        school_id: schoolId,
        otp,
      });

      // Navigate to role-specific home; AuthProvider will load profile from /me
      navigate(ROLE_REDIRECT[registeredRole] || '/');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }

  function handleSkipOtp() {
    // User can skip OTP and verify later from profile
    navigate(ROLE_REDIRECT[registeredRole] || '/');
  }

  const policyResults = PASSWORD_RULES.map((r) => ({
    key: r.key,
    passed: password.length > 0 ? r.test(password) : null,
  }));

  const allPolicyPassed = PASSWORD_RULES.every((r) => r.test(password));

  // Step indicators
  const steps: Step[] = ['code', 'info', 'role', 'otp'];
  const stepIndex = steps.indexOf(step);

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: 480 }}>
        <div className="login-header">
          <h1 className="login-title">{t('app.name')}</h1>
          <LanguageSwitcher />
        </div>

        <h2 className="login-subtitle">{t('register.title')}</h2>

        {/* Step indicator */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 20 }}>
          {steps.map((s, i) => (
            <div
              key={s}
              style={{
                width: 32,
                height: 4,
                borderRadius: 2,
                background: i <= stepIndex ? 'var(--color-primary)' : 'var(--color-border)',
              }}
            />
          ))}
        </div>

        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        {/* Step 1: Code Input */}
        {step === 'code' && (
          <form onSubmit={handleCodeSubmit} className="login-form">
            <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16, textAlign: 'center' }}>
              {t('register.step1')}
            </p>
            <div className="form-field">
              <label htmlFor="code">{t('register.code')}</label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder={t('register.codePlaceholder')}
                maxLength={8}
                required
                autoFocus
                disabled={loading}
                style={{ textAlign: 'center', fontSize: 18, letterSpacing: 4 }}
              />
            </div>
            <button type="submit" className="login-submit" disabled={loading || code.length !== 8}>
              {loading ? t('app.loading') : t('register.next')}
            </button>
            <div style={{ textAlign: 'center', marginTop: 12 }}>
              <Link to="/login" style={{ color: 'var(--color-primary)', fontSize: 14 }}>
                {t('register.hasAccount')}
              </Link>
            </div>
          </form>
        )}

        {/* Step 2: Personal Info */}
        {step === 'info' && (
          <form onSubmit={handleInfoSubmit} className="login-form">
            <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16, textAlign: 'center' }}>
              {t('register.step2')}
            </p>

            <div className="form-field">
              <label htmlFor="reg-email">{t('register.email')}</label>
              <input id="reg-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required disabled={loading} autoComplete="email" />
            </div>

            <div className="form-field">
              <label htmlFor="reg-name">{t('register.fullName')}</label>
              <input id="reg-name" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required disabled={loading} maxLength={200} />
            </div>

            <div className="form-field">
              <label htmlFor="reg-phone">{t('register.phone')}</label>
              <input id="reg-phone" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} disabled={loading} maxLength={20} />
            </div>

            <div className="form-field">
              <label htmlFor="reg-password">{t('register.password')}</label>
              <input id="reg-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={12} disabled={loading} autoComplete="new-password" />
            </div>

            {password.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                {policyResults.map((r) => (
                  <div key={r.key} style={{ fontSize: 12, color: r.passed ? 'var(--color-success)' : 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: 6, padding: '1px 0' }}>
                    <span>{r.passed ? '\u2713' : '\u2717'}</span>
                    <span>{t(`profile.policy.${r.key}`)}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="form-field">
              <label htmlFor="reg-confirm">{t('register.confirmPassword')}</label>
              <input id="reg-confirm" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required disabled={loading} autoComplete="new-password" />
              {confirmPassword.length > 0 && password !== confirmPassword && (
                <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>{t('profile.passwordMismatch')}</span>
              )}
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" className="btn btn-secondary" onClick={() => setStep('code')} style={{ flex: 1 }}>
                {t('app.back')}
              </button>
              <button type="submit" className="login-submit" style={{ flex: 2 }} disabled={!email || !fullName || !password || !allPolicyPassed || password !== confirmPassword}>
                {t('register.next')}
              </button>
            </div>
          </form>
        )}

        {/* Step 3: Role-Specific Fields */}
        {step === 'role' && (
          <form onSubmit={handleRoleSubmit} className="login-form">
            <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16, textAlign: 'center' }}>
              {t('register.step3')}
            </p>

            {/* Student fields */}
            <div>
              <h4 style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 8 }}>{t('register.roleFieldsHint')}</h4>

              <div className="form-field">
                <label htmlFor="reg-dob">{t('register.dateOfBirth')}</label>
                <input id="reg-dob" type="date" value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} disabled={loading} />
              </div>

              <div className="form-field">
                <label htmlFor="reg-class">{t('register.classLevel')}</label>
                <input id="reg-class" type="text" value={classLevel} onChange={(e) => setClassLevel(e.target.value)} disabled={loading} maxLength={50} />
              </div>

              <div className="form-field">
                <label htmlFor="reg-relation">{t('register.relationshipType')}</label>
                <select id="reg-relation" value={relationshipType} onChange={(e) => setRelationshipType(e.target.value)} disabled={loading} className="filter-select">
                  <option value="">{t('register.selectOptional')}</option>
                  {RELATIONSHIP_TYPES.map((rt) => (
                    <option key={rt} value={rt}>{t(`register.relationship_${rt}`)}</option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="reg-subject">{t('register.subjectSpecialty')}</label>
                <input id="reg-subject" type="text" value={subjectSpecialty} onChange={(e) => setSubjectSpecialty(e.target.value)} disabled={loading} maxLength={200} />
              </div>

              <div className="form-field">
                <label htmlFor="reg-qual">{t('register.qualification')}</label>
                <input id="reg-qual" type="text" value={qualification} onChange={(e) => setQualification(e.target.value)} disabled={loading} maxLength={200} />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button type="button" className="btn btn-secondary" onClick={() => setStep('info')} style={{ flex: 1 }}>
                {t('app.back')}
              </button>
              <button type="submit" className="login-submit" style={{ flex: 2 }} disabled={loading}>
                {loading ? t('app.loading') : t('register.submit')}
              </button>
            </div>
          </form>
        )}

        {/* Step 4: Email OTP Verification */}
        {step === 'otp' && (
          <form onSubmit={handleOtpSubmit} className="login-form">
            <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16, textAlign: 'center' }}>
              {t('register.otpInstructions')}
            </p>

            <div className="form-field">
              <label htmlFor="reg-otp">{t('register.otp')}</label>
              <input
                id="reg-otp"
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength={6}
                pattern="[0-9]{6}"
                required
                autoFocus
                disabled={loading}
                style={{ textAlign: 'center', fontSize: 18, letterSpacing: 4 }}
              />
            </div>

            <button type="submit" className="login-submit" disabled={loading || otp.length !== 6}>
              {loading ? t('app.loading') : t('register.verify')}
            </button>

            <button type="button" onClick={handleSkipOtp} style={{ width: '100%', marginTop: 8, background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer', fontSize: 13 }}>
              {t('register.skipOtp')}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
