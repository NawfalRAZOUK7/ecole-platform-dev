export interface NotificationItem {
  id: string;
  school_id: string;
  user_id: string;
  parent_id: string;
  event_ref: string | null;
  title: string;
  body: string | null;
  category: string;
  priority: string;
  action_url: string | null;
  action_payload: Record<string, unknown> | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  updated_at: string | null;
  channels: string[];
}

export interface NotificationPreference {
  channel: string;
  category: string;
  enabled: boolean;
  digest_frequency: string;
}

export interface ConsentItem {
  id: string;
  user_id: string;
  school_id: string;
  topic: string;
  channel: string;
  scope_type: string;
  scope_ref_id: string | null;
  status: 'opted_in' | 'opted_out';
}

export interface NotificationPreferencesResponse {
  user_id: string;
  preferences: NotificationPreference[];
}

export interface NotificationDigestResponse {
  user_id: string;
  digest_frequency: string;
  send_hour: number;
  timezone: string;
}

export interface DeviceItem {
  id: string;
  user_id: string;
  platform: string;
  device_name: string | null;
  token_preview: string;
  last_active_at: string;
  created_at: string;
}
