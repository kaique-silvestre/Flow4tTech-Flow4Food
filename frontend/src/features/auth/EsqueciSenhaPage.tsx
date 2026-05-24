import { useState } from "react";
import { Link } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import { forgotPasswordSchema, type ForgotPasswordValues } from "./authSchemas";

export function EsqueciSenhaPage() {
  const [sent, setSent] = useState(false);

  const { mutate, isPending } = useMutation({
    mutationFn: (data: ForgotPasswordValues) =>
      api.post("/api/auth/forgot-password", { email: data.email }),
    onSuccess: () => setSent(true),
    onError: () => toast.error("Erro ao processar solicitação. Tente novamente."),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-lg border bg-white p-8 shadow-sm">
        <h1 className="mb-2 text-center text-2xl font-bold tracking-tight">Flow4Tech</h1>
        <p className="mb-6 text-center text-sm text-gray-500">Redefinição de senha</p>

        {sent ? (
          <div className="space-y-4 text-center">
            <p className="text-sm text-gray-700">
              Se o email estiver cadastrado, você receberá um link de redefinição em instantes.
            </p>
            <Link to="/login" className="block text-sm text-blue-600 hover:underline">
              ← Voltar ao login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit((data) => mutate(data))} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                autoComplete="email"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "Enviando..." : "ENVIAR LINK"}
            </Button>
            <div className="text-center">
              <Link to="/login" className="text-sm text-gray-500 hover:underline">
                ← Voltar ao login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
