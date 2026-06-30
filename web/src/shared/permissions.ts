/**
 * Backend permission strings — single source of truth on the client.
 *
 * Mirrors `app/core/permissions.py`. Use these to gate *edit* affordances so the
 * UI matches what the API will allow (the backend still enforces them; this just
 * avoids showing actions that would 403).
 */
export const PERMISSIONS = {
  /** Authoring (create/update) of mobile game configurations. TCH + EDUCATOR. */
  GAME_CONFIG_MANAGE: 'PERM-AI:game-config:manage',
} as const;

export type PermissionKey = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

/** True only if `permissions` contains `permission`. */
export function hasPermission(
  permissions: readonly string[] | undefined | null,
  permission: string,
): boolean {
  return Boolean(permissions?.includes(permission));
}
