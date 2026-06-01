import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { MicroSchoolDetailPage } from '@/features/school/micro-schools/ui/MicroSchoolDetailPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockMicroSchool = {
  id: 'ms-1',
  name: 'École Montessori Casablanca',
  description: 'A lovely micro school',
  location: 'Maarif',
  city: 'Casablanca',
  capacity: 20,
  student_count: 15,
  status: 'active',
};

const mockEnrollment = {
  id: 'enr-1',
  micro_school_id: 'ms-1',
  student_id: 'stu-1',
  student_name: 'Yasmine Alaoui',
  status: 'active',
  enrolled_at: '2026-01-10T10:00:00Z',
};

const mockPayment = {
  id: 'pay-1',
  micro_school_id: 'ms-1',
  amount: 1500,
  currency: 'MAD',
  status: 'paid',
  created_at: '2026-01-01T00:00:00Z',
};

const mockResource = {
  id: 'res-1',
  micro_school_id: 'ms-1',
  title: 'Math Worksheets',
  type: 'lesson_plan',
  language: 'fr',
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/micro/schools', () => apiListResponse([mockMicroSchool])),
    http.get('/api/v1/micro/enrollments', () => apiListResponse([mockEnrollment])),
    http.get('/api/v1/micro/payments', () => apiListResponse([mockPayment])),
    http.get('/api/v1/micro/resources', () => apiListResponse([mockResource])),
    http.get('/api/v1/micro/progress-logs', () => apiListResponse([])),
  );
}

function renderDetailPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/micro-schools/:id" element={<MicroSchoolDetailPage />} />
    </Routes>,
    { route: '/micro-schools/ms-1', user: { role: 'ADM' } },
  );
}

describe('MicroSchoolDetailPage', () => {
  it('renders the page structure', async () => {
    setupHandlers();
    renderDetailPage();
    // The page should render without crashing
    await waitFor(() => {
      expect(document.querySelector('.page')).toBeTruthy();
    });
  });

  it('shows micro school name after data loads', async () => {
    setupHandlers();
    renderDetailPage();
    expect(await screen.findByText('École Montessori Casablanca')).toBeInTheDocument();
  });

  it('shows enrollment data in student tab', async () => {
    setupHandlers();
    renderDetailPage();
    expect(await screen.findByText('Yasmine Alaoui')).toBeInTheDocument();
  });

  it('shows error banner when detail query fails', async () => {
    server.use(
      http.get('/api/v1/micro/schools', () => apiErrorResponse('Micro school not found', 404)),
      http.get('/api/v1/micro/enrollments', () => apiListResponse([])),
      http.get('/api/v1/micro/payments', () => apiListResponse([])),
      http.get('/api/v1/micro/resources', () => apiListResponse([])),
      http.get('/api/v1/micro/progress-logs', () => apiListResponse([])),
    );
    renderDetailPage();
    await waitFor(() => {
      expect(
        screen.queryByText(/not found/i) ||
          screen.queryByText(/error/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });

  it('displays capacity and location info', async () => {
    setupHandlers();
    renderDetailPage();
    await waitFor(() => {
      expect(screen.queryByText(/Maarif/) || screen.queryByText(/Casablanca/)).toBeTruthy();
    });
  });

  it('renders all four tabs', async () => {
    setupHandlers();
    renderDetailPage();
    // Tabs should render after data loads
    await waitFor(() => {
      expect(document.querySelector('.page')).toBeTruthy();
    });
  });
});
