import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/format";
import { NovaComandaModal } from "./NovaComandaModal";
import { useComandas, useComandasFechadas } from "./useComandas";

const fmtData = (iso: string | null | undefined) => {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export function ComandasPage() {
  const navigate = useNavigate();
  const [busca, setBusca] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [showHistorico, setShowHistorico] = useState(false);
  const [buscaFechadas, setBuscaFechadas] = useState("");

  const { data: comandas = [], isLoading } = useComandas(busca || undefined);
  const { data: fechadas = [], isLoading: loadingFechadas } = useComandasFechadas(
    showHistorico ? buscaFechadas || undefined : undefined
  );

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
                    <div className="flex items-center gap-2 font-medium">
                      {c.tipo_identificacao === "mesa" ? "Mesa" : ""} {c.identificacao}
                      {c.status === "reaberta" && (
                        <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs text-yellow-700">
                          reaberta
                        </span>
                      )}
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

      {/* Histórico */}
      <div className="mt-8">
        <button
          onClick={() => setShowHistorico((v) => !v)}
          className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          <span>{showHistorico ? "▲" : "▼"}</span>
          Histórico (Fechadas)
        </button>

        {showHistorico && (
          <div className="mt-3">
            <Input
              placeholder="Buscar no histórico..."
              value={buscaFechadas}
              onChange={(e) => setBuscaFechadas(e.target.value)}
              className="mb-3 max-w-sm"
            />
            {loadingFechadas ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded bg-gray-100" />
                ))}
              </div>
            ) : fechadas.length === 0 ? (
              <p className="text-sm text-gray-500">Nenhuma comanda fechada.</p>
            ) : (
              <div className="space-y-2">
                {fechadas.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => navigate(`/comandas/${c.id}`)}
                    className="w-full rounded border border-gray-200 p-3 text-left transition-colors hover:bg-gray-50"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium text-gray-700">
                          #{c.id} — {c.tipo_identificacao === "mesa" ? "Mesa" : ""} {c.identificacao}
                        </div>
                        <div className="text-xs text-gray-500">
                          Garçom: {c.garcom_nome} · Fechada em: {fmtData(c.data_fechamento)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-gray-700">
                          {c.total != null ? formatCurrency(Number(c.total)) : "—"}
                        </div>
                        <div className="text-xs text-gray-400">total</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {showModal && <NovaComandaModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
