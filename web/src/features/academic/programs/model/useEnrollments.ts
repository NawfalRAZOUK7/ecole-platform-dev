/**
 * React Query hooks for the admin Enrollments list (G49 Phase 2.b).
 */

import { useInfiniteQuery } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { enrollmentsService, type AdminEnrollmentFilters } from '../api/enrollments.api';

export const enrollmentQueryKeys = {
  all: ['enrollments'] as const,
  list: (filters: AdminEnrollmentFilters) =>
    [...enrollmentQueryKeys.all, 'admin-list', filters] as const,
};

export function useAdminEnrollmentsQuery(filters: AdminEnrollmentFilters) {
  return useInfiniteQuery({
    queryKey: enrollmentQueryKeys.list(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      enrollmentsService.listAdminEnrollments({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_DEFAULT,
  });
}
