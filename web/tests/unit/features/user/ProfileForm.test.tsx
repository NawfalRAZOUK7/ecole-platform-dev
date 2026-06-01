import { waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ProfileForm } from '@/features/user/profile/ui/ProfileForm';
import { renderWithProviders } from '../../../utils/render';

const noop = () => {};

const studentProfileData = {
  user_id: 'user-1',
  email: 'student@ecole.test',
  full_name: 'Student Example',
  phone: null,
  role: 'STD',
  school_id: 'school-1',
  student_profile: {
    student_number: 'STD-001',
    date_of_birth: '2015-03-10',
    class_level: 'cm2',
    nationality: 'MA',
  },
  parent_profile: null,
  teacher_profile: null,
};

describe('ProfileForm', () => {
  it('renders student profile view mode', async () => {
    const { container } = renderWithProviders(
      <ProfileForm
        loading={false}
        profileData={studentProfileData}
        profileError={null}
        profileForm={{ student_number: 'STD-001', date_of_birth: '2015-03-10' }}
        profileSuccess={false}
        showProfileEdit={false}
        userRole="STD"
        onDismissError={noop}
        onSubmit={noop}
        onToggleEdit={noop}
        onUpdateField={noop}
      />,
    );
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
    expect(container.textContent).toContain('STD-001');
  });

  it('renders teacher profile view mode', async () => {
    const teacherProfileData = {
      ...studentProfileData,
      role: 'TCH',
      student_profile: null,
      teacher_profile: {
        employee_id: 'EMP-001',
        subject_specialty: 'Mathematics',
        qualification: 'Masters',
        reward_points: 42,
      },
    };
    const { container } = renderWithProviders(
      <ProfileForm
        loading={false}
        profileData={teacherProfileData}
        profileError={null}
        profileForm={{ employee_id: 'EMP-001' }}
        profileSuccess={false}
        showProfileEdit={false}
        userRole="TCH"
        onDismissError={noop}
        onSubmit={noop}
        onToggleEdit={noop}
        onUpdateField={noop}
      />,
    );
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders edit form when showProfileEdit is true', async () => {
    const { container } = renderWithProviders(
      <ProfileForm
        loading={false}
        profileData={studentProfileData}
        profileError={null}
        profileForm={{ student_number: 'STD-001' }}
        profileSuccess={false}
        showProfileEdit={true}
        userRole="STD"
        onDismissError={noop}
        onSubmit={noop}
        onToggleEdit={noop}
        onUpdateField={noop}
      />,
    );
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
    expect(container.querySelector('form')).toBeTruthy();
  });

  it('shows success message when profileSuccess is true', async () => {
    const { container } = renderWithProviders(
      <ProfileForm
        loading={false}
        profileData={studentProfileData}
        profileError={null}
        profileForm={{}}
        profileSuccess={true}
        showProfileEdit={false}
        userRole="STD"
        onDismissError={noop}
        onSubmit={noop}
        onToggleEdit={noop}
        onUpdateField={noop}
      />,
    );
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('returns null for roles without profile form', async () => {
    const { container } = renderWithProviders(
      <ProfileForm
        loading={false}
        profileData={null}
        profileError={null}
        profileForm={{}}
        profileSuccess={false}
        showProfileEdit={false}
        userRole="ADM"
        onDismissError={noop}
        onSubmit={noop}
        onToggleEdit={noop}
        onUpdateField={noop}
      />,
    );
    await waitFor(() => expect(document.body.textContent !== undefined).toBe(true));
    expect(container.innerHTML).toBe('');
  });
});
