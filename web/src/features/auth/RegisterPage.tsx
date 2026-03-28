import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { setAccessToken } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { useRegister, useVerifyEmail } from './useRegistration';

const ROLE_REDIRECT: Record<string, string> = {
  PAR: '/feed',
  STD: '/content',
  TCH: '/teacher',
  ADM: '/admin',
  DIR: '/admin',
  SUP: '/notifications',
};

const PASSWORD_RULES = [
  { key: 'minLength', test: (password: string) => password.length >= 12 },
  { key: 'uppercase', test: (password: string) => /[A-Z]/.test(password) },
  { key: 'lowercase', test: (password: string) => /[a-z]/.test(password) },
  { key: 'digit', test: (password: string) => /\d/.test(password) },
  { key: 'special', test: (password: string) => /[^A-Za-z0-9]/.test(password) },
];

const RELATIONSHIP_TYPES = ['father', 'mother', 'guardian', 'other'] as const;

type Step = 'code' | 'info' | 'role' | 'otp';

export function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const registerMutation = useRegister();
  const verifyEmailMutation = useVerifyEmail();
  const loading = registerMutation.isPending || verifyEmailMutation.isPending;
  const [step, setStep] = useState<Step>('code');
  const [error, setError] = useState<string | null>(null);

  const [code, setCode] = useState('');
  const [, setDetectedRole] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [classLevel, setClassLevel] = useState('');
  const [relationshipType, setRelationshipType] = useState('');
  const [subjectSpecialty, setSubjectSpecialty] = useState('');
  const [qualification, setQualification] = useState('');
  const [otp, setOtp] = useState('');
  const [userId, setUserId] = useState('');
  const [schoolId, setSchoolId] = useState('');
  const [registeredRole, setRegisteredRole] = useState('');

  async function handleCodeSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (code.length !== 8) {
      setError(t('register.codeInvalid'));
      return;
    }

    setStep('info');
  }

  function handleInfoSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError(t('profile.passwordMismatch'));
      return;
    }

    const failedRules = PASSWORD_RULES.filter((rule) => !rule.test(password));
    if (failedRules.length > 0) {
      setError(t('profile.passwordPolicyFail'));
      return;
    }

    setStep('role');
  }

  async function handleRoleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const profileData: Record<string, string> = {};
    if (dateOfBirth) profileData.date_of_birth = dateOfBirth;
    if (classLevel) profileData.class_level = classLevel;
    if (relationshipType) profileData.relationship_type = relationshipType;
    if (subjectSpecialty) profileData.subject_specialty = subjectSpecialty;
    if (qualification) profileData.qualification = qualification;

    try {
      const data = await registerMutation.mutateAsync({
        code,
        email,
        full_name: fullName,
        phone: phone || null,
        password,
        profile_data: profileData,
      });

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
    } catch (registrationError) {
      setError(registrationError instanceof Error ? registrationError.message : t('app.error'));
    }
  }

  async function handleOtpSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    try {
      await verifyEmailMutation.mutateAsync({
        user_id: userId,
        school_id: schoolId,
        otp,
      });
      navigate(ROLE_REDIRECT[registeredRole] || '/');
    } catch (verificationError) {
      setError(verificationError instanceof Error ? verificationError.message : t('app.error'));
    }
  }

  function handleSkipOtp() {
    navigate(ROLE_REDIRECT[registeredRole] || '/');
  }

  const policyResults = PASSWORD_RULES.map((rule) => ({
    key: rule.key,
    passed: password.length > 0 ? rule.test(password) : null,
  }));
  const allPolicyPassed = PASSWORD_RULES.every((rule) => rule.test(password));
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

        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 20 }}>
          {steps.map((currentStep, index) => (
            <div
              key={currentStep}
              style={{
                width: 32,
                height: 4,
                borderRadius: 2,
                background: index <= stepIndex ? 'var(--color-primary)' : 'var(--color-border)',
              }}
            />
          ))}
        </div>

        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        {step === 'code' ? (
          <form onSubmit={handleCodeSubmit} className="login-form">
            <p
              style={{
                fontSize: 14,
                color: 'var(--color-text-secondary)',
                marginBottom: 16,
                textAlign: 'center',
              }}
            >
              {t('register.step1')}
            </p>
            <div className="form-field">
              <label htmlFor="code">{t('register.code')}</label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={(event) => setCode(event.target.value.toUpperCase())}
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
        ) : null}

        {step === 'info' ? (
          <form onSubmit={handleInfoSubmit} className="login-form">
            <p
              style={{
                fontSize: 14,
                color: 'var(--color-text-secondary)',
                marginBottom: 16,
                textAlign: 'center',
              }}
            >
              {t('register.step2')}
            </p>

            <div className="form-field">
              <label htmlFor="reg-email">{t('register.email')}</label>
              <input
                id="reg-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                disabled={loading}
                autoComplete="email"
              />
            </div>

            <div className="form-field">
              <label htmlFor="reg-name">{t('register.fullName')}</label>
              <input
                id="reg-name"
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                required
                disabled={loading}
                maxLength={200}
              />
            </div>

            <div className="form-field">
              <label htmlFor="reg-phone">{t('register.phone')}</label>
              <input
                id="reg-phone"
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                disabled={loading}
                maxLength={20}
              />
            </div>

            <div className="form-field">
              <label htmlFor="reg-password">{t('register.password')}</label>
              <input
                id="reg-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={12}
                disabled={loading}
                autoComplete="new-password"
              />
            </div>

            {password.length > 0 ? (
              <div style={{ marginBottom: 12 }}>
                {policyResults.map((result) => (
                  <div
                    key={result.key}
                    style={{
                      fontSize: 12,
                      color: result.passed ? 'var(--color-success)' : 'var(--color-danger)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '1px 0',
                    }}
                  >
                    <span>{result.passed ? '\u2713' : '\u2717'}</span>
                    <span>{t(`profile.policy.${result.key}`)}</span>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="form-field">
              <label htmlFor="reg-confirm">{t('register.confirmPassword')}</label>
              <input
                id="reg-confirm"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
                disabled={loading}
                autoComplete="new-password"
              />
              {confirmPassword.length > 0 && password !== confirmPassword ? (
                <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>
                  {t('profile.passwordMismatch')}
                </span>
              ) : null}
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setStep('code')}
                style={{ flex: 1 }}
              >
                {t('app.back')}
              </button>
              <button
                type="submit"
                className="login-submit"
                style={{ flex: 2 }}
                disabled={loading || !allPolicyPassed || password !== confirmPassword}
              >
                {t('register.next')}
              </button>
            </div>
          </form>
        ) : null}

        {step === 'role' ? (
          <form onSubmit={handleRoleSubmit} className="login-form">
            <p
              style={{
                fontSize: 14,
                color: 'var(--color-text-secondary)',
                marginBottom: 16,
                textAlign: 'center',
              }}
            >
              {t('register.step3')}
            </p>

            <div>
              <h4 style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
                {t('register.roleFieldsHint')}
              </h4>

              <div className="form-field">
                <label htmlFor="reg-dob">{t('register.dateOfBirth')}</label>
                <input
                  id="reg-dob"
                  type="date"
                  value={dateOfBirth}
                  onChange={(event) => setDateOfBirth(event.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="form-field">
                <label htmlFor="reg-class">{t('register.classLevel')}</label>
                <input
                  id="reg-class"
                  type="text"
                  value={classLevel}
                  onChange={(event) => setClassLevel(event.target.value)}
                  disabled={loading}
                  maxLength={50}
                />
              </div>

              <div className="form-field">
                <label htmlFor="reg-relation">{t('register.relationshipType')}</label>
                <select
                  id="reg-relation"
                  value={relationshipType}
                  onChange={(event) => setRelationshipType(event.target.value)}
                  disabled={loading}
                  className="filter-select"
                >
                  <option value="">{t('register.selectOptional')}</option>
                  {RELATIONSHIP_TYPES.map((relationship) => (
                    <option key={relationship} value={relationship}>
                      {t(`register.relationship_${relationship}`)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="reg-subject">{t('register.subjectSpecialty')}</label>
                <input
                  id="reg-subject"
                  type="text"
                  value={subjectSpecialty}
                  onChange={(event) => setSubjectSpecialty(event.target.value)}
                  disabled={loading}
                  maxLength={200}
                />
              </div>

              <div className="form-field">
                <label htmlFor="reg-qual">{t('register.qualification')}</label>
                <input
                  id="reg-qual"
                  type="text"
                  value={qualification}
                  onChange={(event) => setQualification(event.target.value)}
                  disabled={loading}
                  maxLength={200}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setStep('info')}
                style={{ flex: 1 }}
              >
                {t('app.back')}
              </button>
              <button type="submit" className="login-submit" style={{ flex: 2 }} disabled={loading}>
                {loading ? t('app.loading') : t('register.submit')}
              </button>
            </div>
          </form>
        ) : null}

        {step === 'otp' ? (
          <form onSubmit={handleOtpSubmit} className="login-form">
            <p
              style={{
                fontSize: 14,
                color: 'var(--color-text-secondary)',
                marginBottom: 16,
                textAlign: 'center',
              }}
            >
              {t('register.otpInstructions')}
            </p>

            <div className="form-field">
              <label htmlFor="reg-otp">{t('register.otp')}</label>
              <input
                id="reg-otp"
                type="text"
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
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

            <button
              type="button"
              onClick={handleSkipOtp}
              style={{
                width: '100%',
                marginTop: 8,
                background: 'none',
                border: 'none',
                color: 'var(--color-text-secondary)',
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              {t('register.skipOtp')}
            </button>
          </form>
        ) : null}
      </div>
    </div>
  );
}
