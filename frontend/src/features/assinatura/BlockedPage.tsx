import { useSearchParams } from "react-router-dom";

export function BlockedPage() {
  const [params] = useSearchParams();
  const status = params.get("status") ?? "suspensa";
  const contact = params.get("contact") ?? "contato@flow4tech.com.br";

  const statusLabel: Record<string, string> = {
    suspensa: "Suspensa",
    cancelada: "Cancelada",
    trial: "Trial expirado",
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-white p-8 shadow-sm text-center space-y-4">
        <div className="text-4xl">🔒</div>
        <h1 className="text-2xl font-bold text-gray-900">Acesso Bloqueado</h1>
        <p className="text-gray-600">
          O acesso ao Flow4Food está suspenso. Status da assinatura:{" "}
          <span className="font-semibold">{statusLabel[status] ?? status}</span>.
        </p>
        {contact && (
          <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-left text-sm text-amber-800 space-y-1">
            <p className="font-medium">Para regularizar, entre em contato:</p>
            <p>
              <a href={`mailto:${contact}`} className="underline">
                {contact}
              </a>
            </p>
          </div>
        )}
        <p className="text-xs text-gray-400">
          Após a regularização, faça login novamente para restaurar o acesso.
        </p>
      </div>
    </div>
  );
}
