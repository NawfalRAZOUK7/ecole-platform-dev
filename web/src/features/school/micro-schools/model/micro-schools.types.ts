export interface MicroSchool {
  id: string;
  name: string;
  description?: string;
  location: string;
  city: string;
  capacity: number;
  student_count: number;
  status: 'active' | 'suspended' | 'closed';
}

export interface MicroEnrollment {
  id: string;
  micro_school_id: string;
  student_id: string;
  student_name: string;
  status: 'active' | 'withdrawn';
  enrolled_at: string;
}

export interface MicroPayment {
  id: string;
  micro_school_id: string;
  student_id?: string;
  amount: number;
  status: 'pending' | 'paid' | 'overdue';
  paid_at?: string | null;
  created_at: string;
}

export interface MicroResource {
  id: string;
  title: string;
  description?: string | null;
  type: 'activity_sheet' | 'song' | 'game' | 'lesson_plan';
  language: 'ar' | 'fr' | 'en';
  file_url?: string | null;
}

export interface MicroProgressOverview {
  average_progress: number;
  active_students: number;
  completion_rate: number;
  series: Array<{ label: string; value: number }>;
}

export interface MicroStudentProgress {
  student_id: string;
  student_name: string;
  milestones_completed: number;
  progress_rate: number;
  series: Array<{ label: string; value: number }>;
}

export interface CreateMicroSchoolPayload {
  name: string;
  description?: string;
  location: string;
  city: string;
  capacity: number;
  status?: MicroSchool['status'];
}

export interface EnrollStudentPayload {
  student_id: string;
  student_name: string;
  payment_amount: number;
  payment_status: 'pending' | 'paid';
}

export interface CreateMicroPaymentPayload {
  student_id?: string;
  amount: number;
  status?: 'pending' | 'paid' | 'overdue';
}

export interface CreateMicroResourcePayload {
  title: string;
  description?: string;
  type: MicroResource['type'];
  language: MicroResource['language'];
  file_url?: string;
}

export interface MicroGroup {
  id: string;
  micro_school_id: string;
  name: string;
  description?: string | null;
  student_ids: string[];
}

export interface CreateMicroGroupPayload {
  name: string;
  description?: string;
  student_ids?: string[];
}

export interface MicroProgressLog {
  id: string;
  student_id: string;
  micro_school_id: string;
  date: string;
  note: string;
  created_at: string;
}

export interface CreateMicroProgressLogPayload {
  student_id: string;
  micro_school_id: string;
  date: string;
  note: string;
}

export interface MicroPaymentAnalytics {
  total_collected: number;
  total_pending: number;
  total_overdue: number;
  payment_rate: number;
}
