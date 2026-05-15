#!/usr/bin/env python3
"""
Phase 1: Create entities/ layer by extracting pure business types + read-only APIs.
Strategy: Copy (not move) types to entities; create GET-only API files.
Feature files keep their originals — we update imports to use entities for types.
"""

import os
import re
import shutil
from pathlib import Path

BASE = Path("/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web/src")
FEATURES = BASE / "features"
ENTITIES = BASE / "entities"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_file(path: Path, content: str):
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")

def extract_get_methods(content: str) -> tuple[str, str]:
    """Extract GET methods from an API service object. Returns (get_methods, remaining_content)."""
    # Match methods that use api.get<...>
    pattern = re.compile(
        r"^\s+\w+\([^)]*\)\s*\{\s*\n\s*return\s+api\.get<.*?\n\s*\},?\n",
        re.MULTILINE,
    )
    gets = pattern.findall(content)
    remaining = pattern.sub("", content)
    return "\n".join(gets), remaining

def extract_interfaces(content: str) -> str:
    """Extract all interface/type declarations from a file."""
    # This is a simplistic extraction — we'll manually verify
    lines = content.splitlines()
    result = []
    in_interface = False
    brace_depth = 0
    for line in lines:
        if re.match(r"^export\s+(interface|type)\s+", line):
            in_interface = True
        if in_interface:
            result.append(line)
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0 and "{" in result[-1]:
                in_interface = False
                brace_depth = 0
    return "\n".join(result)

# ========================================================================
# Entity 1: user (from auth.api + profile.api)
# ========================================================================
print("=== Creating entities/user ===")
ensure_dir(ENTITIES / "user" / "model")
ensure_dir(ENTITIES / "user" / "api")

# Types: combine auth types + profile types (just the domain types, not UI props)
auth_types = read_file(FEATURES / "auth" / "model" / "auth.types.ts")
profile_types = read_file(FEATURES / "user" / "profile" / "model" / "profile.types.ts")

# For auth.types.ts — these are mostly UI prop types. We keep LoginResponse, RegisterResponse,
# LoginHistoryEntry as domain types.
# For profile.types.ts — we keep ProfileResponse, StudentProfileData, etc.

user_types = """// Auto-generated from features/auth/api/auth.api.ts + features/user/profile

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  school_id: string;
  role: string;
  requires_2fa?: boolean;
  temp_token?: string;
  message?: string;
}

export interface RegisterResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  school_id: string;
  role: string;
  email_verification_required: boolean;
}

export interface LoginHistoryEntry {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  location: string | null;
  status: 'success' | 'failed';
  created_at: string;
}

export type ProfileFieldValue = string | number | boolean | null | undefined;

export interface StudentProfileData {
  student_number?: string | null;
  date_of_birth?: string | null;
  class_level?: string | null;
  nationality?: string | null;
  [key: string]: ProfileFieldValue;
}

export interface ParentProfileData {
  relationship_type?: string | null;
  cin_number?: string | null;
  address?: string | null;
  profession?: string | null;
  emergency_phone?: string | null;
  [key: string]: ProfileFieldValue;
}

export interface TeacherProfileData {
  employee_id?: string | null;
  subject_specialty?: string | null;
  qualification?: string | null;
  reward_points?: number | null;
  [key: string]: ProfileFieldValue;
}

export interface ProfileResponse {
  user_id?: string;
  email?: string;
  full_name?: string;
  phone?: string | null;
  role?: string;
  school_id?: string;
  student_profile?: StudentProfileData | null;
  parent_profile?: ParentProfileData | null;
  teacher_profile?: TeacherProfileData | null;
}

export interface AdminUserProfileResponse extends ProfileResponse {
  user_id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: string;
  school_id: string;
}

export interface ChildEntry {
  user_id: string;
  full_name: string;
  email: string;
  link_id: string;
  linked_at: string | null;
  student_profile: {
    class_level: string | null;
    date_of_birth: string | null;
    student_number: string | null;
    nationality: string | null;
  } | null;
}

export interface SessionItem {
  id: string;
  source: string;
  user_agent: string | null;
  ip_address: string | null;
  device_name: string | null;
  created_at: string;
  last_active: string | null;
  is_current: boolean;
}
"""
write_file(ENTITIES / "user" / "model" / "types.ts", user_types)

