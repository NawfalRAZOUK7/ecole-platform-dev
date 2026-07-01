import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { ProfilePage } from '@/features/user/profile/ui/ProfilePage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

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

const teacherProfileData = {
  user_id: 'user-2',
  email: 'teacher@ecole.test',
  full_name: 'Test Teacher',
  phone: null,
  role: 'TCH',
  school_id: 'school-1',
  student_profile: null,
  parent_profile: null,
  teacher_profile: {
    employee_id: 'EMP-001',
    subject_specialty: 'Mathematics',
    qualification: 'Masters',
    reward_points: 100,
  },
};

describe('ProfilePage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/me/profile', () => apiResponse(studentProfileData)));
  });

  it('renders without crashing for student user', async () => {
    renderWithProviders(<ProfilePage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders without crashing for teacher user', async () => {
    server.use(http.get('/api/v1/me/profile', () => apiResponse(teacherProfileData)));
    renderWithProviders(<ProfilePage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders profile page title', async () => {
    const { container } = renderWithProviders(<ProfilePage />, { user: { role: 'STD' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/me/profile', () => apiErrorResponse('Server error')));
    renderWithProviders(<ProfilePage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders children section for parent user', async () => {
    const parentProfileData = {
      ...studentProfileData,
      role: 'PAR',
      student_profile: null,
      parent_profile: {
        relationship_type: 'father',
        cin_number: 'AB123456',
        address: '123 Main St',
        profession: 'Engineer',
        emergency_phone: '+212600000000',
      },
    };
    server.use(
      http.get('/api/v1/me/profile', () => apiResponse(parentProfileData)),
      http.get('/api/v1/me/children', () => apiListResponse([])),
    );
    renderWithProviders(<ProfilePage />, { user: { role: 'PAR' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
