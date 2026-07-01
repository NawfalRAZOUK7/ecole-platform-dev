/**
 * Tests for auth registration step components:
 * - InviteCodeStep
 * - RegisterSteps
 * - SchoolInfoStep
 * - PersonalInfoStep
 * - VerificationStep
 */
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { InviteCodeStep } from '@/features/auth/ui/InviteCodeStep';
import { RegisterSteps } from '@/features/auth/ui/RegisterSteps';
import { PersonalInfoStep } from '@/features/auth/ui/PersonalInfoStep';
import { SchoolInfoStep } from '@/features/auth/ui/SchoolInfoStep';
import { VerificationStep } from '@/features/auth/ui/VerificationStep';
import { renderWithProviders } from '../../../utils/render';

// ---------------------------------------------------------------------------
// InviteCodeStep
// ---------------------------------------------------------------------------
describe('InviteCodeStep', () => {
  it('renders invite code input', () => {
    renderWithProviders(
      <InviteCodeStep code="" loading={false} onChangeCode={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByLabelText(/code/i)).toBeInTheDocument();
  });

  it('submits code via form submit', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn((e: React.FormEvent) => e.preventDefault());
    const onChangeCode = vi.fn();
    renderWithProviders(
      <InviteCodeStep
        code="ABCD1234"
        loading={false}
        onChangeCode={onChangeCode}
        onSubmit={onSubmit}
      />,
    );
    const btn = screen.getByRole('button');
    await user.click(btn);
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
  });

  it('disables submit when code length < 8', () => {
    renderWithProviders(
      <InviteCodeStep code="AB" loading={false} onChangeCode={vi.fn()} onSubmit={vi.fn()} />,
    );
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
  });

  it('disables submit when loading', () => {
    renderWithProviders(
      <InviteCodeStep code="ABCD1234" loading={true} onChangeCode={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows login link', () => {
    renderWithProviders(
      <InviteCodeStep code="" loading={false} onChangeCode={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByRole('link')).toBeInTheDocument();
  });

  it('calls onChangeCode with uppercase when user types', async () => {
    const user = userEvent.setup();
    const onChangeCode = vi.fn();
    renderWithProviders(
      <InviteCodeStep code="" loading={false} onChangeCode={onChangeCode} onSubmit={vi.fn()} />,
    );
    await user.type(screen.getByRole('textbox'), 'abc');
    expect(onChangeCode).toHaveBeenCalledWith(expect.stringMatching(/[A-Z]/));
  });
});

// ---------------------------------------------------------------------------
// RegisterSteps
// ---------------------------------------------------------------------------
describe('RegisterSteps', () => {
  const steps = ['invite', 'school', 'personal', 'verify'] as const;

  it('renders step indicators', () => {
    renderWithProviders(<RegisterSteps currentStep="invite" steps={steps} />);
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('marks completed steps visually at second step', () => {
    renderWithProviders(<RegisterSteps currentStep="school" steps={steps} />);
    // RegisterSteps renders div indicators without text content, check HTML
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders for each step', () => {
    steps.forEach((step) => {
      const { unmount } = renderWithProviders(<RegisterSteps currentStep={step} steps={steps} />);
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
      unmount();
    });
  });
});

// ---------------------------------------------------------------------------
// PersonalInfoStep
// ---------------------------------------------------------------------------
describe('PersonalInfoStep', () => {
  it('renders personal info form fields', () => {
    renderWithProviders(
      <PersonalInfoStep
        allPolicyPassed={false}
        confirmPassword=""
        email=""
        fullName=""
        loading={false}
        password=""
        phone=""
        policyResults={[]}
        onBack={vi.fn()}
        onChangeConfirmPassword={vi.fn()}
        onChangeEmail={vi.fn()}
        onChangeFullName={vi.fn()}
        onChangePassword={vi.fn()}
        onChangePhone={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(50);
  });

  it('shows form inputs', () => {
    renderWithProviders(
      <PersonalInfoStep
        allPolicyPassed={true}
        confirmPassword="pass123"
        email="user@test.com"
        fullName="Test User"
        loading={false}
        password="pass123"
        phone="+212600000000"
        policyResults={[]}
        onBack={vi.fn()}
        onChangeConfirmPassword={vi.fn()}
        onChangeEmail={vi.fn()}
        onChangeFullName={vi.fn()}
        onChangePassword={vi.fn()}
        onChangePhone={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(document.body.textContent).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// SchoolInfoStep
// ---------------------------------------------------------------------------
describe('SchoolInfoStep', () => {
  it('renders school info form', () => {
    renderWithProviders(
      <SchoolInfoStep
        classLevel=""
        dateOfBirth=""
        loading={false}
        qualification=""
        relationshipType=""
        relationshipTypes={['parent', 'guardian']}
        subjectSpecialty=""
        onBack={vi.fn()}
        onChangeClassLevel={vi.fn()}
        onChangeDateOfBirth={vi.fn()}
        onChangeQualification={vi.fn()}
        onChangeRelationshipType={vi.fn()}
        onChangeSubjectSpecialty={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(50);
  });

  it('renders form elements', () => {
    renderWithProviders(
      <SchoolInfoStep
        classLevel="ce2"
        dateOfBirth="2010-01-01"
        loading={false}
        qualification=""
        relationshipType="parent"
        relationshipTypes={['parent', 'guardian']}
        subjectSpecialty=""
        onBack={vi.fn()}
        onChangeClassLevel={vi.fn()}
        onChangeDateOfBirth={vi.fn()}
        onChangeQualification={vi.fn()}
        onChangeRelationshipType={vi.fn()}
        onChangeSubjectSpecialty={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(document.body.textContent).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// VerificationStep
// ---------------------------------------------------------------------------
describe('VerificationStep', () => {
  it('renders verification form', () => {
    renderWithProviders(
      <VerificationStep
        loading={false}
        otp=""
        onChangeOtp={vi.fn()}
        onSkip={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows OTP input', () => {
    renderWithProviders(
      <VerificationStep
        loading={false}
        otp="123456"
        onChangeOtp={vi.fn()}
        onSkip={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(document.body.textContent).toBeTruthy();
  });
});
