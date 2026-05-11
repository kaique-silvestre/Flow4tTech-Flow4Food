import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDebounce } from "use-debounce";
import { LayoutList, LayoutGrid } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/format";
import { NovaComandaModal } from "./NovaComandaModal";
import { useComandas, useComandasFechadas } from "./useComandas";

type ViewMode = "lista" | "cards";

function getInitialViewMode(): ViewMode {
  try {
    const v = localStorage.getItem("comandas_view_mode");
    if (v === "lista" || v === "cards") return v;
  } catch {
    // ignore
  }
  return "lista";
}

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

function todayISODate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function ComandasPage() {
  const navigate = useNavigate();
  const [busca, setBusca] = useState("");
  const [debouncedBusca] = useDebounce(busca, 350);
  const [showModal, setShowModal] = useState(false);
  const [showHistorico, setShowHistorico] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>(getInitialViewMode);

  const today = todayISODate();

  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 60_000);
    return () => clearInterval(id);
  }, []);

  const queryBusca = busca === "" ? undefined : debouncedBusca || undefined;
  const { data: comandas = [], isLoading } = useComandas(queryBusca);
  const { data: fechadasHoje = [], isLoading: loadingFechadas } = useComandasFechadas(
    showHistorico ? { data_inicio: today, data_fim: today } : undefined
  );

  function toggleView(mode: ViewMode) {
    setViewMode(mode);
    try {
      localStorage.setItem("comandas_view_mode", mode);
    } catch {
      // ignore
    }
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Comandas Abertas</h1>
        <div className="flex items-center gap-2">
          <div className="flex rounded border">
            <button
              onClick={() => toggleView("lista")}
              title="Visualização lista"
              className={`flex items-center gap-1 px-2 py-1.5 text-sm transition-colors ${
                viewMode === "lista"
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-500 hover:text-gray-800"
              }`}
            >
              <LayoutList size={16} />
            </button>
            <button
              onClick={() => toggleView("cards")}
              title="Visualização cards"
              className={`flex items-center gap-1 px-2 py-1.5 text-sm transition-colors ${
                viewMode === "cards"
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-500 hover:text-gray-800"
              }`}
            >
              <LayoutGrid size={16} />
            </button>
          </div>
          <Button onClick={() => setShowModal(true)}>+ Nova Comanda</Button>
        </div>
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
        <div className={viewMode === "cards" ? "grid grid-cols-2 gap-3 lg:grid-cols-3" : "space-y-2"}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : comandas.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma comanda aberta.</p>
      ) : viewMode === "lista" ? (
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
                      {ativos.length === 1 ? "item" : "itens"} · {Math.floor((now - new Date(c.created_at).getTime()) / 60_000)} min
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
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
          {comandas.map((c) => {
            const ativos = c.itens_ativos.filter((i) => !i.cancelado);
            return (
              <button
                key={c.id}
                onClick={() => navigate(`/comandas/${c.id}`)}
                className="flex flex-col gap-2 rounded border bg-white p-4 text-left shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-900">
                    {c.tipo_identificacao === "mesa" ? "Mesa " : ""}{c.identificacao}
                  </span>
                  {c.status === "reaberta" && (
                    <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs text-yellow-700">
                      reaberta
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {c.garcom_nome}
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">
                    {ativos.length} {ativos.length === 1 ? "item" : "itens"} · {Math.floor((now - new Date(c.created_at).getTime()) / 60_000)} min
                  </span>
                  <span className="font-medium text-gray-900">
                    {formatCurrency(Number(c.total_parcial))}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Histórico do dia */}
      <div className="mt-8">
        <button
          onClick={() => setShowHistorico((v) => !v)}
          className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          <span>{showHistorico ? "▲" : "▼"}</span>
          Histórico do dia
        </button>

        {showHistorico && (
          <div className="mt-3">
            {loadingFechadas ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded bg-gray-100" />
                ))}
              </div>
            ) : fechadasHoje.length === 0 ? (
              <p className="text-sm text-gray-500">Nenhuma comanda fechada hoje.</p>
            ) : (
              <div className="space-y-2">
                {fechadasHoje.map((c) => (
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

      <NovaComandaModal open={showModal} onClose={() => setShowModal(false)} />
    </div>
  );
}
