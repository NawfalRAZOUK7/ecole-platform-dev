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
  /** Contexte plateforme : SUP / gestionnaire de contenu (CMS). Identité visuelle dédiée. */
  isPlatform: boolean;
  schoolType: SchoolType;
  /** Identité visuelle, pilotée par le CONTEXTE d'école (formel/informel), jamais par le rôle. */
  designMode: DesignMode;
  ageTier: AgeTier;
  /** Accent ludique (gros texte, icônes) pour les jeunes élèves. N'est PAS un thème séparé. */
  ageAccent: boolean;
  themeMode: ThemeMode;
  isRtl: boolean;
  appliedTheme: 'light' | 'dark' | 'kids' | 'kids-dark';
}

/**
 * Règle de design (décision produit) :
 *  - 3 identités par CONTEXTE : Plateforme (SUP/CMS), École formelle, École informelle.
 *  - TOUS les rôles d'une même école partagent l'identité de cette école (y compris l'élève).
 *  - L'âge de l'élève n'ajoute qu'un ACCENT (gros texte, icônes), pas un thème « kids » séparé.
 *  - Mêmes tokens web et mobile : un compte est cohérent d'une plateforme à l'autre.
 */
export function resolveDesignContext(input: DesignContextInput): DesignContext {
  const role = (input.role ?? '').toUpperCase();
  const isPlatform = role === 'SUP' || role === 'CONTENT_MGR' || role === 'CMS';
  const schoolType = normalizeSchoolType(input.schoolType);
  const override = normalizeDesignMode(
    input.designMode ?? readSettingsDesignMode(input.schoolSettings),
  );
  const designMode = isInformalContext(role, input.pathname)
    ? 'informal'
    : (override ?? schoolType);
  const themeMode = input.themeMode === 'dark' ? 'dark' : 'light';
  const ageTier = input.ageTier ?? 'primaire';
  // Accent ludique (gros texte, icônes) réservé aux jeunes enfants :
  //  - tout élève en contexte INFORMEL (rawd : enfants 3-5 ans), ET
  //  - l'élève FORMEL en préscolaire (PS/MS/GS → tier 'maternelle').
  // Le primaire formel et au-delà gardent le look standard (piloté par niveau/matière).
  const ageAccent = role === 'STD' && (designMode === 'informal' || ageTier === 'maternelle');
  // Plus de thème « kids » séparé : l'élève reste sur le thème (clair/sombre) de son école.
  const appliedTheme = themeMode;

  return {
    role,
    isPlatform,
    schoolType,
    designMode,
    ageTier,
    ageAccent,
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
