export type UserRole =
  | 'SYS'
  | 'SUP'
  | 'ADM'
  | 'DIR'
  | 'TCH'
  | 'EDUCATOR'
  | 'PAR'
  | 'STD'
  | 'CONTENT_MGR'
  | 'PUBLIC';

export type SchoolStatus = 'active' | 'suspended' | 'trial';

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface School {
  id: string;
  name: string;
  code: string;
  address: string;
  city: string;
  status?: SchoolStatus;
  region?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string | null;
}

export interface Class {
  id: string;
  code?: string;
  name: string;
  level: string;
  school_id: string;
  academic_year: string;
  teacher_count?: number;
  student_count?: number;
}

export interface Student {
  id: string;
  user_id: string;
  class_id: string;
  enrollment_date: string;
  school_id?: string;
  status?: string;
}

export interface Grade {
  id: string;
  student_id: string;
  assessment_id: string;
  value: number;
  comment?: string;
  updated_at?: string;
}

export interface Invoice {
  id: string;
  school_id: string;
  student_id: string;
  amount: number;
  currency: 'MAD';
  status: InvoiceStatus;
  due_date?: string;
  issued_date?: string;
}
