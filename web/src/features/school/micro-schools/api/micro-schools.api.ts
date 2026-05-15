import { api } from '@/core/api/client';
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
} from '@/entities/school/micro-school/model/types';

const EMPTY_UUID = '00000000-0000-0000-0000-000000000000';

export const microSchoolsService = {
  listMicroSchools(params?: Record<string, string | number | undefined>) {
    return api.get<MicroSchool[]>('/micro/schools', params);
  },

  createMicroSchool(payload: CreateMicroSchoolPayload) {
    return api.post<MicroSchool>('/micro/schools', payload);
  },

  async getMicroSchoolDetail(id: string) {
    const response = await api.list<MicroSchool>('/micro/schools', { id });
    const school = response.data.find((item) => item.id === id) ??
      response.data[0] ?? {
        id,
        name: '',
        description: '',
        location: '',
        city: '',
        capacity: 0,
        student_count: 0,
        status: 'active',
      };

    return {
      data: school,
      meta: response.meta,
    };
  },

  updateMicroSchool(id: string, payload: Partial<CreateMicroSchoolPayload>) {
    return api.put<MicroSchool>(`/micro/schools/${id}`, payload);
  },

  deleteMicroSchool(id: string) {
    return api.put<void>(`/micro/schools/${id}`, { status: 'closed', id });
  },

  getEnrollments(id: string) {
    return api.list<MicroEnrollment>('/micro/enrollments', { micro_school_id: id });
  },

  async enrollStudent(id: string, payload: EnrollStudentPayload) {
    const groupsResponse = await api.list<MicroGroup>(`/micro/schools/${id}/groups`);
    return api.post<MicroEnrollment>('/micro/enrollments', {
      micro_group_id: groupsResponse.data[0]?.id ?? id,
      child_name: payload.student_name,
      parent_id: EMPTY_UUID,
      date_of_birth: '2020-01-01',
      status: 'active',
    });
  },

  unenrollStudent(id: string, enrollmentId: string) {
    return api.delete<void>(`/micro/schools/${id}/enrollments/${enrollmentId}`);
  },

  getPayments(id: string) {
    return api.list<MicroPayment>('/micro/payments', { micro_school_id: id });
  },

  createPayment(id: string, payload: CreateMicroPaymentPayload) {
    return api.post<MicroPayment>('/micro/payments', {
      micro_school_id: id,
      parent_id: EMPTY_UUID,
      child_enrollment_id: EMPTY_UUID,
      amount: payload.amount,
      currency: 'MAD',
      period_type: 'monthly',
      period_start: new Date().toISOString().slice(0, 10),
      period_end: new Date().toISOString().slice(0, 10),
      status: payload.status ?? 'pending',
    });
  },

  getResources(id: string) {
    return api.list<MicroResource>('/micro/resources', { micro_school_id: id });
  },

  addResource(id: string, payload: CreateMicroResourcePayload) {
    return api.post<MicroResource>('/micro/resources', {
      micro_school_id: id,
      title: payload.title,
      description: payload.description,
      resource_type: payload.type,
      age_group: 'all',
      language: payload.language,
      file_url: payload.file_url,
      is_premium: false,
    });
  },

  async getProgress(id: string) {
    const response = await api.list<MicroProgressLog>('/micro/progress-logs', {
      micro_school_id: id,
    });
    const totalLogs = response.data.length;
    const studentIds = new Set(response.data.map((item) => item.student_id));
    const series = response.data.map((item) => ({
      label: item.date,
      value: 1,
    }));

    return {
      data: {
        average_progress: totalLogs === 0 ? 0 : 100,
        active_students: studentIds.size,
        completion_rate: totalLogs === 0 ? 0 : 100,
        series,
      } satisfies MicroProgressOverview,
      meta: response.meta,
    };
  },

  async getStudentProgress(id: string, studentId: string) {
    const response = await api.list<MicroProgressLog>('/micro/progress-logs', {
      micro_school_id: id,
      student_id: studentId,
    });

    return {
      data: {
        student_id: studentId,
        student_name: studentId,
        milestones_completed: response.data.length,
        progress_rate: response.data.length === 0 ? 0 : 100,
        series: response.data.map((item) => ({
          label: item.date,
          value: 1,
        })),
      } satisfies MicroStudentProgress,
      meta: response.meta,
    };
  },

  createGroup(id: string, payload: CreateMicroGroupPayload) {
    return api.post<MicroGroup>('/micro/groups', {
      micro_school_id: id,
      name: payload.name,
      age_range_min: 2,
      age_range_max: 6,
    });
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
