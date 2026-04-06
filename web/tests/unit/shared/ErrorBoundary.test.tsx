import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ErrorBoundary } from '@/shared/ui/ErrorBoundary';
import { renderWithProviders } from '../../utils/render';

describe('ErrorBoundary', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('catches an error and shows the fallback UI', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    function BrokenComponent() {
      throw new Error('Boom');
    }

    renderWithProviders(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Boom')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('retry button resets the error state', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();
    let shouldThrow = true;

    function BrokenComponent() {
      if (shouldThrow) {
        throw new Error('Boom');
      }
      return <div>Recovered</div>;
    }

    renderWithProviders(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>
    );

    shouldThrow = false;
    await user.click(screen.getByRole('button', { name: /retry/i }));

    expect(screen.getByText('Recovered')).toBeInTheDocument();
  });
});
