import { api } from '@/core/api/client';

export interface CurrentConsentEntry {
  id: string;
  topic: string;
  channel: string;
  scope_type: string;
  status: 'opted_in' | 'opted_out';
  created_at: string;
  updated_at: string;
}

export interface ConsentHistoryEntry {
  id: string;
  action_type: string;
  outcome: string;
  target_id: string | null;
  actor_id: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface ConsentLogResponse {
  user_id: string;
  current_consents: CurrentConsentEntry[];
  change_history: ConsentHistoryEntry[];
}

export interface GDPRDeletionResponse {
  user_id: string;
  anonymized_at: string | null;
  status: string;
  message: string;
}

export const gdprService = {
  getDataExport(userId: string) {
    return api.get<Record<string, unknown>>(`/users/${userId}/data-export`);
  },

  requestDataDeletion(userId: string) {
    return api.post<GDPRDeletionResponse>(`/users/${userId}/data-deletion`, {});
  },

  getConsentLog(userId: string) {
    return api.get<ConsentLogResponse>(`/users/${userId}/consent-log`);
  },
};
