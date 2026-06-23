import { useState, useMemo } from "react";
import { usePlatformCockpit, type CockpitMetricsItem } from "./usePlatformApi";

const STATUS_OPTIONS = ["", "trial", "ativa", "suspensa", "cancelada"] as const;

const STATUS_LABELS: Record<string, string> = {
  trial: "Trial",
  ativa: "Ativa",
  suspensa: "Suspensa",
  cancelada: "Cancelada",
};

const STATUS_COLORS: Record<string, string> = {
  trial: "bg-yellow-100 text-yellow-800",
  ativa: "bg-green-100 text-green-800",
  suspensa: "bg-red-100 text-red-800",
  cancelada: "bg-gray-100 text-gray-600",
};

type SortKey = keyof Pick<
  CockpitMetricsItem,
  "dias_cliente" | "comandas_mes" | "faturamento_mes" | "usuarios_ativos_30d" | "compras_mes"
>;

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "dias_cliente", label: "Dias cliente" },
  { key: "comandas_mes", label: "Comandas/mês" },
  { key: "faturamento_mes", label: "Faturamento/mês" },
  { key: "usuarios_ativos_30d", label: "Usuários 30d" },
  { key: "compras_mes", label: "Compras/mês" },
];

function fmtNum(n: number) {
  return n.toLocaleString("pt-BR");
}

function fmtBRL(n: number) {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtDate(s: string | null) {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("pt-BR");
}

function renderCell(key: SortKey, row: CockpitMetricsItem) {
  if (key === "faturamento_mes") return fmtBRL(row[key]);
  return fmtNum(row[key]);
}

export function PlatformCockpitPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("dias_cliente");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const { data: rows = [], isLoading } = usePlatformCockpit(statusFilter || undefined);

  const sorted = useMemo(
    () =>
      [...rows].sort((a, b) => {
        const diff = a[sortKey] - b[sortKey];
        return sortDir === "asc" ? diff : -diff;
      }),
    [rows, sortKey, sortDir],
  );

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Cockpit de Métricas</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os status</option>
          {STATUS_OPTIONS.filter(Boolean).map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Carregando…</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-x-auto">
          <table className="w-full text-sm whitespace-nowrap">
            <thead className="bg-gray-50 text-gray-600 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Empresa</th>
                <th className="px-4 py-3 font-medium">Assinatura</th>
                <th className="px-4 py-3 font-medium">Último login</th>
                {COLUMNS.map(({ key, label }) => (
                  <th
                    key={key}
                    className="px-4 py-3 font-medium cursor-pointer select-none hover:bg-gray-100"
                    onClick={() => toggleSort(key)}
                  >
                    {label}
                    {key === sortKey ? (
                      <span className="ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>
                    ) : (
                      <span className="ml-1 text-gray-300">↕</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sorted.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{t.nome_fantasia}</div>
                    <div className="text-xs text-gray-400">{t.cnpj ?? "—"}</div>
                  </td>
                  <td className="px-4 py-3">
                    {t.status_assinatura ? (
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[t.status_assinatura] ?? ""}`}
                      >
                        {STATUS_LABELS[t.status_assinatura] ?? t.status_assinatura}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{fmtDate(t.ultimo_login)}</td>
                  {COLUMNS.map(({ key }) => (
                    <td key={key} className="px-4 py-3 text-gray-700">
                      {renderCell(key, t)}
                    </td>
                  ))}
                </tr>
              ))}
              {sorted.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                    Nenhum tenant encontrado
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
