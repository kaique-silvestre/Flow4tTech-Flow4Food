import type { ApiErrorBody } from "@/lib/api";

interface AxiosLikeError {
  response?: {
    status?: number;
    data?: ApiErrorBody;
  };
}

/**
 * Standard error-handling helpers for TanStack Query `onError` callbacks.
 * The backend always responds with the `ApiErrorBody` envelope
 * (`{ error: { code, message, field } }`) for handled errors — these
 * helpers pull each piece out consistently instead of every hook
 * re-implementing its own inline cast.
 */
export function getApiErrorMessage(err: unknown, fallback: string): string {
  return (err as AxiosLikeError)?.response?.data?.error?.message ?? fallback;
}

export function getApiErrorCode(err: unknown): string | undefined {
  return (err as AxiosLikeError)?.response?.data?.error?.code;
}

export function getApiErrorStatus(err: unknown): number | undefined {
  return (err as AxiosLikeError)?.response?.status;
}
