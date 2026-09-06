/** Shared decision logic behind RequireAuth and RequirePlatformAuth.
 *
 * Both guards protect a route tree the same way: no token -> denied; token
 * present but it didn't decode into a usable `user` object (bad/expired
 * token) -> the stale token is cleared and access is denied; otherwise
 * allowed. RequireAuth additionally allows a `hasBypass` session
 * (impersonation, carried outside the normal auth store) to skip both
 * checks.
 */
export interface AuthGuardState {
  token: string | null;
  user: unknown | null;
  clearToken: () => void;
}

export function resolveAuthGuard(state: AuthGuardState, hasBypass = false): boolean {
  if (hasBypass) return true;
  if (!state.token) return false;
  if (!state.user) {
    state.clearToken();
    return false;
  }
  return true;
}
