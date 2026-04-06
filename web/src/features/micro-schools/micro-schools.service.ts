import { api } from '@/services/api/client';
import type {
  CreateMicroGroupPayload,
  CreateMicroPaymentPayload,
  CreateMicroProgressLogPayload,
  CreateMicroResourcePayload,
  CreateMicroSchoolPayload,
  EnrollStudentPayload,
  MicroEnrollment,
  MicroGroup,
  MicroPayment,
  MicroPaymentAnalytics,
  MicroProgressLog,
  MicroProgressOverview,
  MicroResource,
  MicroSchool,
  MicroStudentProgress,
} from './micro-schools.types';

export const microSchoolsService = {
  listMicroSchools(params?: Record<string, string | number | undefined>) {
    return api.get<MicroSchool[]>('/micro/schools', params);
  },

  createMicroSchool(payload: CreateMicroSchoolPayload) {
    return api.post<MicroSchool>('/micro/schools', payload);
  },

  getMicroSchoolDetail(id: string) {
    return api.get<MicroSchool>(`/micro/schools/${id}`);
  },

  updateMicroSchool(id: string, payload: Partial<CreateMicroSchoolPayload>) {
    return api.put<MicroSchool>(`/micro/schools/${id}`, payload);
  },

  deleteMicroSchool(id: string) {
    return api.delete<void>(`/micro/schools/${id}`);
  },

  getEnrollments(id: string) {
    return api.get<MicroEnrollment[]>(`/micro/schools/${id}/enrollments`);
  },

  enrollStudent(id: string, payload: EnrollStudentPayload) {
    return api.post<MicroEnrollment>(`/micro/schools/${id}/enrollments`, payload);
  },

  unenrollStudent(id: string, enrollmentId: string) {
    return api.delete<void>(`/micro/schools/${id}/enrollments/${enrollmentId}`);
  },

  getPayments(id: string) {
    return api.get<MicroPayment[]>(`/micro/schools/${id}/payments`);
  },

  createPayment(id: string, payload: CreateMicroPaymentPayload) {
    return api.post<MicroPayment>(`/micro/schools/${id}/payments`, payload);
  },

  getResources(id: string) {
    return api.get<MicroResource[]>(`/micro/schools/${id}/resources`);
  },

  addResource(id: string, payload: CreateMicroResourcePayload) {
    return api.post<MicroResource>(`/micro/schools/${id}/resources`, payload);
  },

  getProgress(id: string) {
    return api.get<MicroProgressOverview>(`/micro/schools/${id}/progress`);
  },

  getStudentProgress(id: string, studentId: string) {
    return api.get<MicroStudentProgress>(`/micro/schools/${id}/progress/${studentId}`);
  },

  createGroup(id: string, payload: CreateMicroGroupPayload) {
    return api.post<MicroGroup>(`/micro/schools/${id}/groups`, payload);
  },

  getGroups(id: string) {
    return api.get<MicroGroup[]>(`/micro/schools/${id}/groups`);
  },

  createEnrollment(payload: EnrollStudentPayload & { micro_school_id: string }) {
    return api.post<MicroEnrollment>('/micro/enrollments', payload);
  },

  listEnrollments(params?: Record<string, string | number | undefined>) {
    return api.get<MicroEnrollment[]>('/micro/enrollments', params);
  },

  createTopLevelPayment(payload: CreateMicroPaymentPayload & { micro_school_id: string }) {
    return api.post<MicroPayment>('/micro/payments', payload);
  },

  listPayments(params?: Record<string, string | number | undefined>) {
    return api.get<MicroPayment[]>('/micro/payments', params);
  },

  getPaymentAnalytics(params?: Record<string, string | number | undefined>) {
    return api.get<MicroPaymentAnalytics>('/micro/payments/analytics', params);
  },

  createTopLevelResource(payload: CreateMicroResourcePayload & { micro_school_id: string }) {
    return api.post<MicroResource>('/micro/resources', payload);
  },

  listTopLevelResources(params?: Record<string, string | number | undefined>) {
    return api.get<MicroResource[]>('/micro/resources', params);
  },

  createProgressLog(payload: CreateMicroProgressLogPayload) {
    return api.post<MicroProgressLog>('/micro/progress-logs', payload);
  },

  listProgressLogs(params?: Record<string, string | number | undefined>) {
    return api.get<MicroProgressLog[]>('/micro/progress-logs', params);
  },
};
