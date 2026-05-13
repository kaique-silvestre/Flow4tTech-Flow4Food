import { toast as sonner } from "sonner";

type ToastOpts = { description?: string; duration?: number };

export const toast = {
  success: (msg: string, opts?: ToastOpts) => sonner.success(msg, { duration: 2500, ...opts }),
  error: (msg: string, opts?: ToastOpts) => sonner.error(msg, { duration: 8000, ...opts }),
  warning: (msg: string, opts?: ToastOpts) => sonner.warning(msg, { duration: 4500, ...opts }),
};
