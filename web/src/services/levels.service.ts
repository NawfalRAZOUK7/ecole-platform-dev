/**
 * Level-age mapping service — G46.
 * Fetches platform-level or school-specific level→age mappings.
 */

import { api } from './api/client';

export interface LevelAgeMapping {
  id: string;
  level_code: string;
  label_fr: string;
  label_ar: string | null;
  label_en: string | null;
  default_age_min: number;
  default_age_max: number;
  display_order: number;
  school_id: string | null;
}

/** Fetch all level-age mappings, optionally filtered by school. */
export async function fetchLevelMappings(schoolId?: string): Promise<LevelAgeMapping[]> {
  const params: Record<string, string | undefined> = schoolId
    ? { school_id: schoolId }
    : {};
  const response = await api.get<LevelAgeMapping[]>('/levels', params);
  return response.data;
}

/** Build a lookup map from level_code → mapping for fast access. */
export function buildLevelMap(mappings: LevelAgeMapping[]): Record<string, LevelAgeMapping> {
  return Object.fromEntries(mappings.map((m) => [m.level_code, m]));
}