# Read-only API for user entity
user_api = """import { api } from '@/core/api/client';
import type {
  LoginResponse,
  RegisterResponse,
  LoginHistoryEntry,
  ProfileResponse,
  AdminUserProfileResponse,
  ChildEntry,
  SessionItem,
} from '../model/types';

export interface RegisterPayload {
  code: string;
  email: string;
  full_name: string;
  phone: string | null;
  password: string;
  profile_data: Record<string, string>;
}

export interface VerifyEmailPayload {
  user_id: string;
  school_id: string;
  otp: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  school_id: string;
}

export interface Verify2faPayload {
  code: string;
  user_id?: string;
}

export const userApi = {
  /** GET /auth/me */
  getMe() {
    return api.get<{
      user_id: string;
      email: string;
      full_name: string;
      role: string;
      school_id: string;
    }>('/auth/me');
  },

  /** GET /auth/login-history */
  getLoginHistory() {
    return api.get<LoginHistoryEntry[]>('/auth/login-history');
  },

  /** GET /me/profile */
  getProfile() {
    return api.get<ProfileResponse>('/me/profile');
  },

  /** GET /me/children */
  listChildren() {
    return api.get<ChildEntry[]>('/me/children');
  },

  /** GET /auth/sessions */
  listSessions() {
    return api.get<SessionItem[]>('/auth/sessions');
  },

  /** GET /admin/users/:id/profile */
  getAdminUserProfile(userId: string) {
    return api.get<AdminUserProfileResponse>(`/admin/users/${userId}/profile`);
  },
};
"""
write_file(ENTITIES / "user" / "api" / "user.api.ts", user_api)

# Barrels
write_file(ENTITIES / "user" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "user" / "api" / "index.ts", "export * from './user.api';\n")
write_file(ENTITIES / "user" / "index.ts", "export * from './model';\nexport * from './api';\n")

print("  entities/user created.")

# ========================================================================
# Entity 2: school (from schools.api.ts + micro-schools.api.ts types)
# ========================================================================
print("=== Creating entities/school ===")
ensure_dir(ENTITIES / "school" / "model")
ensure_dir(ENTITIES / "school" / "api")

# Read the schools API to understand types
schools_api = read_file(FEATURES / "school" / "settings" / "api" / "schools.api.ts")
# Extract inline response types
type_blocks = []
for m in re.finditer(r"api\.(get|post|put|patch|delete)<(.*?)>", schools_api):
    type_blocks.append(m.group(2))

# Let's read micro-schools API too
micro_api = read_file(FEATURES / "school" / "micro-schools" / "api" / "micro-schools.api.ts")

# For school entity, we'll copy the schools.api as-is since it has both reads and writes,
# but focus on creating the types file. Actually, let's just create the API with reads.
# schools.api.ts has GET=1 MUT=2 — mostly mutations. Not a great candidate.
# micro-schools.api.ts has GET=7 MUT=12 — also mixed.
# Let's create the entity types but keep APIs in features for now.

# Search for school-related types in the codebase
school_types = """export interface SchoolSettings {
  id: string;
  name: string;
  branding?: {
    primary_color?: string;
    logo_url?: string | null;
  };
  features?: Record<string, boolean>;
}
"""
write_file(ENTITIES / "school" / "model" / "types.ts", school_types)
write_file(ENTITIES / "school" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "school" / "api" / "index.ts", "// Placeholder — school read APIs kept in features/school for now\n")
write_file(ENTITIES / "school" / "index.ts", "export * from './model';\n")
print("  entities/school created (types only, APIs mixed).")

# ========================================================================
# Entity 3: content (from content catalog API — mostly reads)
# ========================================================================
print("=== Creating entities/content ===")
ensure_dir(ENTITIES / "content" / "model")
ensure_dir(ENTITIES / "content" / "api")

content_api = read_file(FEATURES / "content" / "catalog" / "api" / "content.api.ts")
# content.api.ts has GET=1 MUT=5 — mostly mutations, skip for now

# Let's use documents.api.ts which has GET=11 MUT=8 — more reads
# Actually documents has many reads, let's create entities/documents instead

print("  entities/content skipped (mixed reads/writes).")

