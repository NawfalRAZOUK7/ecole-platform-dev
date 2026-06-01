/**
 * Tests for src/shared/ui/navIcons.ts
 */
import { describe, it, expect } from 'vitest';
import { getNavIcon, NAV_ICON_MAP, DEFAULT_NAV_ICON } from '@/shared/ui/navIcons';

describe('navIcons', () => {
  it('NAV_ICON_MAP is a non-empty object', () => {
    expect(Object.keys(NAV_ICON_MAP).length).toBeGreaterThan(0);
  });

  it('DEFAULT_NAV_ICON is defined', () => {
    expect(DEFAULT_NAV_ICON).toBeDefined();
  });

  it('getNavIcon returns an icon for known keys', () => {
    // Try some known navigation keys from the Layout
    const knownKeys = ['nav.adminDashboard', 'nav.adminUsers', 'nav.attendance', 'nav.gradebook'];
    knownKeys.forEach((key) => {
      const icon = getNavIcon(key);
      expect(icon).toBeDefined();
    });
  });

  it('getNavIcon returns DEFAULT_NAV_ICON for unknown keys', () => {
    const icon = getNavIcon('nav.unknownKey12345');
    expect(icon).toBe(DEFAULT_NAV_ICON);
  });

  it('getNavIcon returns a non-null icon component', () => {
    const icon = getNavIcon('nav.adminDashboard');
    // Lucide icons are objects with a render function or a forward-ref component
    expect(icon).toBeDefined();
    expect(icon).not.toBeNull();
  });

  it('all NAV_ICON_MAP values are defined', () => {
    Object.values(NAV_ICON_MAP).forEach((icon) => {
      expect(icon).toBeDefined();
    });
  });
});
