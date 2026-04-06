import type { AttendanceClassStats, AttendanceRecord } from '@/features/attendance/attendance.types';
import type { BudgetEnvelope } from '@/features/budgets/budgets.types';
import type { StudentGradeRow } from '@/features/gradebook/gradebook.types';
import type { InvoiceSummary } from '@/features/invoices/invoices.service';
import type { ClassOption, StudentItem } from '@/features/teacher/teacher.service';
import type { UserProfile } from '@/services/auth/AuthContext';

export interface TestSchool {
  id: string;
  name: string;
  code: string;
  status: 'active' | 'inactive';
  timezone: string;
}

export interface AttendanceClassResponse {
  class_id: string;
  stats: AttendanceClassStats;
  records: AttendanceRecord[];
}

let sequence = 0;

function nextId(prefix: string) {
  sequence += 1;
  return `${prefix}-${sequence}`;
}

export function createSchool(overrides: Partial<TestSchool> = {}): TestSchool {
  return {
    id: nextId('school'),
    name: 'Ecole Horizon',
    code: 'SCH-001',
    status: 'active',
    timezone: 'Africa/Casablanca',
    ...overrides,
  };
}

export function createUser(overrides: Partial<UserProfile> = {}): UserProfile {
  const schoolId = overrides.school_id ?? createSchool().id;
  return {
    id: nextId('user'),
    email: 'teacher@ecole.test',
    full_name: 'Test User',
    role: 'TCH',
    school_id: schoolId,
    totp_enabled: false,
    permissions: ['read:all'],
    memberships: [
      {
        school_id: schoolId,
        role: overrides.role ?? 'TCH',
        status: 'active',
      },
    ],
    ...overrides,
  };
}

export function createClass(overrides: Partial<ClassOption> = {}): ClassOption {
  return {
    id: nextId('class'),
    code: '6A',
    name: 'Sixieme A',
    ...overrides,
  };
}

export function createStudent(overrides: Partial<StudentItem> = {}): StudentItem {
  return {
    id: nextId('student'),
    full_name: 'Student Example',
    email: 'student@ecole.test',
    enrollment_status: 'active',
    ...overrides,
  };
}

export function createGrade(overrides: Partial<StudentGradeRow> = {}): StudentGradeRow {
  return {
    assessment_id: nextId('assessment'),
    title: 'Quiz 1',
    date: '2026-04-01',
    weight: 1,
    type: 'quiz',
    value: 16,
    ...overrides,
  };
}

export function createInvoice(overrides: Partial<InvoiceSummary> = {}): InvoiceSummary {
  return {
    id: nextId('invoice'),
    invoice_number: 'INV-2026-001',
    student_id: createStudent().id,
    student_name: 'Student Example',
    label: 'Tuition April',
    total_amount: 1200,
    total_cents: 120000,
    currency: 'MAD',
    status: 'pending',
    issued_date: '2026-04-01',
    due_date: '2026-04-10',
    ...overrides,
  };
}

export function createBudget(overrides: Partial<BudgetEnvelope> = {}): BudgetEnvelope {
  return {
    id: nextId('budget'),
    name: 'Q2 Operations',
    total_amount: 50000,
    spent_amount: 12000,
    remaining_amount: 38000,
    status: 'active',
    currency: 'MAD',
    start_date: '2026-04-01',
    end_date: '2026-06-30',
    created_at: '2026-04-01T09:00:00Z',
    ...overrides,
  };
}

export function createAttendanceRecord(overrides: Partial<AttendanceRecord> = {}): AttendanceRecord {
  const student = createStudent();
  const classItem = createClass();
  return {
    id: nextId('attendance'),
    student_id: student.id,
    student_name: student.full_name,
    class_id: classItem.id,
    date: '2026-04-06',
    status: 'present',
    justified: false,
    justification: undefined,
    marked_by: createUser({ role: 'TCH' }).id,
    ...overrides,
  };
}
