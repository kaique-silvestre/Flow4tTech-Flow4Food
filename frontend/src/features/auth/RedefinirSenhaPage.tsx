import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, type ApiErrorBody } from "@/lib/api";
import { toast } from "@/lib/toast";
import { resetPasswordSchema, type ResetPasswordValues } from "./authSchemas";

interface ResetTokenInfo {
  name: string;
}

export function RedefinirSenhaPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const navigate = useNavigate();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["reset-token", token],
    queryFn: () =>
      api.get<ResetTokenInfo>(`/api/auth/reset-password/${token}`).then((r) => r.data),
    enabled: !!token,
    retry: false,
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (values: ResetPasswordValues) =>
      api.post("/api/auth/reset-password", { token, new_password: values.new_password }),
    onSuccess: () => {
      toast.success("Senha redefinida com sucesso");
      navigate("/login", { replace: true });
    },
    onError: (err) => {
      const msg =
        (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message ??
        "Erro ao redefinir senha. Tente novamente.";
      toast.error(msg);
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordValues>({
    resolver: zodResolver(resetPasswordSchema),
  });

  if (!token) {
    return <InvalidLink reason="Token ausente." />;
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <p className="text-sm text-gray-500">Validando link...</p>
      </div>
    );
  }

  if (isError) {
    const msg =
      (error as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message ??
      "Link expirado. Solicite um novo.";
    return <InvalidLink reason={msg} />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-lg border bg-white p-8 shadow-sm">
        <h1 className="mb-2 text-center text-2xl font-bold tracking-tight">Flow4Food</h1>
        <p className="mb-1 text-center text-sm text-gray-500">Redefinir senha</p>
        {data?.name && (
          <p className="mb-6 text-center text-sm font-medium text-gray-700">{data.name}</p>
        )}
        <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="new_password">Nova senha</Label>
            <Input
              id="new_password"
              type="password"
              placeholder="Mínimo 6 caracteres"
              autoComplete="new-password"
              {...register("new_password")}
            />
            {errors.new_password && (
              <p className="text-sm text-red-500">{errors.new_password.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="confirm_password">Confirmar nova senha</Label>
            <Input
              id="confirm_password"
              type="password"
              placeholder="Repita a nova senha"
              autoComplete="new-password"
              {...register("confirm_password")}
            />
            {errors.confirm_password && (
              <p className="text-sm text-red-500">{errors.confirm_password.message}</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? "Salvando..." : "REDEFINIR SENHA"}
          </Button>
        </form>
      </div>
    </div>
  );
}

function InvalidLink({ reason }: { reason: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-lg border bg-white p-8 shadow-sm text-center space-y-4">
        <h1 className="text-2xl font-bold tracking-tight">Flow4Food</h1>
        <p className="text-sm text-red-600">{reason}</p>
        <Link to="/esqueci-senha" className="block text-sm text-blue-600 hover:underline">
          Solicitar novo link →
        </Link>
      </div>
    </div>
  );
}
