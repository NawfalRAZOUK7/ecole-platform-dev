/** All role codes in the system. */
export const ROLE_CODES = ['ADM', 'DIR', 'TCH', 'PAR', 'STD'] as const;

/** Type for valid role codes. */
export type RoleCode = (typeof ROLE_CODES)[number];

/** Admin-only roles. */
export const ADMIN_ROLES: RoleCode[] = ['ADM'];

/** Management roles (admin + director). */
export const MANAGEMENT_ROLES: RoleCode[] = ['ADM', 'DIR'];

/** Staff roles (admin + director + teacher). */
export const STAFF_ROLES: RoleCode[] = ['ADM', 'DIR', 'TCH'];

/** All user roles. */
export const ALL_ROLES: RoleCode[] = ['ADM', 'DIR', 'TCH', 'PAR', 'STD'];
