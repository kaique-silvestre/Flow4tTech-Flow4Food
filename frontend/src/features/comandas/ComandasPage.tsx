import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/format";
import { NovaComandaModal } from "./NovaComandaModal";
import { useComandas } from "./useComandas";

export function ComandasPage() {
  const navigate = useNavigate();
  const [busca, setBusca] = useState("");
  const [showModal, setShowModal] = useState(false);
  const { data: comandas = [], isLoading } = useComandas(busca || undefined);

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Comandas Abertas</h1>
        <Button onClick={() => setShowModal(true)}>+ Nova Comanda</Button>
      </div>

      <div className="mb-4">
        <Input
          placeholder="Buscar por nome ou mesa..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : comandas.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma comanda aberta.</p>
      ) : (
        <div className="space-y-2">
          {comandas.map((c) => {
            const ativos = c.itens_ativos.filter((i) => !i.cancelado);
            return (
              <button
                key={c.id}
                onClick={() => navigate(`/comandas/${c.id}`)}
                className="w-full rounded border p-4 text-left transition-colors hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">
                      {c.tipo_identificacao === "mesa" ? "Mesa" : ""} {c.identificacao}
                    </div>
                    <div className="text-sm text-gray-500">
                      Garçom: {c.garcom_nome} · {ativos.length}{" "}
                      {ativos.length === 1 ? "item" : "itens"} · {c.tempo_aberta_minutos} min
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{formatCurrency(Number(c.total_parcial))}</div>
                    <div className="text-xs text-gray-400">parcial</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {showModal && <NovaComandaModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
