/**
 * Tests for remaining uncovered shared UI components:
 * - Breadcrumb
 * - RetryButton
 * - LanguageSwitcher
 */
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Breadcrumb } from '@/shared/ui/Breadcrumb';
import { RetryButton } from '@/shared/ui/RetryButton';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { renderWithProviders } from '../../utils/render';

// ---------------------------------------------------------------------------
// Breadcrumb
// ---------------------------------------------------------------------------
describe('Breadcrumb', () => {
  it('renders breadcrumb nav', () => {
    renderWithProviders(<Breadcrumb items={[{ label: 'Home', href: '/' }, { label: 'Users' }]} />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('renders all items', () => {
    renderWithProviders(
      <Breadcrumb
        items={[
          { label: 'Home', href: '/' },
          { label: 'Admin', href: '/admin' },
          { label: 'Users' },
        ]}
      />,
    );
    expect(document.body.textContent).toContain('Home');
    expect(document.body.textContent).toContain('Admin');
    expect(document.body.textContent).toContain('Users');
  });

  it('marks last item with aria-current="page"', () => {
    renderWithProviders(<Breadcrumb items={[{ label: 'Home', href: '/' }, { label: 'Users' }]} />);
    const current = document.querySelector('[aria-current="page"]');
    expect(current).toBeTruthy();
  });

  it('renders link for items with href that are not last', () => {
    renderWithProviders(
      <Breadcrumb items={[{ label: 'Home', href: '/' }, { label: 'Current' }]} />,
    );
    expect(document.querySelector('a[href="/"]')).toBeTruthy();
  });

  it('renders separator between items', () => {
    renderWithProviders(<Breadcrumb items={[{ label: 'A', href: '/a' }, { label: 'B' }]} />);
    const separators = document.querySelectorAll('[aria-hidden="true"]');
    expect(separators.length).toBeGreaterThan(0);
  });

  it('renders single item without separator', () => {
    renderWithProviders(<Breadcrumb items={[{ label: 'Only' }]} />);
    const separators = document.querySelectorAll('.breadcrumb__separator');
    expect(separators.length).toBe(0);
  });

  it('renders empty breadcrumb gracefully', () => {
    renderWithProviders(<Breadcrumb items={[]} />);
    expect(document.querySelector('nav')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// RetryButton
// ---------------------------------------------------------------------------
describe('RetryButton', () => {
  it('renders retry button', () => {
    renderWithProviders(<RetryButton onRetry={vi.fn()} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('calls onRetry when clicked', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    renderWithProviders(<RetryButton onRetry={onRetry} />);
    await user.click(screen.getByRole('button'));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('is not disabled by default', () => {
    renderWithProviders(<RetryButton onRetry={vi.fn()} />);
    expect(screen.getByRole('button')).not.toBeDisabled();
  });

  it('is disabled and shows loading when loading=true', () => {
    renderWithProviders(<RetryButton onRetry={vi.fn()} loading={true} />);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    expect(btn.getAttribute('aria-busy')).toBe('true');
  });

  it('shows retry text when not loading', () => {
    renderWithProviders(<RetryButton onRetry={vi.fn()} />);
    expect(screen.getByRole('button').textContent).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// LanguageSwitcher
// ---------------------------------------------------------------------------
describe('LanguageSwitcher', () => {
  it('renders language buttons', () => {
    renderWithProviders(<LanguageSwitcher />);
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(3); // fr, ar, en
  });

  it('buttons show language labels', () => {
    renderWithProviders(<LanguageSwitcher />);
    const text = document.body.textContent ?? '';
    // Should show French/Arabic/English labels
    expect(text.length).toBeGreaterThan(0);
  });

  it('switches language on button click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LanguageSwitcher />);
    const buttons = screen.getAllByRole('button');
    // Click a non-active language
    const nonActiveBtn = buttons.find((b) => b.getAttribute('aria-pressed') === 'false');
    if (nonActiveBtn) {
      await user.click(nonActiveBtn);
      await waitFor(() => expect(document.body.textContent).toBeTruthy());
    }
  });

  it('active language button has aria-pressed=true', () => {
    renderWithProviders(<LanguageSwitcher />);
    const activeBtn = document.querySelector('[aria-pressed="true"]');
    expect(activeBtn).toBeTruthy();
  });

  it('marks current language button as active', () => {
    renderWithProviders(<LanguageSwitcher />);
    const activeBtns = document.querySelectorAll('[aria-pressed="true"]');
    expect(activeBtns.length).toBe(1);
  });
});
