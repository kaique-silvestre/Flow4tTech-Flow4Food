import { memo, useState } from "react";
import { usePlatformCockpit, type CockpitMetricsItem } from "./usePlatformApi";
import {
  SUBSCRIPTION_STATUS_OPTIONS,
  SUBSCRIPTION_STATUS_LABELS as STATUS_LABELS,
  SUBSCRIPTION_STATUS_COLORS as STATUS_COLORS,
} from "./subscriptionStatus";

const STATUS_OPTIONS = ["", ...SUBSCRIPTION_STATUS_OPTIONS] as const;

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

const CockpitRow = memo(function CockpitRow({ row }: { row: CockpitMetricsItem }) {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3">
        <div className="font-medium text-gray-900">{row.nome_fantasia}</div>
        <div className="text-xs text-gray-400">{row.cnpj ?? "—"}</div>
      </td>
      <td className="px-4 py-3">
        {row.status_assinatura ? (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[row.status_assinatura] ?? ""}`}>
            {STATUS_LABELS[row.status_assinatura] ?? row.status_assinatura}
          </span>
        ) : (
          <span className="text-gray-400">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-gray-500">{fmtDate(row.ultimo_login)}</td>
      {COLUMNS.map(({ key }) => (
        <td key={key} className="px-4 py-3 text-gray-700">
          {renderCell(key, row)}
        </td>
      ))}
    </tr>
  );
});

export function PlatformCockpitPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = usePlatformCockpit(statusFilter || undefined, page);
  const rows = data?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Cockpit de Métricas</h1>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
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
                  <th key={key} className="px-4 py-3 font-medium">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((t) => (
                <CockpitRow key={t.id} row={t} />
              ))}
              {rows.length === 0 && (
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
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-end gap-3 text-sm text-gray-600">
          <span>Página {data.page} de {data.total_pages} ({data.total} empresas)</span>
          <button type="button" onClick={() => setPage((current) => current - 1)} disabled={page === 1} className="rounded border px-3 py-1 disabled:cursor-not-allowed disabled:opacity-50">Anterior</button>
          <button type="button" onClick={() => setPage((current) => current + 1)} disabled={page >= data.total_pages} className="rounded border px-3 py-1 disabled:cursor-not-allowed disabled:opacity-50">Próxima</button>
        </div>
      )}
    </div>
  );
}
