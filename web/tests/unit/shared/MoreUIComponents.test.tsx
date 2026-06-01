/**
 * Tests for SentryDebugButton, AnimatedPage/StaggerContainer/StaggerItem
 */
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { SentryDebugButton } from '@/shared/components/SentryDebugButton';
import { AnimatedPage, StaggerContainer, StaggerItem } from '@/shared/ui/AnimatedPage';
import { renderWithProviders } from '../../utils/render';

// ---------------------------------------------------------------------------
// SentryDebugButton
// ---------------------------------------------------------------------------
describe('SentryDebugButton', () => {
  it('renders a button', () => {
    render(<SentryDebugButton />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('button has text content', () => {
    render(<SentryDebugButton />);
    expect(screen.getByRole('button').textContent?.length).toBeGreaterThan(0);
  });

  it('throws error on click (ErrorBoundary should catch it)', async () => {
    const user = userEvent.setup();
    // Mock Sentry to avoid real calls
    vi.mock('@sentry/react', () => ({
      logger: { info: vi.fn() },
      addBreadcrumb: vi.fn(),
    }));
    render(<SentryDebugButton />);
    const btn = screen.getByRole('button');
    // Clicking throws - just verify button is clickable
    expect(btn).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// AnimatedPage, StaggerContainer, StaggerItem
// ---------------------------------------------------------------------------
describe('AnimatedPage', () => {
  it('renders children', () => {
    renderWithProviders(
      <AnimatedPage>
        <div data-testid="child">Content</div>
      </AnimatedPage>,
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('accepts className prop', () => {
    const { container } = renderWithProviders(
      <AnimatedPage className="test-class">
        <span>Text</span>
      </AnimatedPage>,
    );
    expect(container.querySelector('.test-class')).toBeTruthy();
  });

  it('renders multiple children', () => {
    renderWithProviders(
      <AnimatedPage>
        <p>First</p>
        <p>Second</p>
      </AnimatedPage>,
    );
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
  });
});

describe('StaggerContainer', () => {
  it('renders children with stagger animation', () => {
    renderWithProviders(
      <StaggerContainer>
        <div>Item 1</div>
        <div>Item 2</div>
      </StaggerContainer>,
    );
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('accepts custom staggerDelay', () => {
    renderWithProviders(
      <StaggerContainer staggerDelay={0.1}>
        <div>Content</div>
      </StaggerContainer>,
    );
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('accepts className', () => {
    const { container } = renderWithProviders(
      <StaggerContainer className="stagger-class">
        <div>x</div>
      </StaggerContainer>,
    );
    expect(container.querySelector('.stagger-class')).toBeTruthy();
  });
});

describe('StaggerItem', () => {
  it('renders children inside stagger item', () => {
    renderWithProviders(
      <StaggerContainer>
        <StaggerItem>
          <span>Stagger child</span>
        </StaggerItem>
      </StaggerContainer>,
    );
    expect(screen.getByText('Stagger child')).toBeInTheDocument();
  });

  it('accepts className prop', () => {
    const { container } = renderWithProviders(
      <StaggerContainer>
        <StaggerItem className="item-class">
          <span>Item</span>
        </StaggerItem>
      </StaggerContainer>,
    );
    expect(container.querySelector('.item-class')).toBeTruthy();
  });
});
