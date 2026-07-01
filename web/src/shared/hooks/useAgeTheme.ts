/**
 * Age/niveau-based theme hook — adapts the UI for maternelle (3-5), primaire
 * (6-9), college (10-13+).
 *
 * Resolves a tier from the Moroccan school level (`class_level`) when known,
 * otherwise from the date_of_birth, and sets `data-age-tier` on <html> for CSS
 * targeting. Mirrors the mobile `resolveAgeTier`.
 *
 * Usage: call once in Layout when role === STD, or in any student page.
 */

import { useEffect, useMemo } from 'react';

export type AgeTier = 'maternelle' | 'primaire' | 'college';

/**
 * Map a Moroccan `class_level` label to a tier when recognisable.
 * Returns null when the label is unknown (caller falls back to age/DOB).
 */
function niveauToTier(niveau: string): AgeTier | null {
  const n = niveau.toLowerCase();
  if (/maternelle|prescol|\b(ps|ms|gs)\b/.test(n)) return 'maternelle';
  if (/primaire|\b(cp|ce1|ce2|cm1|cm2)\b/.test(n)) return 'primaire';
  if (/college|collège|lycee|lycée|terminale|\b(6e|6eme|6ème|[1-3]\s?ac|tc|bac)\b/.test(n)) {
    return 'college';
  }
  return null;
}

/**
 * Compute the student's age in full years from a date_of_birth string (YYYY-MM-DD).
 */
function computeAge(dateOfBirth: string): number {
  const dob = new Date(dateOfBirth);
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
    age--;
  }
  return age;
}

/**
 * Map age to a tier:
 *   - maternelle: 3-5 (preschool — big visuals, simple nav, mascot)
 *   - primaire: 6-9 (primary — gamified, colorful but structured)
 *   - college: 10+ (middle school — compact, more mature)
 */
function ageToTier(age: number): AgeTier {
  if (age <= 5) return 'maternelle';
  if (age <= 9) return 'primaire';
  return 'college';
}

/**
 * Hook: resolves the tier (niveau first, then date_of_birth, else primaire) and
 * applies `data-age-tier` to <html>. Returns the tier for conditional rendering.
 */
export function useAgeTheme(
  dateOfBirth?: string | null,
  niveau?: string | null,
): AgeTier {
  const tier = useMemo<AgeTier>(() => {
    if (niveau) {
      const byNiveau = niveauToTier(niveau);
      if (byNiveau) return byNiveau;
    }
    if (!dateOfBirth) return 'primaire'; // default fallback
    const age = computeAge(dateOfBirth);
    return ageToTier(age);
  }, [dateOfBirth, niveau]);

  useEffect(() => {
    document.documentElement.setAttribute('data-age-tier', tier);
    return () => {
      document.documentElement.removeAttribute('data-age-tier');
    };
  }, [tier]);

  return tier;
}
