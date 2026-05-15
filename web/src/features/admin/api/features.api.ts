import { api } from '@/core/api/client';

export interface FeatureToggle {
  id: string;
  feature_key: string;
  display_name: string;
  description: string | null;
  enabled_globally: boolean;
  enabled_school_ids: string[];
  enabled_role_codes: string[];
  created_at: string;
  updated_at: string | null;
}

export interface FeatureTogglePayload {
  display_name?: string;
  description?: string | null;
  enabled_globally?: boolean;
  enabled_school_ids?: string[];
  enabled_role_codes?: string[];
}

export const featuresService = {
  listActiveFeatures() {
    return api.get<{ features: string[] }>('/features/active');
  },

  listFeatures() {
    return api.list<FeatureToggle>('/features');
  },

  getFeature(toggleId: string) {
    return api.get<FeatureToggle>(`/features/${toggleId}`);
  },

  createFeature(payload: {
    feature_key: string;
    display_name: string;
    description?: string | null;
    enabled_globally?: boolean;
    enabled_school_ids?: string[];
    enabled_role_codes?: string[];
  }) {
    return api.post<FeatureToggle>('/features', payload);
  },

  updateFeature(toggleId: string, payload: FeatureTogglePayload) {
    return api.put<FeatureToggle>(`/features/${toggleId}`, payload);
  },

  deleteFeature(toggleId: string) {
    return api.delete<void>(`/features/${toggleId}`);
  },
};
