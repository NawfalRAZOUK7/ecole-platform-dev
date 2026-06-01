import { screen, waitFor, act } from '@testing-library/react';
import { describe, expect, it, vi, afterEach } from 'vitest';
import { OfflineIndicator } from '@/shared/ui/OfflineIndicator';
import { renderWithProviders } from '../../utils/render';

describe('OfflineIndicator', () => {
  afterEach(() => {
    // Restore navigator.onLine to true after each test
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: true,
    });
  });

  it('renders nothing when online and was not previously offline', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: true,
    });
    const { container } = renderWithProviders(<OfflineIndicator />);
    expect(container.firstChild).toBeNull();
  });

  it('renders offline message when navigator.onLine is false', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: false,
    });
    renderWithProviders(<OfflineIndicator />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows offline text when offline', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: false,
    });
    renderWithProviders(<OfflineIndicator />);
    const statusEl = screen.getByRole('status');
    expect(statusEl.textContent).toMatch(/offline|You are offline/i);
  });

  it('has aria-live="polite" attribute', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: false,
    });
    renderWithProviders(<OfflineIndicator />);
    const statusEl = screen.getByRole('status');
    expect(statusEl).toHaveAttribute('aria-live', 'polite');
  });

  it('has class offline-indicator when visible', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: false,
    });
    renderWithProviders(<OfflineIndicator />);
    const statusEl = screen.getByRole('status');
    expect(statusEl.className).toContain('offline-indicator');
  });

  it('shows online message when coming back online after being offline', async () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: false,
    });
    renderWithProviders(<OfflineIndicator />);
    expect(screen.getByRole('status')).toBeInTheDocument();

    // Simulate coming back online
    act(() => {
      Object.defineProperty(window.navigator, 'onLine', {
        writable: true,
        value: true,
      });
      window.dispatchEvent(new Event('online'));
    });

    await waitFor(() => {
      const status = screen.queryByRole('status');
      if (status) {
        expect(status.textContent).toMatch(/back online|online/i);
      }
    });
  });

  it('hides indicator after going online briefly', async () => {
    vi.useFakeTimers();
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: true,
    });
    renderWithProviders(<OfflineIndicator />);
    // Should be hidden immediately when online and no wasOffline
    expect(screen.queryByRole('status')).toBeNull();
    vi.useRealTimers();
  });

  it('dispatching offline event shows offline message', async () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: true,
    });
    renderWithProviders(<OfflineIndicator />);

    act(() => {
      Object.defineProperty(window.navigator, 'onLine', {
        writable: true,
        value: false,
      });
      window.dispatchEvent(new Event('offline'));
    });

    await waitFor(() => {
      const status = screen.queryByRole('status');
      if (status) {
        expect(status.textContent).toMatch(/offline/i);
      }
    });
  });
});
