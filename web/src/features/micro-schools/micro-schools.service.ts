import { api } from '@/services/api/client';
import type {
  CreateMicroPaymentPayload,
  CreateMicroResourcePayload,
  CreateMicroSchoolPayload,
  EnrollStudentPayload,
  MicroEnrollment,
  MicroPayment,
  MicroProgressOverview,
  MicroResource,
  MicroSchool,
  MicroStudentProgress,
} from './micro-schools.types';

export const microSchoolsService = {
  listMicroSchools(params?: Record<string, string | number | undefined>) {
    return api.get<MicroSchool[]>('/micro-schools', params);
  },

  createMicroSchool(payload: CreateMicroSchoolPayload) {
    return api.post<MicroSchool>('/micro-schools', payload);
  },

  getMicroSchoolDetail(id: string) {
    return api.get<MicroSchool>(`/micro-schools/${id}`);
  },

  updateMicroSchool(id: string, payload: Partial<CreateMicroSchoolPayload>) {
    return api.put<MicroSchool>(`/micro-schools/${id}`, payload);
  },

  deleteMicroSchool(id: string) {
    return api.delete<void>(`/micro-schools/${id}`);
  },

  getEnrollments(id: string) {
    return api.get<MicroEnrollment[]>(`/micro-schools/${id}/enrollments`);
  },

  enrollStudent(id: string, payload: EnrollStudentPayload) {
    return api.post<MicroEnrollment>(`/micro-schools/${id}/enrollments`, payload);
  },

  unenrollStudent(id: string, enrollmentId: string) {
    return api.delete<void>(`/micro-schools/${id}/enrollments/${enrollmentId}`);
  },

  getPayments(id: string) {
    return api.get<MicroPayment[]>(`/micro-schools/${id}/payments`);
  },

  createPayment(id: string, payload: CreateMicroPaymentPayload) {
    return api.post<MicroPayment>(`/micro-schools/${id}/payments`, payload);
  },

  getResources(id: string) {
    return api.get<MicroResource[]>(`/micro-schools/${id}/resources`);
  },

  addResource(id: string, payload: CreateMicroResourcePayload) {
    return api.post<MicroResource>(`/micro-schools/${id}/resources`, payload);
  },

  getProgress(id: string) {
    return api.get<MicroProgressOverview>(`/micro-schools/${id}/progress`);
  },

  getStudentProgress(id: string, studentId: string) {
    return api.get<MicroStudentProgress>(`/micro-schools/${id}/progress/${studentId}`);
  },
};
