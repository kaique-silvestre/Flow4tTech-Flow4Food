import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginSchema, type LoginFormValues } from "./authSchemas";
import { useLogin } from "./useLogin";

export function LoginPage() {
  const { mutate, isPending } = useLogin();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-lg border bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-center text-2xl font-bold tracking-tight">Flow4Food</h1>
        <p className="mb-6 text-center text-sm text-gray-500">por Flow4Tech</p>

        <form onSubmit={handleSubmit((data) => mutate(data))} className="space-y-4">
          <p className="text-base font-semibold text-gray-800">Bem-vindo de volta</p>
          <div className="space-y-1">
            <Label htmlFor="identifier">Email ou usuário</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                id="identifier"
                type="text"
                placeholder="Digite seu email ou usuário"
                autoComplete="username"
                className="pl-10"
                {...register("identifier")}
              />
            </div>
            {errors.identifier && (
              <p className="text-sm text-red-500">{errors.identifier.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label htmlFor="password">Senha</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                autoComplete="current-password"
                className="pl-10 pr-10"
                {...register("password")}
              />
              <button
                type="button"
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md text-gray-400 hover:text-gray-600"
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="text-sm text-red-500">{errors.password.message}</p>
            )}
          </div>

          <div className="flex justify-end">
            <Link to="/esqueci-senha" className="text-sm text-gray-500 hover:underline">
              Esqueci minha senha
            </Link>
          </div>

          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? "Entrando..." : "ENTRAR"}
          </Button>
        </form>
      </div>
    </div>
  );
}
