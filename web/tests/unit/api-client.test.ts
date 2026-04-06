import { describe, expect, it } from 'vitest';

describe('API Client', () => {
  it('should be importable', async () => {
    const mod = await import('@/services/api/client');

    expect(mod.api).toBeDefined();
  });
});
