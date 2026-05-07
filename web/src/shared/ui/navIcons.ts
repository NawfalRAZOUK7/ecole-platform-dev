/**
 * Navigation icon mapping — Lucide icons replacing emoji.
 */

import type { LucideIcon } from 'lucide-react';
import {
  LayoutDashboard,
  Users,
  Ticket,
  Medal,
  ClipboardList,
  FileText,
  BarChart3,
  UserPlus,
  Link,
  BookOpen,
  Backpack,
  GitBranch,
  ScrollText,
  School,
  Banknote,
  FileSpreadsheet,
  Receipt,
  Clock,
  CalendarDays,
  Briefcase,
  TrendingUp,
  Home,
  GraduationCap,
  PenTool,
  CheckSquare,
  BarChart2,
  Library,
  Gamepad2,
  HelpCircle,
  Grid,
  Database,
  Star,
  Newspaper,
  Settings,
  Sparkles,
  MapPin,
  MessageSquare,
  Megaphone,
  Bell,
  FileBarChart,
  FolderOpen,
  Zap,
  Send,
  Target,
  Ruler,
  UserCircle,
  Lock,
  History,
  Inbox,
  ShieldCheck,
} from 'lucide-react';

export const NAV_ICON_MAP: Record<string, LucideIcon> = {
  // Admin
  'nav.adminDashboard': LayoutDashboard,
  'nav.adminUsers': Users,
  'nav.adminInvitations': Ticket,
  'nav.adminBadges': Medal,
  'nav.adminAudit': ClipboardList,
  'nav.adminJustifications': FileText,
  'nav.adminAnalytics': BarChart3,
  'nav.adminBatchRegister': UserPlus,
  'nav.adminFamilyLinks': Link,
  'nav.adminPrograms': BookOpen,
  'nav.adminEnrollments': Backpack,
  'nav.adminEquivalences': GitBranch,
  'nav.adminEligibilityRules': ScrollText,
  'nav.adminSettings': School,
  'nav.adminFeeStructures': Banknote,
  'nav.adminFeeAssignments': FileSpreadsheet,
  'nav.adminGenerateInvoices': Receipt,

  // Billing
  'nav.billingSiblingPolicy': Link,
  'nav.billingLateFees': Clock,
  'nav.billingPaymentPlans': CalendarDays,

  // Shared
  'nav.budgets': Briefcase,
  'nav.financialHealth': TrendingUp,
  'nav.microSchools': Home,

  // Teacher
  'nav.teacherClasses': GraduationCap,
  'nav.teacherCourses': BookOpen,
  'nav.teacherAssignments': PenTool,
  'nav.teacherSubmissions': FileText,
  'nav.teacherAttendance': CheckSquare,
  'nav.teacherAssessments': BarChart2,
  'nav.teacherContentLibrary': Library,
  'nav.teacherQuizzes': HelpCircle,
  'nav.teacherClassProgress': TrendingUp,
  'nav.games': Gamepad2,
  'nav.rubrics': Grid,
  'nav.questionBank': Database,

  // Student
  'nav.studentHome': Home,
  'nav.studentContent': BookOpen,
  'nav.studentQuizzes': HelpCircle,
  'nav.studentGames': Gamepad2,
  'nav.studentWriting': PenTool,
  'nav.progress': TrendingUp,
  'nav.myRewards': Star,
  'nav.submissions': Send,
  'nav.skills': Target,

  // Parent
  'nav.myChildren': Users,
  'nav.feed': Newspaper,
  'nav.rewards': Star,
  'nav.parentProgress': TrendingUp,
  'nav.justification': FileText,
  'nav.invoices': Receipt,

  // Shared modules
  'nav.timetable': CalendarDays,
  'nav.timetableConstraints': Settings,
  'nav.timetableGenerate': Sparkles,
  'nav.calendar': CalendarDays,
  'nav.calendarHolidays': MapPin,
  'nav.messages': MessageSquare,
  'nav.announcements': Megaphone,
  'nav.notifications': Bell,
  'nav.reports': FileBarChart,
  'nav.documents': FolderOpen,
  'nav.notificationSettings': Zap,
  'nav.content': BookOpen,
  'nav.results': BarChart2,
  'nav.activities': Target,
  'nav.compliance': Ruler,

  // Profile
  'nav.profile': UserCircle,
  'nav.sessions': Lock,
  'nav.twoFactor': ShieldCheck,
  'nav.loginHistory': History,
};

// Fallback for icons not in the map
export const DEFAULT_NAV_ICON = Inbox;

export function getNavIcon(labelKey: string): LucideIcon {
  return NAV_ICON_MAP[labelKey] || DEFAULT_NAV_ICON;
}
