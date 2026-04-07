import { api } from '@/services/api/client';

export interface SchoolRecord {
  id: string;
  name: string;
  code: string;
  address: string | null;
  city: string | null;
  phone: string | null;
  email: string | null;
  timezone: string;
  default_language: string;
}

export const schoolsService = {
  getSchool(schoolId: string) {
    return api.get<SchoolRecord>(`/schools/${schoolId}`);
  },

  updateSchool(
    schoolId: string,
    payload: Partial<Pick<SchoolRecord, 'name' | 'address' | 'city' | 'phone'>>
  ) {
    return api.patch<SchoolRecord>(`/schools/${schoolId}`, payload);
  },
};
