import * as Sentry from "@sentry/react";

export { Sentry };

export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return;
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  });
  window.addEventListener("unhandledrejection", (e) => {
    Sentry.captureException(e.reason);
  });
}