# ========================================================================
# Entity 4: document (from documents.api.ts)
# ========================================================================
print("=== Creating entities/document ===")
ensure_dir(ENTITIES / "document" / "model")
ensure_dir(ENTITIES / "document" / "api")

doc_types = read_file(FEATURES / "content" / "documents" / "model" / "documents.types.ts")
write_file(ENTITIES / "document" / "model" / "types.ts", doc_types)

# Extract GET methods from documents.api.ts
doc_api_content = read_file(FEATURES / "content" / "documents" / "api" / "documents.api.ts")
# We keep the full file for now but create an index
write_file(ENTITIES / "document" / "api" / "index.ts", "// documents API kept in features/content/documents/api for now\n")
write_file(ENTITIES / "document" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "document" / "index.ts", "export * from './model';\n")
print("  entities/document created.")

# ========================================================================
# Entity 5: sync (from sync.api.ts)
# ========================================================================
print("=== Creating entities/sync ===")
ensure_dir(ENTITIES / "sync" / "model")
ensure_dir(ENTITIES / "sync" / "api")

sync_types = read_file(FEATURES / "sync" / "model" / "sync.types.ts")
write_file(ENTITIES / "sync" / "model" / "types.ts", sync_types)
write_file(ENTITIES / "sync" / "model" / "index.ts", "export * from './types';\n")

# sync.api.ts has GET=2 MUT=5, mixed. We'll create a read-only version.
sync_api = read_file(FEATURES / "sync" / "api" / "sync.api.ts")
write_file(ENTITIES / "sync" / "api" / "sync.api.ts", sync_api)  # Full copy for now
write_file(ENTITIES / "sync" / "api" / "index.ts", "export * from './sync.api';\n")
write_file(ENTITIES / "sync" / "index.ts", "export * from './model';\nexport * from './api';\n")
print("  entities/sync created.")

# ========================================================================
# Entity 6: academic/gradebook
# ========================================================================
print("=== Creating entities/academic/gradebook ===")
ensure_dir(ENTITIES / "academic" / "gradebook" / "model")
ensure_dir(ENTITIES / "academic" / "gradebook" / "api")

gb_types = read_file(FEATURES / "academic" / "gradebook" / "model" / "gradebook.types.ts")
write_file(ENTITIES / "academic" / "gradebook" / "model" / "types.ts", gb_types)
write_file(ENTITIES / "academic" / "gradebook" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "academic" / "gradebook" / "api" / "index.ts", "// gradebook API kept in features for now\n")
write_file(ENTITIES / "academic" / "gradebook" / "index.ts", "export * from './model';\n")
print("  entities/academic/gradebook created.")

# ========================================================================
# Entity 7: academic/attendance
# ========================================================================
print("=== Creating entities/academic/attendance ===")
ensure_dir(ENTITIES / "academic" / "attendance" / "model")
ensure_dir(ENTITIES / "academic" / "attendance" / "api")

att_types = read_file(FEATURES / "academic" / "attendance" / "model" / "attendance.types.ts")
write_file(ENTITIES / "academic" / "attendance" / "model" / "types.ts", att_types)
write_file(ENTITIES / "academic" / "attendance" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "academic" / "attendance" / "api" / "index.ts", "// attendance API kept in features for now\n")
write_file(ENTITIES / "academic" / "attendance" / "index.ts", "export * from './model';\n")
print("  entities/academic/attendance created.")

# ========================================================================
# Entity 8: academic/skills
# ========================================================================
print("=== Creating entities/academic/skills ===")
ensure_dir(ENTITIES / "academic" / "skills" / "model")
ensure_dir(ENTITIES / "academic" / "skills" / "api")

skills_types = read_file(FEATURES / "academic" / "skills" / "model" / "skills.types.ts")
write_file(ENTITIES / "academic" / "skills" / "model" / "types.ts", skills_types)
write_file(ENTITIES / "academic" / "skills" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "academic" / "skills" / "api" / "index.ts", "// skills API kept in features for now\n")
write_file(ENTITIES / "academic" / "skills" / "index.ts", "export * from './model';\n")
print("  entities/academic/skills created.")

# ========================================================================
# Entity 9: academic/timetable
# ========================================================================
print("=== Creating entities/academic/timetable ===")
ensure_dir(ENTITIES / "academic" / "timetable" / "model")
ensure_dir(ENTITIES / "academic" / "timetable" / "api")

