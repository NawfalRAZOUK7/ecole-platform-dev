import { api } from '@/core/api/client';
import type {
  ComplianceDashboard,
  ComplianceReport,
  CreateCurriculumMappingPayload,
  CreateMenCurriculumPayload,
  CreateMenObjectivePayload,
  CurriculumMapping,
  GenerateComplianceReportPayload,
  MenCurriculum,
  MenObjective,
} from '@/entities/admin/compliance/model/types';

export const complianceService = {
  listCurricula(
    params: {
      level?: string;
      grade?: string;
      subject?: string;
      academic_year?: string;
      is_active?: boolean;
    } = {},
  ) {
    return api.list<MenCurriculum>('/compliance/curricula', {
      ...params,
      is_active: params.is_active === undefined ? undefined : String(params.is_active),
    });
  },

  createCurriculum(payload: CreateMenCurriculumPayload) {
    return api.post<MenCurriculum>('/compliance/curricula', payload);
  },

  listObjectives(curriculumId: string, trimester?: number) {
    return api.list<MenObjective>(`/compliance/curricula/${curriculumId}/objectives`, {
      trimester,
    });
  },

  createObjective(curriculumId: string, payload: CreateMenObjectivePayload) {
    return api.post<MenObjective>(`/compliance/curricula/${curriculumId}/objectives`, payload);
  },

  createMapping(payload: CreateCurriculumMappingPayload) {
    return api.post<CurriculumMapping>('/compliance/mappings', payload);
  },

  listMappings(
    params: {
      curriculum_id?: string;
      objective_id?: string;
      course_id?: string;
      content_item_id?: string;
    } = {},
  ) {
    return api.list<CurriculumMapping>('/compliance/mappings', params);
  },

  deleteMapping(mappingId: string) {
    return api.delete<void>(`/compliance/mappings/${mappingId}`);
  },

  getDashboard(params: {
    academic_year_id: string;
    level?: string;
    grade?: string;
    subject?: string;
  }) {
    return api.get<ComplianceDashboard>('/compliance/dashboard', params);
  },

  generateReport(payload: GenerateComplianceReportPayload) {
    return api.post<ComplianceReport>('/compliance/reports/generate', payload);
  },

  listReports(
    params: {
      curriculum_id?: string;
      academic_year_id?: string;
    } = {},
  ) {
    return api.list<ComplianceReport>('/compliance/reports', params);
  },

  getReport(reportId: string) {
    return api.get<ComplianceReport>(`/compliance/reports/${reportId}`);
  },

  downloadReportUrl(reportId: string) {
    return `/api/v1/compliance/reports/${reportId}/download`;
  },

  downloadReport(reportId: string) {
    return api.get<{ download_url: string }>(`/compliance/reports/${reportId}/download`);
  },
};
