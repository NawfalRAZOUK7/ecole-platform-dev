// Auto-generated from features/auth/api/auth.api.ts + features/user/profile

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  school_id: string;
  role: string;
  requires_2fa?: boolean;
  temp_token?: string;
  message?: string;
}

export interface RegisterResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  school_id: string;
  role: string;
  email_verification_required: boolean;
}

export interface LoginHistoryEntry {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  location: string | null;
  status: 'success' | 'failed';
  created_at: string;
}

export type ProfileFieldValue = string | number | boolean | null | undefined;

export interface StudentProfileData {
  student_number?: string | null;
  date_of_birth?: string | null;
  class_level?: string | null;
  nationality?: string | null;
  [key: string]: ProfileFieldValue;
}

export interface ParentProfileData {
  relationship_type?: string | null;
  cin_number?: string | null;
  address?: string | null;
  profession?: string | null;
  emergency_phone?: string | null;
  [key: string]: ProfileFieldValue;
}

export interface TeacherProfileData {
  employee_id?: string | null;
  subject_specialty?: string | null;
  qualification?: string | null;
  reward_points?: number | null;
  [key: string]: ProfileFieldValue;
}

export interface ProfileResponse {
  user_id?: string;
  email?: string;
  full_name?: string;
  phone?: string | null;
  role?: string;
  school_id?: string;
  student_profile?: StudentProfileData | null;
  parent_profile?: ParentProfileData | null;
  teacher_profile?: TeacherProfileData | null;
}

export interface AdminUserProfileResponse extends ProfileResponse {
  user_id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: string;
  school_id: string;
}

export interface ChildEntry {
  user_id: string;
  full_name: string;
  email: string;
  link_id: string;
  linked_at: string | null;
  student_profile: {
    class_level: string | null;
    date_of_birth: string | null;
    student_number: string | null;
    nationality: string | null;
  } | null;
}

export interface SessionItem {
  id: string;
  source: string;
  user_agent: string | null;
  ip_address: string | null;
  device_name: string | null;
  created_at: string;
  last_active: string | null;
  is_current: boolean;
}
