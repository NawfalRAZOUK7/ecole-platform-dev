export type SchoolType = 'formal' | 'informal';
export type DesignMode = 'formal' | 'informal';
export type AgeTier = 'maternelle' | 'primaire' | 'college';
export type ThemeMode = 'light' | 'dark';

export interface DesignContextInput {
  role?: string | null;
  pathname?: string | null;
  schoolType?: string | null;
  designMode?: string | null;
  schoolSettings?: Record<string, unknown> | null;
  ageTier?: AgeTier | null;
  themeMode?: ThemeMode | null;
  isRtl?: boolean;
}

export interface DesignContext {
  role: string;
  schoolType: SchoolType;
  designMode: DesignMode;
  ageTier: AgeTier;
  themeMode: ThemeMode;
  isRtl: boolean;
  appliedTheme: 'light' | 'dark' | 'kids' | 'kids-dark';
}

export function resolveDesignContext(input: DesignContextInput): DesignContext {
  const role = (input.role ?? '').toUpperCase();
  const schoolType = normalizeSchoolType(input.schoolType);
  const override = normalizeDesignMode(
    input.designMode ?? readSettingsDesignMode(input.schoolSettings),
  );
  const designMode = isInformalContext(role, input.pathname)
    ? 'informal'
    : override ?? schoolType;
  const themeMode = input.themeMode === 'dark' ? 'dark' : 'light';
  const ageTier = input.ageTier ?? 'primaire';
  const appliedTheme =
    role === 'STD' ? (themeMode === 'dark' ? 'kids-dark' : 'kids') : themeMode;

  return {
    role,
    schoolType,
    designMode,
    ageTier,
    themeMode,
    isRtl: Boolean(input.isRtl),
    appliedTheme,
  };
}

export function readSettingsDesignMode(
  settings?: Record<string, unknown> | null,
): DesignMode | null {
  const value = settings?.design_mode;
  return normalizeDesignMode(typeof value === 'string' ? value : null);
}

function normalizeSchoolType(value?: string | null): SchoolType {
  return value === 'informal' ? 'informal' : 'formal';
}

function normalizeDesignMode(value?: string | null): DesignMode | null {
  if (value === 'formal' || value === 'informal') return value;
  return null;
}

function isInformalContext(role: string, pathname?: string | null): boolean {
  if (role === 'EDUCATOR') return true;
  return Boolean(pathname?.startsWith('/micro-schools') || pathname?.startsWith('/micro/'));
}
