import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT, STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { calendarService, type CalendarEventPayload, type CalendarEventsFilters } from './calendar.service';

export const calendarQueryKeys = {
  all: ['calendar'] as const,
  events: () => [...calendarQueryKeys.all, 'events'] as const,
  eventList: (filters: CalendarEventsFilters) => [...calendarQueryKeys.events(), 'list', filters] as const,
  options: () => [...calendarQueryKeys.all, 'options'] as const,
  eventDetails: () => [...calendarQueryKeys.all, 'event'] as const,
  eventDetail: (id: string) => [...calendarQueryKeys.eventDetails(), id] as const,
};

export function useCalendarEvents(filters: CalendarEventsFilters) {
  return useInfiniteQuery({
    queryKey: calendarQueryKeys.eventList(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      calendarService.listEvents({
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCalendarOptions() {
  return useQuery({
    queryKey: calendarQueryKeys.options(),
    queryFn: async () => (await calendarService.getOptions()).data,
    staleTime: STALE_CONTENT,
  });
}

export function useCalendarEvent(
  eventId: string | null | undefined,
  options: { enabled?: boolean; refetchInterval?: number | false } = {}
) {
  const enabled = Boolean(eventId) && (options.enabled ?? true);

  return useQuery({
    queryKey: eventId ? calendarQueryKeys.eventDetail(eventId) : [...calendarQueryKeys.eventDetails(), 'pending'],
    queryFn: async () => (await calendarService.getEvent(eventId!)).data,
    enabled,
    staleTime: STALE_DEFAULT,
    refetchInterval: options.refetchInterval,
  });
}

export function useCreateCalendarEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CalendarEventPayload) => (await calendarService.createEvent(payload)).data,
    onSuccess: async (event) => {
      queryClient.setQueryData(calendarQueryKeys.eventDetail(event.id), event);
      await queryClient.invalidateQueries({ queryKey: calendarQueryKeys.events() });
    },
  });
}

export function useUpdateCalendarEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: CalendarEventPayload }) =>
      (await calendarService.updateEvent(id, payload)).data,
    onSuccess: async (event) => {
      queryClient.setQueryData(calendarQueryKeys.eventDetail(event.id), event);
      await queryClient.invalidateQueries({ queryKey: calendarQueryKeys.events() });
    },
  });
}

export function useDeleteCalendarEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await calendarService.deleteEvent(id);
      return id;
    },
    onSuccess: async (eventId) => {
      queryClient.removeQueries({ queryKey: calendarQueryKeys.eventDetail(eventId) });
      await queryClient.invalidateQueries({ queryKey: calendarQueryKeys.events() });
    },
  });
}

export function useCalendarEventRsvp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: 'attending' | 'maybe' | 'declined' }) => {
      await calendarService.respondToEvent(id, status);
      return id;
    },
    onSuccess: async (eventId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: calendarQueryKeys.events() }),
        queryClient.invalidateQueries({ queryKey: calendarQueryKeys.eventDetail(eventId) }),
      ]);
    },
  });
}
