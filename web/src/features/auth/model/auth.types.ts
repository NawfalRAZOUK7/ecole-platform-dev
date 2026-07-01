import type { FormEvent } from 'react';

export type RegisterStep = 'code' | 'info' | 'role' | 'otp';

export interface RegisterStepsProps {
  currentStep: RegisterStep;
  steps: RegisterStep[];
}

export interface InviteCodeStepProps {
  code: string;
  loading: boolean;
  onChangeCode: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

export interface PasswordPolicyResult {
  key: string;
  passed: boolean | null;
}

export interface PersonalInfoStepProps {
  allPolicyPassed: boolean;
  confirmPassword: string;
  email: string;
  fullName: string;
  loading: boolean;
  password: string;
  phone: string;
  policyResults: PasswordPolicyResult[];
  onBack: () => void;
  onChangeConfirmPassword: (value: string) => void;
  onChangeEmail: (value: string) => void;
  onChangeFullName: (value: string) => void;
  onChangePassword: (value: string) => void;
  onChangePhone: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

export interface SchoolInfoStepProps {
  classLevel: string;
  dateOfBirth: string;
  loading: boolean;
  qualification: string;
  relationshipType: string;
  relationshipTypes: readonly string[];
  subjectSpecialty: string;
  onBack: () => void;
  onChangeClassLevel: (value: string) => void;
  onChangeDateOfBirth: (value: string) => void;
  onChangeQualification: (value: string) => void;
  onChangeRelationshipType: (value: string) => void;
  onChangeSubjectSpecialty: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

export interface VerificationStepProps {
  loading: boolean;
  otp: string;
  onChangeOtp: (value: string) => void;
  onSkip: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}
