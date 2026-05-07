import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import type { LoginFormValues } from "./authSchemas";

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export function useLogin() {
  const setToken = useAuthStore((s) => s.setToken);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: LoginFormValues) =>
      api.post<TokenResponse>("/api/auth/login", data).then((r) => r.data),
    onSuccess: (data) => {
      setToken(data.access_token);
      navigate("/", { replace: true });
    },
    onError: () => {
      toast.error("Senha incorreta. Verifique e tente novamente.", {
        duration: Infinity,
      });
    },
  });
}
