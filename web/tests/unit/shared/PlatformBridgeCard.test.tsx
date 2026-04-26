import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PlatformBridgeCard } from '@/shared/ui/PlatformBridgeCard';
import { renderWithProviders } from '../../utils/render';

describe('PlatformBridgeCard', () => {
  it('renders mobile variant with title, description, and default icon', () => {
    renderWithProviders(
      <PlatformBridgeCard
        targetPlatform="mobile"
        title="Interactive Coloring"
        description="This activity is designed for tablets."
      />,
    );

    expect(screen.getByText('Interactive Coloring')).toBeInTheDocument();
    expect(screen.getByText('This activity is designed for tablets.')).toBeInTheDocument();
    // Default mobile icon
    expect(screen.getByText('📱')).toBeInTheDocument();
  });

  it('renders web variant with web-specific default icon', () => {
    renderWithProviders(
      <PlatformBridgeCard
        targetPlatform="web"
        title="Advanced Admin Tools"
        description="Bulk enrollment available on web."
      />,
    );

    expect(screen.getByText('Advanced Admin Tools')).toBeInTheDocument();
    expect(screen.getByText('Bulk enrollment available on web.')).toBeInTheDocument();
    expect(screen.getByText('💻')).toBeInTheDocument();
  });

  it('uses custom icon when provided', () => {
    renderWithProviders(
      <PlatformBridgeCard
        targetPlatform="mobile"
        title="Coloring"
        description="Use the app."
        icon="🎨"
      />,
    );

    expect(screen.getByText('🎨')).toBeInTheDocument();
    expect(screen.queryByText('📱')).not.toBeInTheDocument();
  });

  it('renders with RTL direction', () => {
    const { container } = renderWithProviders(
      <PlatformBridgeCard targetPlatform="mobile" title="تلوين" description="وصف" />,
    );

    const card = container.querySelector('.platform-bridge-card');
    expect(card).toHaveAttribute('dir', 'rtl');
  });

  it('shows correct platform badge label for mobile', () => {
    renderWithProviders(
      <PlatformBridgeCard targetPlatform="mobile" title="Test" description="Desc" />,
    );

    // Default value from i18n fallback
    expect(screen.getByText('متوفر على التطبيق')).toBeInTheDocument();
  });

  it('shows correct platform badge label for web', () => {
    renderWithProviders(
      <PlatformBridgeCard targetPlatform="web" title="Test" description="Desc" />,
    );

    expect(screen.getByText('متوفر على الويب')).toBeInTheDocument();
  });
});
