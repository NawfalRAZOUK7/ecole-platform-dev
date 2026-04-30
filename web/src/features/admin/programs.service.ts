/**
 * Academic Program Management — typed API client (G49 Phase 2).
 *
 * Maps to the backend endpoints created in:
 *   app/api/v1/programs.py            — programs CRUD + POST /enrollments/:id/program
 *   app/api/v1/student_academic.py    — /students/:id/program-history etc.
 */

import { api } from '@/services/api/client';
import { getAccessToken } from '@/services/api/client';
import i18next from 'i18next';

// ---------------------------------------------------------------------------
// Domain types (mirror app/schemas/programs.py)
// ---------------------------------------------------------------------------
export type ProgramAssignmentReason =
  | 'INITIAL'
  | 'TRANSFER'
  | 'PROMOTION'
  | 'CORRECTION'
  | 'READMISSION';

export interface Program {
  id: string;
  school_id: string;
  code: string;
  name: string;
  level: string | null;
  description: string | null;
  is_active: boolean;
  version_label: string;
  effective_from: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ProgramSummary {
  id: string;
  code: string;
  name: string;
  version_label: string;
}

export interface ProgramCreatePayload {
  code: string;
  name: string;
  level?: string | null;
  description?: string | null;
  version_label?: string;
  effective_from?: string | null;
}

export interface ProgramUpdatePayload {
  name?: string;
  level?: string | null;
  description?: string | null;
  is_active?: boolean;
  version_label?: string;
  effective_from?: string | null;
}

export interface ProgramAssignPayload {
  program_id: string;
  /** G50a Phase 3.1: optional version pin. Must belong to program_id. */
  program_version_id?: string | null;
  reason_code: ProgramAssignmentReason;
  reason_note?: string | null;
}

export interface ProgramAssignmentEvent {
  id: string;
  school_id: string;
  student_id: string;
  academic_year_id: string;
  period_id: string | null;
  from_program_id: string | null;
  to_program_id: string;
  from_enrollment_id: string | null;
  to_enrollment_id: string | null;
  reason_code: ProgramAssignmentReason;
  reason_note: string | null;
  actor_user_id: string | null;
  occurred_at: string;
}

export interface AcademicTimelineEntry {
  enrollment_id: string;
  academic_year_id: string;
  academic_year_label: string | null;
  academic_year_start: string;
  academic_year_end: string;
  period_id: string;
  period_label: string | null;
  period_start: string;
  period_end: string;
  class_id: string;
  class_code: string;
  class_name: string;
  program: ProgramSummary | null;
  status: string;
}

export interface CurrentProgram {
  student_id: string;
  academic_year_id: string | null;
  period_id: string | null;
  enrollment_id: string | null;
  program: ProgramSummary | null;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------
export interface ProgramVersion {
  id: string;
  school_id: string;
  program_id: string;
  version_label: string;
  description: string | null;
  effective_from: string | null;
  retired_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface ProgramEquivalence {
  id: string;
  school_id: string;
  from_program_id: string;
  to_program_id: string;
  kind: 'EQUIVALENT' | 'SUPERSEDES' | 'PARTIAL';
  note: string | null;
  ratified_at: string | null;
  ratified_by: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AcademicSnapshot {
  id: string;
  school_id: string;
  student_id: string;
  academic_year_id: string;
  snapshot_kind: 'YEAR_END' | 'MID_YEAR' | 'MANUAL';
  snapshot_data: Record<string, unknown>;
  taken_at: string;
  taken_by: string | null;
}

export interface TranscriptProgramSummary {
  id: string;
  code: string | null;
  name: string | null;
  version_label: string | null;
}

export interface TranscriptPayload {
  student: Record<string, unknown>;
  school: Record<string, unknown>;
  academic_year: Record<string, unknown>;
  source: Record<string, unknown>;
  enrollments: Array<Record<string, unknown>>;
  program_events: Array<Record<string, unknown>>;
  grades_summary: Array<Record<string, unknown>>;
  attendance_summary: Record<string, unknown>;
  equivalence_resolutions: Array<{
    program: TranscriptProgramSummary;
    resolved_program_ids: string[];
    resolved_programs: TranscriptProgramSummary[];
  }>;
}

export type EligibilityRuleKind = 'PROMOTION' | 'ADMISSION' | 'TRANSFER';

export interface EligibilityRule {
  id: string;
  school_id: string;
  kind: EligibilityRuleKind;
  target_program_id: string;
  condition_type: string;
  condition_params: Record<string, unknown>;
  message_key: string;
  is_active: boolean;
}

export interface EligibilityCheckResult {
  student_id: string;
  target_program_id: string;
  kind: EligibilityRuleKind;
  eligible: boolean;
  rules: Array<{
    rule_id: string;
    condition_type: string;
    message_key: string;
    passed: boolean;
    detail: string | null;
  }>;
}

export const programsService = {
  // Catalog
  listPrograms(activeOnly = true) {
    return api.list<Program>('/programs', { active_only: activeOnly ? 1 : 0 });
  },

  // Phase 3.1 — versions
  listProgramVersions(programId: string) {
    return api.list<ProgramVersion>(`/programs/${programId}/versions`);
  },

  createProgramVersion(
    programId: string,
    body: {
      version_label: string;
      description?: string | null;
      effective_from?: string | null;
      is_active?: boolean;
    },
  ) {
    return api.post<ProgramVersion>(`/programs/${programId}/versions`, body);
  },

  updateProgramVersion(
    programId: string,
    versionId: string,
    body: {
      description?: string | null;
      effective_from?: string | null;
      retired_at?: string | null;
      is_active?: boolean;
    },
  ) {
    return api.patch<ProgramVersion>(`/programs/${programId}/versions/${versionId}`, body);
  },

  // Phase 3.2 — equivalences
  listProgramEquivalences(programId?: string) {
    return api.list<ProgramEquivalence>(
      '/program-equivalences',
      programId ? { program_id: programId } : undefined,
    );
  },

  createProgramEquivalence(body: {
    from_program_id: string;
    to_program_id: string;
    kind: 'EQUIVALENT' | 'SUPERSEDES' | 'PARTIAL';
    note?: string | null;
    ratified_at?: string | null;
  }) {
    return api.post<ProgramEquivalence>('/program-equivalences', body);
  },

  deleteProgramEquivalence(equivalenceId: string) {
    return api.delete<void>(`/program-equivalences/${equivalenceId}`);
  },

  // Phase 3.3 — snapshots
  listStudentSnapshots(studentId: string) {
    return api.list<AcademicSnapshot>(`/students/${studentId}/snapshots`);
  },

  takeSnapshot(body: {
    student_id: string;
    academic_year_id: string;
    snapshot_kind?: 'YEAR_END' | 'MID_YEAR' | 'MANUAL';
  }) {
    return api.post<AcademicSnapshot>('/academic-snapshots', body);
  },

  getSnapshotTranscript(snapshotId: string) {
    return api.get<TranscriptPayload>(`/academic-snapshots/${snapshotId}/transcript`);
  },

  async getSnapshotTranscriptHtml(snapshotId: string, lang = i18next.language || 'fr') {
    const headers: Record<string, string> = {
      Accept: 'text/html',
      'Accept-Language': lang,
    };
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(
      `/api/v1/academic-snapshots/${snapshotId}/transcript/html?lang=${encodeURIComponent(lang)}`,
      {
        headers,
        credentials: 'include',
      },
    );
    if (!response.ok) {
      throw new Error('Transcript preview failed');
    }
    return response.text();
  },

  async downloadSnapshotTranscriptPdf(snapshotId: string, lang = i18next.language || 'fr') {
    const headers: Record<string, string> = {
      Accept: 'application/pdf',
      'Accept-Language': lang,
    };
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(
      `/api/v1/academic-snapshots/${snapshotId}/transcript/pdf?lang=${encodeURIComponent(lang)}`,
      {
        headers,
        credentials: 'include',
      },
    );
    if (!response.ok) {
      throw new Error('Transcript PDF download failed');
    }
    return response.blob();
  },

  getStudentTranscript(
    studentId: string,
    academicYearId: string,
    mode: 'preview' | 'snapshot' = 'preview',
  ) {
    return api.get<TranscriptPayload>(`/students/${studentId}/transcript`, {
      academic_year_id: academicYearId,
      mode,
    });
  },

  async getStudentTranscriptHtml(
    studentId: string,
    academicYearId: string,
    mode: 'preview' | 'snapshot' = 'preview',
    lang = i18next.language || 'fr',
  ) {
    const headers: Record<string, string> = {
      Accept: 'text/html',
      'Accept-Language': lang,
    };
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(
      `/api/v1/students/${studentId}/transcript/html?academic_year_id=${encodeURIComponent(academicYearId)}&mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`,
      {
        headers,
        credentials: 'include',
      },
    );
    if (!response.ok) {
      throw new Error('Transcript preview failed');
    }
    return response.text();
  },

  async downloadStudentTranscriptPdf(
    studentId: string,
    academicYearId: string,
    mode: 'preview' | 'snapshot' = 'preview',
    lang = i18next.language || 'fr',
  ) {
    const headers: Record<string, string> = {
      Accept: 'application/pdf',
      'Accept-Language': lang,
    };
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(
      `/api/v1/students/${studentId}/transcript/pdf?academic_year_id=${encodeURIComponent(academicYearId)}&mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`,
      {
        headers,
        credentials: 'include',
      },
    );
    if (!response.ok) {
      throw new Error('Transcript PDF download failed');
    }
    return response.blob();
  },

  // Phase 3.4 — eligibility
  listEligibilityRules(
    filters: {
      kind?: EligibilityRuleKind;
      target_program_id?: string;
      active_only?: boolean;
    } = {},
  ) {
    return api.list<EligibilityRule>('/eligibility/rules', {
      kind: filters.kind,
      target_program_id: filters.target_program_id,
      active_only: filters.active_only === false ? 0 : 1,
    });
  },

  createEligibilityRule(body: {
    kind: EligibilityRuleKind;
    target_program_id: string;
    condition_type: string;
    condition_params?: Record<string, unknown>;
    message_key: string;
    is_active?: boolean;
  }) {
    return api.post<EligibilityRule>('/eligibility/rules', body);
  },

  deleteEligibilityRule(ruleId: string) {
    return api.delete<void>(`/eligibility/rules/${ruleId}`);
  },

  checkEligibility(studentId: string, kind: EligibilityRuleKind, targetProgramId: string) {
    return api.get<EligibilityCheckResult>(`/students/${studentId}/eligibility`, {
      kind,
      target_program_id: targetProgramId,
    });
  },

  getProgram(programId: string) {
    return api.get<Program>(`/programs/${programId}`);
  },

  createProgram(body: ProgramCreatePayload) {
    return api.post<Program>('/programs', body);
  },

  updateProgram(programId: string, body: ProgramUpdatePayload) {
    return api.patch<Program>(`/programs/${programId}`, body);
  },

  // Assignment
  assignProgram(enrollmentId: string, body: ProgramAssignPayload) {
    return api.post<ProgramAssignmentEvent>(`/enrollments/${enrollmentId}/program`, body);
  },

  // Read views — student academic history
  getProgramHistory(studentId: string) {
    return api.list<ProgramAssignmentEvent>(`/students/${studentId}/program-history`);
  },

  getAcademicTimeline(studentId: string) {
    return api.list<AcademicTimelineEntry>(`/students/${studentId}/academic-timeline`);
  },

  getCurrentProgram(studentId: string) {
    return api.get<CurrentProgram>(`/students/${studentId}/current-program`);
  },
};
