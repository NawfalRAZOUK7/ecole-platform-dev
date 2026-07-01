import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { CurriculumMappingPage } from '@/features/admin/compliance/ui/CurriculumMappingPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockCurriculum = {
  id: 'cur-1',
  level: 'Primary',
  grade: '6',
  subject: 'Mathematics',
  academic_year: '2025-2026',
  version: '1.0',
  is_active: true,
};

const mockObjective = {
  id: 'obj-1',
  code: 'OBJ-001',
  title_fr: 'Objective One',
  title_ar: 'هدف واحد',
  description_fr: 'Description',
  trimester: 1,
  unit_number: 1,
  hours_recommended: 2,
  display_order: 0,
  is_mandatory: true,
};

const mockMapping = {
  id: 'map-1',
  objective_id: 'obj-1',
  objective_code: 'OBJ-001',
  course_id: 'course-1',
  content_item_id: 'content-1',
  coverage_percent: 80,
  notes: null,
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/compliance/curricula', () => apiListResponse([mockCurriculum])),
    http.get('/api/v1/compliance/curricula/:id/objectives', () => apiListResponse([mockObjective])),
    http.get('/api/v1/compliance/mappings', () => apiListResponse([mockMapping])),
  );
}

describe('CurriculumMappingPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/compliance/curricula', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([mockCurriculum]);
      }),
      http.get('/api/v1/compliance/mappings', () => apiListResponse([])),
    );
    renderWithProviders(<CurriculumMappingPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') ||
        document.querySelector('.loading-state') ||
        document.querySelector('[aria-label="Loading..."]'),
    ).toBeTruthy();
  });

  it('renders curricula data successfully', async () => {
    setupHandlers();
    renderWithProviders(<CurriculumMappingPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Mathematics/)).toBeInTheDocument();
  });

  it('renders mapping rows after load', async () => {
    setupHandlers();
    renderWithProviders(<CurriculumMappingPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(screen.queryByText('OBJ-001')).toBeInTheDocument();
    });
  });

  it('shows error state when curricula fails to load', async () => {
    server.use(
      http.get('/api/v1/compliance/curricula', () => apiErrorResponse('Failed to load curricula')),
      http.get('/api/v1/compliance/mappings', () => apiListResponse([])),
    );
    renderWithProviders(<CurriculumMappingPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load curricula/)).toBeInTheDocument();
  });
});
