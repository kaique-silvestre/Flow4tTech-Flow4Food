import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import * as Sentry from "@sentry/react";
import { useAuthStore } from "@/stores/authStore";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 15000,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let _refreshing = false;
let _queue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

function _processQueue(error: unknown, token: string | null) {
  _queue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token!);
  });
  _queue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry) {
      if (_refreshing) {
        return new Promise((resolve, reject) => {
          _queue.push({
            resolve: (token) => {
              original.headers.Authorization = `Bearer ${token}`;
              resolve(api(original));
            },
            reject,
          });
        });
      }

      original._retry = true;
      _refreshing = true;

      try {
        const { data } = await axios.post<{ access_token: string }>(
          `${api.defaults.baseURL}/api/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const newToken = data.access_token;
        useAuthStore.getState().setToken(newToken);
        original.headers.Authorization = `Bearer ${newToken}`;
        _processQueue(null, newToken);
        return api(original);
      } catch (refreshError) {
        _processQueue(refreshError, null);
        useAuthStore.getState().clearToken();
        if (window.location.pathname !== "/login") {
          window.location.assign("/login");
        }
        return Promise.reject(refreshError);
      } finally {
        _refreshing = false;
      }
    }

    if (error.response?.status && error.response.status >= 500) {
      Sentry.captureException(error);
    }
    return Promise.reject(error);
  }
);

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    field: string | null;
  };
}
