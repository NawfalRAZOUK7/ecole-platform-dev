import { describe, expect, it } from 'vitest';
import { resolveDesignContext } from '@/shared/ui/designContext';

describe('resolveDesignContext', () => {
  it('keeps formal as the default for non-student school contexts', () => {
    const context = resolveDesignContext({
      role: 'ADM',
      schoolType: 'formal',
      themeMode: 'light',
    });

    expect(context.designMode).toBe('formal');
    expect(context.schoolType).toBe('formal');
    expect(context.appliedTheme).toBe('light');
  });

  it('uses settings design_mode before school_type', () => {
    const context = resolveDesignContext({
      role: 'DIR',
      schoolType: 'formal',
      schoolSettings: { design_mode: 'informal' },
    });

    expect(context.designMode).toBe('informal');
  });

  it('forces informal for educator and micro routes', () => {
    expect(resolveDesignContext({ role: 'EDUCATOR', schoolType: 'formal' }).designMode).toBe(
      'informal',
    );
    expect(resolveDesignContext({ role: 'ADM', pathname: '/micro-schools' }).designMode).toBe(
      'informal',
    );
  });

  it('keeps student themes aligned with the school theme mode', () => {
    expect(resolveDesignContext({ role: 'STD', themeMode: 'light' }).appliedTheme).toBe('light');
    expect(resolveDesignContext({ role: 'STD', themeMode: 'dark' }).appliedTheme).toBe('dark');
  });
});
