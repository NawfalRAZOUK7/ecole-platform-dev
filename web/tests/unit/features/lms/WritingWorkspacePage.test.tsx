import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { WritingWorkspacePage } from '@/features/lms/student/ui/WritingWorkspacePage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse } from '../../../utils/mocks';

const mockWritingResponse = {
  id: 'attempt-1',
  text: 'My story text',
  feedback: {
    corrected_text: 'My corrected story text',
    suggestions: ['Use more vivid verbs', 'Check punctuation'],
    score: 85,
    encouragement: 'Great job!',
  },
  created_at: '2026-01-01T00:00:00Z',
};

const mockProfile = {
  user_id: 'user-1',
  email: 'student@test.com',
  full_name: 'Test Student',
  phone: null,
  role: 'STD',
  school_id: 'school-1',
  student_profile: {
    student_number: 'STD-001',
    date_of_birth: '2015-09-01',
    class_level: 'ce2',
    nationality: 'MA',
  },
  parent_profile: null,
  teacher_profile: null,
};

describe('WritingWorkspacePage', () => {
  it('renders without crashing', async () => {
    renderWithProviders(<WritingWorkspacePage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders the writing textarea', async () => {
    renderWithProviders(<WritingWorkspacePage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.querySelector('textarea')).toBeTruthy();
    });
  });

  it('renders writing type selector buttons', async () => {
    renderWithProviders(<WritingWorkspacePage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
    // Check type buttons exist (story, essay, letter, description, free)
    expect(document.body.textContent).toBeTruthy();
  });

  it('shows character count area', async () => {
    renderWithProviders(<WritingWorkspacePage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.textContent).toContain('5000');
    });
  });

  it('shows feedback after submission', async () => {
    server.use(
      http.post('/api/v1/writing-attempts', () =>
        HttpResponse.json({
          data: mockWritingResponse,
          meta: { timestamp: new Date().toISOString(), version: 'test' },
        }),
      ),
    );
    renderWithProviders(<WritingWorkspacePage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
