export const IMPERSONATION_SESSION_KEY = "impersonation_token";

/**
 * Starts a support session without putting its bearer credential in a URL.
 * `about:blank` inherits this application's origin, so sessionStorage can be
 * populated before the first application request is made.
 */
export function openImpersonationSession(token: string): boolean {
  const supportWindow = window.open("about:blank", "_blank");
  if (!supportWindow) return false;

  supportWindow.sessionStorage.setItem(IMPERSONATION_SESSION_KEY, token);
  supportWindow.opener = null;
  supportWindow.location.replace("/");
  return true;
}

export function hasImpersonationSession(): boolean {
  return Boolean(sessionStorage.getItem(IMPERSONATION_SESSION_KEY));
}
