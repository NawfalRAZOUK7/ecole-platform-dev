/**
 * Age-based theme hook — adapts the UI for maternelle (3-5), primaire (6-9), college (10-13+).
 *
 * Reads `date_of_birth` from the student profile and computes an age tier.
 * Sets `data-age-tier` attribute on <html> for CSS targeting.
 *
 * Usage: call once in Layout when role === STD.
 */

import { useEffect, useMemo } from 'react';
import { useProfileData } from '@/features/profile/useProfile';

export type AgeTier = 'maternelle' | 'primaire' | 'college';

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
 * Hook: reads the student profile, computes age tier, applies `data-age-tier` to <html>.
 * Returns the current tier for conditional rendering in components.
 */
export function useAgeTheme(): AgeTier {
  const profileQuery = useProfileData();

  const tier = useMemo<AgeTier>(() => {
    const dob = profileQuery.data?.student_profile?.date_of_birth;
    if (!dob) return 'primaire'; // default fallback
    const age = computeAge(dob);
    return ageToTier(age);
  }, [profileQuery.data]);

  useEffect(() => {
    document.documentElement.setAttribute('data-age-tier', tier);
    return () => {
      document.documentElement.removeAttribute('data-age-tier');
    };
  }, [tier]);

  return tier;
}
