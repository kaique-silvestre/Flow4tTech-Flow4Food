/** Subscription status options shared by every platform-admin screen that
 * displays or edits `status_assinatura` (tenants list, cockpit, tenant
 * detail) — previously copy-pasted in each of those three files. */
export const SUBSCRIPTION_STATUS_OPTIONS = ["trial", "ativa", "suspensa", "cancelada"] as const;

export const SUBSCRIPTION_STATUS_LABELS: Record<string, string> = {
  trial: "Trial",
  ativa: "Ativa",
  suspensa: "Suspensa",
  cancelada: "Cancelada",
};

export const SUBSCRIPTION_STATUS_COLORS: Record<string, string> = {
  trial: "bg-yellow-100 text-yellow-800",
  ativa: "bg-green-100 text-green-800",
  suspensa: "bg-red-100 text-red-800",
  cancelada: "bg-gray-100 text-gray-600",
};
