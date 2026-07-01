import { waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { GenerateQuizPage } from '@/features/lms/question-bank/ui/GenerateQuizPage';
import { renderWithProviders } from '../../../utils/render';

describe('GenerateQuizPage', () => {
  it('renders without crashing', async () => {
    renderWithProviders(<GenerateQuizPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('renders the generate form', async () => {
    renderWithProviders(<GenerateQuizPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(100);
    });
  });

  it('renders with subject input', async () => {
    renderWithProviders(<GenerateQuizPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML).toContain('input');
    });
  });

  it('renders back button', async () => {
    renderWithProviders(<GenerateQuizPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(50);
    });
    expect(document.body.innerHTML).toContain('button');
  });
});
