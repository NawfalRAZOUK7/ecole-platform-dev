/**
 * Tests for src/shared/lib/levels.ts
 * Covers: fetchLevelMappings (API call + defaults computation) and buildLevelMap.
 */
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import { buildLevelMap, fetchLevelMappings, type LevelAgeMapping } from '@/shared/lib/levels';

// NOTE: api.get<T>() returns ApiResponse<T> = { data: T, meta: ... }
// (cf. src/core/api/client.ts line 287). All MSW responses must wrap their
// payload in a `{ data: ... }` envelope.
const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };

describe('shared/lib/levels — fetchLevelMappings', () => {
  it('returns mappings unchanged when defaults are already present', async () => {
    server.use(
      http.get('/api/v1/lms/levels/mappings', () =>
        HttpResponse.json({
          data: [
            {
              level: 'CP',
              min_age_months: 72,
              max_age_months: 84,
              default_age_min: 6,
              default_age_max: 7,
              display_label: 'Cours Préparatoire',
            },
          ],
          meta: META,
        }),
      ),
    );

    const result = await fetchLevelMappings();

    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({
      level: 'CP',
      default_age_min: 6,
      default_age_max: 7,
      display_label: 'Cours Préparatoire',
    });
  });

  it('computes default_age_min/max from months when defaults are missing', async () => {
    server.use(
      http.get('/api/v1/lms/levels/mappings', () =>
        HttpResponse.json({
          data: [
            {
              level: 'CE1',
              min_age_months: 84,
              max_age_months: 95,
              // missing defaults on purpose
              display_label: 'Cours Élémentaire 1',
            },
          ],
          meta: META,
        }),
      ),
    );

    const [mapping] = await fetchLevelMappings();

    // floor(84/12) = 7, ceil(95/12) = 8
    expect(mapping.default_age_min).toBe(7);
    expect(mapping.default_age_max).toBe(8);
  });

  it('falls back to zero when month fields are absent', async () => {
    server.use(
      http.get('/api/v1/lms/levels/mappings', () =>
        HttpResponse.json({
          data: [
            {
              level: 'unknown',
              display_label: 'Unknown',
              // no min/max ages, no defaults
            },
          ],
          meta: META,
        }),
      ),
    );

    const [mapping] = await fetchLevelMappings();
    expect(mapping.default_age_min).toBe(0);
    expect(mapping.default_age_max).toBe(0);
  });

  it('propagates HTTP errors', async () => {
    server.use(
      http.get('/api/v1/lms/levels/mappings', () =>
        HttpResponse.json({ error: 'server error' }, { status: 500 }),
      ),
    );

    await expect(fetchLevelMappings()).rejects.toBeDefined();
  });
});

describe('shared/lib/levels — buildLevelMap', () => {
  const sample: LevelAgeMapping[] = [
    {
      level: 'CP',
      min_age_months: 72,
      max_age_months: 84,
      default_age_min: 6,
      default_age_max: 7,
      display_label: 'Cours Préparatoire',
    },
    {
      level: 'CE1',
      min_age_months: 84,
      max_age_months: 96,
      default_age_min: 7,
      default_age_max: 8,
      display_label: 'Cours Élémentaire 1',
    },
  ];

  it('returns an empty object for an empty input', () => {
    expect(buildLevelMap([])).toEqual({});
  });

  it('keys mappings by their level field', () => {
    const map = buildLevelMap(sample);
    expect(Object.keys(map).sort()).toEqual(['CE1', 'CP']);
    expect(map.CP.display_label).toBe('Cours Préparatoire');
    expect(map.CE1.default_age_max).toBe(8);
  });

  it('keeps the last mapping when two share the same level (last-write-wins)', () => {
    const duplicate: LevelAgeMapping = {
      ...sample[0],
      display_label: 'CP (alias)',
    };
    const map = buildLevelMap([sample[0], duplicate]);
    expect(map.CP.display_label).toBe('CP (alias)');
  });
});
