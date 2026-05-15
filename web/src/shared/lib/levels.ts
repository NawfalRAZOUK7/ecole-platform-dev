import { api } from '@/core/api/client';

export interface LevelAgeMapping {
  level: string;
  min_age_months: number;
  max_age_months: number;
  default_age_min: number;
  default_age_max: number;
  display_label: string;
}

export async function fetchLevelMappings(): Promise<LevelAgeMapping[]> {
  const { data } = await api.get<LevelAgeMapping[]>('/lms/levels/mappings');
  return data.map((mapping) => ({
    ...mapping,
    default_age_min: mapping.default_age_min ?? Math.floor((mapping.min_age_months ?? 0) / 12),
    default_age_max: mapping.default_age_max ?? Math.ceil((mapping.max_age_months ?? 0) / 12),
  }));
}

export function buildLevelMap(mappings: LevelAgeMapping[]): Record<string, LevelAgeMapping> {
  return Object.fromEntries(mappings.map((m) => [m.level, m]));
}