tt_types = read_file(FEATURES / "academic" / "timetable" / "model" / "timetable.types.ts")
write_file(ENTITIES / "academic" / "timetable" / "model" / "types.ts", tt_types)
write_file(ENTITIES / "academic" / "timetable" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "academic" / "timetable" / "api" / "index.ts", "// timetable API kept in features for now\n")
write_file(ENTITIES / "academic" / "timetable" / "index.ts", "export * from './model';\n")
print("  entities/academic/timetable created.")

# ========================================================================
# Entity 10: communication/calendar
# ========================================================================
print("=== Creating entities/communication/calendar ===")
ensure_dir(ENTITIES / "communication" / "calendar" / "model")
ensure_dir(ENTITIES / "communication" / "calendar" / "api")

cal_types = read_file(FEATURES / "communication" / "calendar" / "model" / "calendar.types.ts")
write_file(ENTITIES / "communication" / "calendar" / "model" / "types.ts", cal_types)
write_file(ENTITIES / "communication" / "calendar" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "communication" / "calendar" / "api" / "index.ts", "// calendar API kept in features for now\n")
write_file(ENTITIES / "communication" / "calendar" / "index.ts", "export * from './model';\n")
print("  entities/communication/calendar created.")

# ========================================================================
# Entity 11: billing/budget
# ========================================================================
print("=== Creating entities/billing/budget ===")
ensure_dir(ENTITIES / "billing" / "budget" / "model")
ensure_dir(ENTITIES / "billing" / "budget" / "api")

budget_types = read_file(FEATURES / "billing" / "budgets" / "model" / "budgets.types.ts")
write_file(ENTITIES / "billing" / "budget" / "model" / "types.ts", budget_types)
write_file(ENTITIES / "billing" / "budget" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "billing" / "budget" / "api" / "index.ts", "// budget API kept in features for now\n")
write_file(ENTITIES / "billing" / "budget" / "index.ts", "export * from './model';\n")
print("  entities/billing/budget created.")

# ========================================================================
# Entity 12: reports/financial-health
# ========================================================================
print("=== Creating entities/reports/financial-health ===")
ensure_dir(ENTITIES / "reports" / "financial-health" / "model")
ensure_dir(ENTITIES / "reports" / "financial-health" / "api")

fh_types = read_file(FEATURES / "reports" / "financial-health" / "model" / "financial-health.types.ts")
write_file(ENTITIES / "reports" / "financial-health" / "model" / "types.ts", fh_types)
write_file(ENTITIES / "reports" / "financial-health" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "reports" / "financial-health" / "api" / "index.ts", "// financial-health API kept in features for now\n")
write_file(ENTITIES / "reports" / "financial-health" / "index.ts", "export * from './model';\n")
print("  entities/reports/financial-health created.")

# ========================================================================
# Entity 13: school/micro-school
# ========================================================================
print("=== Creating entities/school/micro-school ===")
ensure_dir(ENTITIES / "school" / "micro-school" / "model")
ensure_dir(ENTITIES / "school" / "micro-school" / "api")

ms_types = read_file(FEATURES / "school" / "micro-schools" / "model" / "micro-schools.types.ts")
write_file(ENTITIES / "school" / "micro-school" / "model" / "types.ts", ms_types)
write_file(ENTITIES / "school" / "micro-school" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "school" / "micro-school" / "api" / "index.ts", "// micro-school API kept in features for now\n")
write_file(ENTITIES / "school" / "micro-school" / "index.ts", "export * from './model';\n")
print("  entities/school/micro-school created.")

# ========================================================================
# Entity 14: content/teacher-library
# ========================================================================
print("=== Creating entities/content/teacher-library ===")
ensure_dir(ENTITIES / "content" / "teacher-library" / "model")
ensure_dir(ENTITIES / "content" / "teacher-library" / "api")

tl_types = read_file(FEATURES / "content" / "teacher-library" / "model" / "content-library.types.ts")
write_file(ENTITIES / "content" / "teacher-library" / "model" / "types.ts", tl_types)
write_file(ENTITIES / "content" / "teacher-library" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "content" / "teacher-library" / "api" / "index.ts", "// teacher-library API kept in features for now\n")
write_file(ENTITIES / "content" / "teacher-library" / "index.ts", "export * from './model';\n")
print("  entities/content/teacher-library created.")

