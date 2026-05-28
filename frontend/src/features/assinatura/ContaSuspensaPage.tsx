export function ContaSuspensaPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-sm rounded-lg border bg-white p-8 shadow-sm text-center space-y-4">
        <div className="text-4xl">🔒</div>
        <h1 className="text-2xl font-bold text-gray-900">Conta Suspensa</h1>
        <p className="text-gray-600">
          O acesso ao sistema está temporariamente suspenso.
        </p>
        <p className="text-gray-600">
          Procure o responsável pelo estabelecimento para regularizar a situação.
        </p>
      </div>
    </div>
  );
}
