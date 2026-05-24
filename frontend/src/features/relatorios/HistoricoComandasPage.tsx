import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDebounce } from "use-debounce";
import { formatCurrency, formatDate } from "@/lib/format";
import { useGarcons } from "@/features/cadastros/garcons/useGarcons";
import { useHistoricoComandas } from "./useRelatorios";

function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function HistoricoComandasPage() {
  const navigate = useNavigate();
  const hoje = new Date();
  const seteDiasAtras = new Date(hoje);
  seteDiasAtras.setDate(hoje.getDate() - 7);

  const [dataInicio, setDataInicio] = useState(toIsoDate(seteDiasAtras));
  const [dataFim, setDataFim] = useState(toIsoDate(hoje));
  const [garcomId, setGarcomId] = useState<number | null>(null);
  const [busca, setBusca] = useState("");
  const [debouncedBusca] = useDebounce(busca, 350);

  const { data: garconsData } = useGarcons();
  const garcons = garconsData?.itens ?? [];
  const { data, isLoading } = useHistoricoComandas({
    data_inicio: dataInicio,
    data_fim: dataFim,
    garcom_id: garcomId,
    busca: busca === "" ? "" : debouncedBusca,
  });

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/relatorios")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        ← Relatórios
      </button>
      <h1 className="mb-4 text-xl font-semibold">Histórico de Comandas</h1>

      {/* Filtros */}
      <div className="mb-4 flex flex-wrap gap-3 text-sm">
        <div className="flex items-center gap-1">
          <label className="text-gray-500">De</label>
          <input
            type="date"
            className="rounded border px-2 py-1"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1">
          <label className="text-gray-500">Até</label>
          <input
            type="date"
            className="rounded border px-2 py-1"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
          />
        </div>
        <select
          className="rounded border px-2 py-1"
          value={garcomId ?? ""}
          onChange={(e) => setGarcomId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">Todos os garçons</option>
          {garcons.map((g) => (
            <option key={g.id} value={g.id}>
              {g.nome}
            </option>
          ))}
        </select>
        <input
          className="rounded border px-2 py-1"
          placeholder="Buscar por identificação..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
      </div>

      {/* Resultados */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !data || data.comandas.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma comanda encontrada.</p>
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-1">ID</th>
                <th className="pb-1">Identificação</th>
                <th className="pb-1">Garçom</th>
                <th className="pb-1 text-right">Total</th>
                <th className="pb-1 text-right">Desconto</th>
                <th className="pb-1 text-right">Cortesias</th>
                <th className="pb-1 text-right">Fechamento</th>
              </tr>
            </thead>
            <tbody>
              {data.comandas.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => navigate(`/comandas/${c.id}`)}
                  className="border-b hover:bg-gray-50 cursor-pointer"
                >
                  <td className="py-2 text-gray-400">#{c.id}</td>
                  <td className="py-2">{c.identificacao}</td>
                  <td className="py-2">{c.garcom_nome}</td>
                  <td className="py-2 text-right">{formatCurrency(c.total)}</td>
                  <td className="py-2 text-right">
                    {c.desconto_valor ? formatCurrency(c.desconto_valor) : "—"}
                  </td>
                  <td className="py-2 text-right">
                    {c.cortesias > 0 ? formatCurrency(c.cortesias) : "—"}
                  </td>
                  <td className="py-2 text-right">{formatDate(c.data_fechamento)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-gray-400">{data.total} comanda(s) encontrada(s).</p>
        </>
      )}
    </div>
  );
}
