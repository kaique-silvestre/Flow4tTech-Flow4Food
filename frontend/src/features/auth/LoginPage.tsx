import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginSchema, type LoginFormValues } from "./authSchemas";
import { useLogin } from "./useLogin";

export function LoginPage() {
  const { mutate, isPending } = useLogin();

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
        <h1 className="mb-6 text-center text-2xl font-bold tracking-tight">Flow4Tech</h1>
        <form onSubmit={handleSubmit((data) => mutate(data))} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="identifier">Email ou usuário</Label>
            <Input
              id="identifier"
              type="text"
              placeholder="Digite seu email ou usuário"
              autoComplete="username"
              {...register("identifier")}
            />
            {errors.identifier && (
              <p className="text-sm text-red-500">{errors.identifier.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="password">Senha</Label>
            <Input
              id="password"
              type="password"
              placeholder="Digite sua senha"
              autoComplete="current-password"
              {...register("password")}
            />
            {errors.password && (
              <p className="text-sm text-red-500">{errors.password.message}</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? "Entrando..." : "ENTRAR"}
          </Button>
        </form>
      </div>
    </div>
  );
}
