import { useAuthStore } from "@/stores/authStore";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";

export function AssinaturaVencidaPage() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  useEffect(() => {
    if (user && user.profile_name !== "Admin") {
      navigate("/conta-suspensa", { replace: true });
    }
  }, [user, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-white p-8 shadow-sm text-center space-y-4">
        <div className="text-4xl">⚠️</div>
        <h1 className="text-2xl font-bold text-gray-900">Assinatura Vencida</h1>
        <p className="text-gray-600">
          O acesso ao Flow4Food está suspenso porque a assinatura do seu estabelecimento está vencida ou inativa.
        </p>
        <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-left text-sm text-amber-800 space-y-1">
          <p className="font-medium">Para regularizar:</p>
          <p>Entre em contato com a Flow4Tech para renovar sua assinatura.</p>
          <p className="mt-2 font-medium">Contato:</p>
          <p>contato@flow4tech.com.br</p>
        </div>
        <p className="text-xs text-gray-400">
          Após a regularização, faça login novamente para restaurar o acesso.
        </p>
      </div>
    </div>
  );
}
