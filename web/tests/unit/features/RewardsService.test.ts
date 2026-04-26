import { describe, expect, it } from 'vitest';
import { xpThresholdForLevel } from '@/features/rewards/rewards.service';

describe('xpThresholdForLevel', () => {
  it('returns 0 for level 1', () => {
    expect(xpThresholdForLevel(1)).toBe(0);
  });

  it('returns 0 for level 0 (edge case)', () => {
    expect(xpThresholdForLevel(0)).toBe(0);
  });

  it('returns 0 for negative levels (edge case)', () => {
    expect(xpThresholdForLevel(-1)).toBe(0);
  });

  it('computes correct XP threshold for level 2', () => {
    // 50 * (2-1) * 2 = 50 * 1 * 2 = 100
    expect(xpThresholdForLevel(2)).toBe(100);
  });

  it('computes correct XP threshold for level 3', () => {
    // 50 * (3-1) * 3 = 50 * 2 * 3 = 300
    expect(xpThresholdForLevel(3)).toBe(300);
  });

  it('computes correct XP threshold for level 5', () => {
    // 50 * (5-1) * 5 = 50 * 4 * 5 = 1000
    expect(xpThresholdForLevel(5)).toBe(1000);
  });

  it('computes correct XP threshold for level 10', () => {
    // 50 * (10-1) * 10 = 50 * 9 * 10 = 4500
    expect(xpThresholdForLevel(10)).toBe(4500);
  });

  it('XP thresholds increase with level', () => {
    let prev = 0;
    for (let level = 2; level <= 20; level++) {
      const current = xpThresholdForLevel(level);
      expect(current).toBeGreaterThan(prev);
      prev = current;
    }
  });
});
