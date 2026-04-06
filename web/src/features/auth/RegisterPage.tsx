import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { setAccessToken } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { InviteCodeStep } from './InviteCodeStep';
import { PersonalInfoStep } from './PersonalInfoStep';
import { RegisterSteps } from './RegisterSteps';
import { SchoolInfoStep } from './SchoolInfoStep';
import { VerificationStep } from './VerificationStep';
import type { RegisterStep } from './register.types';
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

export function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const registerMutation = useRegister();
  const verifyEmailMutation = useVerifyEmail();
  const loading = registerMutation.isPending || verifyEmailMutation.isPending;
  const [step, setStep] = useState<RegisterStep>('code');
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
  const steps: RegisterStep[] = ['code', 'info', 'role', 'otp'];

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: 480 }}>
        <div className="login-header">
          <h1 className="login-title">{t('app.name')}</h1>
          <LanguageSwitcher />
        </div>

        <h2 className="login-subtitle">{t('register.title')}</h2>

        <RegisterSteps currentStep={step} steps={steps} />

        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        {step === 'code' ? (
          <InviteCodeStep code={code} loading={loading} onChangeCode={setCode} onSubmit={handleCodeSubmit} />
        ) : null}

        {step === 'info' ? (
          <PersonalInfoStep
            allPolicyPassed={allPolicyPassed}
            confirmPassword={confirmPassword}
            email={email}
            fullName={fullName}
            loading={loading}
            password={password}
            phone={phone}
            policyResults={policyResults}
            onBack={() => setStep('code')}
            onChangeConfirmPassword={setConfirmPassword}
            onChangeEmail={setEmail}
            onChangeFullName={setFullName}
            onChangePassword={setPassword}
            onChangePhone={setPhone}
            onSubmit={handleInfoSubmit}
          />
        ) : null}

        {step === 'role' ? (
          <SchoolInfoStep
            classLevel={classLevel}
            dateOfBirth={dateOfBirth}
            loading={loading}
            qualification={qualification}
            relationshipType={relationshipType}
            relationshipTypes={RELATIONSHIP_TYPES}
            subjectSpecialty={subjectSpecialty}
            onBack={() => setStep('info')}
            onChangeClassLevel={setClassLevel}
            onChangeDateOfBirth={setDateOfBirth}
            onChangeQualification={setQualification}
            onChangeRelationshipType={setRelationshipType}
            onChangeSubjectSpecialty={setSubjectSpecialty}
            onSubmit={handleRoleSubmit}
          />
        ) : null}

        {step === 'otp' ? (
          <VerificationStep loading={loading} otp={otp} onChangeOtp={setOtp} onSkip={handleSkipOtp} onSubmit={handleOtpSubmit} />
        ) : null}
      </div>
    </div>
  );
}