# ========================================================================
# Entity 15: content/cms (quiz builder + content upload types)
# ========================================================================
print("=== Creating entities/content/cms ===")
ensure_dir(ENTITIES / "content" / "cms" / "model")
ensure_dir(ENTITIES / "content" / "cms" / "api")

qb_types = read_file(FEATURES / "content" / "cms" / "model" / "quiz-builder.types.ts")
cu_types = read_file(FEATURES / "content" / "cms" / "model" / "content-upload.types.ts")
write_file(ENTITIES / "content" / "cms" / "model" / "types.ts", qb_types + "\n" + cu_types)
write_file(ENTITIES / "content" / "cms" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "content" / "cms" / "api" / "index.ts", "// cms API kept in features for now\n")
write_file(ENTITIES / "content" / "cms" / "index.ts", "export * from './model';\n")
print("  entities/content/cms created.")

# ========================================================================
# Entity 16: admin/compliance
# ========================================================================
print("=== Creating entities/admin/compliance ===")
ensure_dir(ENTITIES / "admin" / "compliance" / "model")
ensure_dir(ENTITIES / "admin" / "compliance" / "api")

comp_types = read_file(FEATURES / "admin" / "compliance" / "model" / "compliance.types.ts")
write_file(ENTITIES / "admin" / "compliance" / "model" / "types.ts", comp_types)
write_file(ENTITIES / "admin" / "compliance" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "admin" / "compliance" / "api" / "index.ts", "// compliance API kept in features for now\n")
write_file(ENTITIES / "admin" / "compliance" / "index.ts", "export * from './model';\n")
print("  entities/admin/compliance created.")

# ========================================================================
# Entity 17: lms/rubric
# ========================================================================
print("=== Creating entities/lms/rubric ===")
ensure_dir(ENTITIES / "lms" / "rubric" / "model")
ensure_dir(ENTITIES / "lms" / "rubric" / "api")

rub_types = read_file(FEATURES / "lms" / "rubrics" / "model" / "rubrics.types.ts")
write_file(ENTITIES / "lms" / "rubric" / "model" / "types.ts", rub_types)
write_file(ENTITIES / "lms" / "rubric" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "lms" / "rubric" / "api" / "index.ts", "// rubric API kept in features for now\n")
write_file(ENTITIES / "lms" / "rubric" / "index.ts", "export * from './model';\n")
print("  entities/lms/rubric created.")

# ========================================================================
# Entity 18: lms/question-bank
# ========================================================================
print("=== Creating entities/lms/question-bank ===")
ensure_dir(ENTITIES / "lms" / "question-bank" / "model")
ensure_dir(ENTITIES / "lms" / "question-bank" / "api")

qb_types = read_file(FEATURES / "lms" / "question-bank" / "model" / "question-bank.types.ts")
write_file(ENTITIES / "lms" / "question-bank" / "model" / "types.ts", qb_types)
write_file(ENTITIES / "lms" / "question-bank" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "lms" / "question-bank" / "api" / "index.ts", "// question-bank API kept in features for now\n")
write_file(ENTITIES / "lms" / "question-bank" / "index.ts", "export * from './model';\n")
print("  entities/lms/question-bank created.")

# ========================================================================
# Entity 19: lms/teacher-quiz
# ========================================================================
print("=== Creating entities/lms/teacher-quiz ===")
ensure_dir(ENTITIES / "lms" / "teacher-quiz" / "model")
ensure_dir(ENTITIES / "lms" / "teacher-quiz" / "api")

tq_types = read_file(FEATURES / "lms" / "teacher" / "model" / "teacher-quiz.types.ts")
write_file(ENTITIES / "lms" / "teacher-quiz" / "model" / "types.ts", tq_types)
write_file(ENTITIES / "lms" / "teacher-quiz" / "model" / "index.ts", "export * from './types';\n")
write_file(ENTITIES / "lms" / "teacher-quiz" / "api" / "index.ts", "// teacher-quiz API kept in features for now\n")
write_file(ENTITIES / "lms" / "teacher-quiz" / "index.ts", "export * from './model';\n")
print("  entities/lms/teacher-quiz created.")

print("\n=== All entities created ===")
print(f"Entities root: {ENTITIES}")
print("Next: update feature imports to use entity types where possible.")
