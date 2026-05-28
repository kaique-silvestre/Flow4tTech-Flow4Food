import { toast } from "@/lib/toast";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/format";

export function PlaceholderPage() {
  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-xl w-full space-y-6 text-center">
        <h1 className="text-3xl font-bold">Flow4Food</h1>
        <p className="text-slate-600">Foundation pronta. Próximas issues constroem o domínio.</p>
        <p className="text-sm text-slate-500">Exemplo de formatação: {formatCurrency(80.1)}</p>
        <div className="flex gap-3 justify-center">
          <Button onClick={() => toast.success("Toast de sucesso")}>Sucesso</Button>
          <Button variant="destructive" onClick={() => toast.error("Toast de erro")}>
            Erro
          </Button>
          <Button
            variant="outline"
            onClick={() => toast.warning("Toast de aviso")}
          >
            Aviso
          </Button>
        </div>
      </div>
    </main>
  );
}
