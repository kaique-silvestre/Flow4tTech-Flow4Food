/** Decodes the payload segment of a JWT without verifying its signature.
 *
 * Auth is enforced server-side; this is purely for reading claims already
 * trusted because they came back from our own login/refresh endpoints
 * (used to populate the client-side user/admin object in the auth stores).
 * Returns null for any malformed token instead of throwing, so callers can
 * treat a bad token the same way as "not logged in".
 */
export function decodeJwtPayload<T>(token: string): T | null {
  try {
    const base64 = token.split(".")[1];
    const json = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json) as T;
  } catch {
    return null;
  }
}
