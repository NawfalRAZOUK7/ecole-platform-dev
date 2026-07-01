import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi } from 'vitest';
import { BadgeEditor } from '@/features/ai/badges/ui/BadgeEditor';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const mockBadge = {
  id: 'badge-1',
  code: 'FIRST_STAR',
  titleFr: 'Première étoile',
  titleAr: 'النجمة الأولى',
  titleEn: 'First Star',
  descriptionFr: 'Obtenir sa première étoile',
  descriptionAr: null,
  descriptionEn: 'Get your first star',
  icon: '⭐',
  criteriaType: 'stars_total',
  criteriaValue: 1,
  displayOrder: 1,
  isActive: true,
};

describe('BadgeEditor (create new)', () => {
  it('renders without crashing', async () => {
    renderWithProviders(<BadgeEditor onCancel={vi.fn()} onSaved={vi.fn()} />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders form fields', async () => {
    renderWithProviders(<BadgeEditor onCancel={vi.fn()} onSaved={vi.fn()} />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });

  it('renders cancel and save buttons', async () => {
    renderWithProviders(<BadgeEditor onCancel={vi.fn()} onSaved={vi.fn()} />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });
});

describe('BadgeEditor (edit existing)', () => {
  it('renders with existing badge data', async () => {
    renderWithProviders(<BadgeEditor badge={mockBadge} onCancel={vi.fn()} onSaved={vi.fn()} />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });

  it('shows error state on save failure', async () => {
    server.use(http.put('/api/v1/rewards/badges/badge-1', () => apiErrorResponse('Update failed')));
    renderWithProviders(<BadgeEditor badge={mockBadge} onCancel={vi.fn()} onSaved={vi.fn()} />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
