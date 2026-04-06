import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { Route, Routes, useParams } from 'react-router-dom';
import { delay, http } from 'msw';
import { describe, expect, it } from 'vitest';
import { MicroSchoolListPage } from '@/features/micro-schools/MicroSchoolListPage';
import { renderWithProviders } from '../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../utils/mocks';

const microSchools = [
  {
    id: 'school-1',
    name: 'Atlas Learning Hub',
    location: 'Rue Atlas',
    city: 'Casablanca',
    capacity: 40,
    student_count: 24,
    status: 'active' as const,
  },
  {
    id: 'school-2',
    name: 'Sahara Micro-School',
    location: 'Avenue Sahara',
    city: 'Agadir',
    capacity: 30,
    student_count: 18,
    status: 'suspended' as const,
  },
];

function MicroSchoolDetailStub() {
  const { id } = useParams();
  return <div>Detail route: {id}</div>;
}

function renderMicroSchoolListPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/micro-schools" element={<MicroSchoolListPage />} />
      <Route path="/micro-schools/:id" element={<MicroSchoolDetailStub />} />
    </Routes>,
    {
      route: '/micro-schools',
      user: { role: 'ADM' },
    }
  );
}

describe('MicroSchoolListPage', () => {
  it('loads schools, filters them by search, and navigates to detail', async () => {
    const user = userEvent.setup();

    server.use(http.get('/api/v1/micro-schools', () => apiResponse(microSchools)));

    renderMicroSchoolListPage();

    expect(await screen.findByText('Atlas Learning Hub')).toBeInTheDocument();
    expect(screen.getByText('Sahara Micro-School')).toBeInTheDocument();

    await user.type(screen.getByRole('searchbox'), 'Atlas');

    await waitFor(() => {
      expect(screen.queryByText('Sahara Micro-School')).not.toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Atlas Learning Hub/i }));

    expect(await screen.findByText('Detail route: school-1')).toBeInTheDocument();
  });

  it('shows an error banner when schools fail to load', async () => {
    server.use(
      http.get('/api/v1/micro-schools', () => apiErrorResponse('Unable to load micro-schools'))
    );

    renderMicroSchoolListPage();

    expect(await screen.findByText('Unable to load micro-schools')).toBeInTheDocument();
  });

  it('stays empty until the school list resolves', async () => {
    server.use(
      http.get('/api/v1/micro-schools', async () => {
        await delay(200);
        return apiResponse(microSchools);
      })
    );

    renderMicroSchoolListPage();

    expect(screen.queryByText('Atlas Learning Hub')).not.toBeInTheDocument();
    expect(await screen.findByText('Atlas Learning Hub')).toBeInTheDocument();
  });
});
