import type {
  CalendarClassOption,
  CalendarEventItem,
  CalendarView,
  EventFormState,
  EventRsvpStatus,
  EventType,
} from './types';

import { ROLE_CODES } from '@/shared/constants/roles';
export const ROLE_OPTIONS = ROLE_CODES;

export interface CalendarFiltersProps {
  availableClasses: CalendarClassOption[];
  copyState: string | null;
  icalUrl: string;
  selectedClassId: string;
  selectedDate: Date;
  selectedDayItems: CalendarEventItem[];
  selectedTypes: EventType[];
  onChangeClassId: (value: string) => void;
  onCopyIcal: () => void;
  onOpenDetails: (item: CalendarEventItem) => void;
  onToggleType: (type: EventType) => void;
}

export interface CalendarGridProps {
  anchorDate: Date;
  filteredItems: CalendarEventItem[];
  selectedDate: Date;
  view: CalendarView;
  onChangeAnchorDate: (direction: -1 | 1) => void;
  onOpenDetails: (item: CalendarEventItem) => void;
  onSelectDate: (day: Date) => void;
}

export interface EventFormProps {
  availableClasses: CalendarClassOption[];
  initialEvent?: CalendarEventItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
  userRole: string;
}

export interface EventDetailProps {
  event: CalendarEventItem;
  onClose?: () => void;
  onDelete?: () => void;
  onEdit?: () => void;
  onRsvp?: (status: EventRsvpStatus) => void;
  showOpenPageLink?: boolean;
}

export type EventFormUpdater = (value: EventFormState) => void;
