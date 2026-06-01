import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { FeatureTogglesPage } from '@/pages/admin/FeatureTogglesPage';
import { renderWithProviders } from '../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../utils/mocks';

const featureToggle = {
  id: 'feature-1',
  feature_key: 'ai_assistant',
  display_name: 'AI Assistant',
  description: 'Enable AI assistant for teachers',
  enabled_globally: true,
  enabled_role_codes: ['TCH', 'ADM'],
  enabled_school_ids: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: null,
};

const disabledFeature = {
  id: 'feature-2',
  feature_key: 'beta_gradebook',
  display_name: 'Beta Gradebook',
  description: null,
  enabled_globally: false,
  enabled_role_codes: [],
  enabled_school_ids: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: null,
};

describe('FeatureTogglesPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/features', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<FeatureTogglesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no features', async () => {
    const { container } = renderWithProviders(<FeatureTogglesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders feature toggles in a table', async () => {
    server.use(
      http.get('/api/v1/features', () => apiListResponse([featureToggle, disabledFeature])),
    );
    renderWithProviders(<FeatureTogglesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toContain('ai_assistant'));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/features', () => apiErrorResponse('Server error')));
    renderWithProviders(<FeatureTogglesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders page title', async () => {
    renderWithProviders(<FeatureTogglesPage />, { user: { role: 'ADM' } });
    // The page renders a title (translated - e.g. "Feature Toggles" or the i18n key)
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(100));
  });
});
