import { describe, expect, it } from 'vitest';
import {
  getRoleAccent,
  getSubjectColor,
  subjectColors,
  darkSubjectColors,
} from '@/shared/ui/tokens';

describe('design tokens', () => {
  it('returns subject colors with normalized keys and fallback', () => {
    expect(getSubjectColor('Math')).toBe(subjectColors.math);
    expect(getSubjectColor('islamic studies')).toBe(subjectColors.islamic_studies);
    expect(getSubjectColor('unknown')).toBe(subjectColors.default);
  });

  it('uses dark subject colors for dark and kids-dark themes', () => {
    expect(getSubjectColor('math', 'dark')).toBe(darkSubjectColors.math);
    expect(getSubjectColor('math', 'kids-dark')).toBe(darkSubjectColors.math);
  });

  it('returns role accents with a stable fallback', () => {
    expect(getRoleAccent('ADM')).toBe('#2563eb');
    expect(getRoleAccent('dir')).toBe('#4f46e5');
    expect(getRoleAccent('unknown')).toBe('#2563eb');
  });
});
