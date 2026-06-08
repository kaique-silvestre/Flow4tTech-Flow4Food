import { useNavigate, useParams } from "react-router-dom";
import { useComanda } from "./useComandas";
import { useEstabelecimento } from "@/features/configuracoes/useEstabelecimento";
import { formatQuantidade, parseApiDate } from "@/lib/format";

const brl = (value: number | null | undefined) =>
  value != null
    ? new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value)
    : null;

const fmtData = (iso: string | null | undefined) => {
  if (!iso) return "—";
  return parseApiDate(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export function PreContaPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: comanda, isLoading, isError } = useComanda(Number(id));
  const { data: estabelecimento } = useEstabelecimento();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="w-80 space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-8 animate-pulse rounded bg-gray-200" />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !comanda) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 gap-4">
        <p className="text-red-600 font-medium">Comanda não encontrada.</p>
        <button
          onClick={() => navigate("/vendas/comandas")}
          className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700"
        >
          Voltar às comandas
        </button>
      </div>
    );
  }

  const itensAtivos = comanda.itens_ativos.filter((i) => !i.cancelado);

  return (
    <div className="print-wrapper min-h-screen bg-gray-100 flex flex-col items-center py-8 px-4">
      <style>{`
        @media print {
          @page {
            size: 80mm auto;
            margin: 0mm;
          }
          html {
            width: 80mm !important;
            margin: 0 !important;
            padding: 0 !important;
          }
          body {
            background: white !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 80mm !important;
            min-height: unset !important;
          }
          .no-print,
          [data-sonner-toaster] { display: none !important; }
          .print-wrapper {
            display: block !important;
            width: 80mm !important;
            min-height: unset !important;
            padding: 0 !important;
            margin: 0 !important;
            background: white !important;
          }
          .print-container {
            box-shadow: none !important;
            border: none !important;
            border-radius: 0 !important;
            width: 80mm !important;
            max-width: 80mm !important;
            padding: 3mm 4mm !important;
            margin: 0 !important;
            font-size: 10.5px !important;
            line-height: 1.35 !important;
            color: #000 !important;
          }
          .print-container * {
            color: #000 !important;
          }
        }
      `}</style>

      <div className="no-print flex gap-3 mb-6 w-full max-w-sm">
        <button
          onClick={() => window.print()}
          className="flex-1 min-h-[44px] px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 font-medium"
        >
          Imprimir
        </button>
        <button
          onClick={() => navigate(`/vendas/comandas/${id}`)}
          className="flex-1 min-h-[44px] px-4 py-2 border border-gray-400 text-gray-700 rounded hover:bg-gray-50 font-medium"
        >
          Voltar à comanda
        </button>
      </div>

      <div
        className="print-container bg-white w-full max-w-sm p-6 font-mono text-sm shadow-md rounded"
        style={{ maxWidth: "320px" }}
      >
        <div className="text-center mb-4 border-b pb-3">
          <p className="font-bold text-base uppercase">
            {estabelecimento?.nome ?? "ESTABELECIMENTO"}
          </p>
          {estabelecimento?.cnpj && (
            <p className="text-xs text-gray-600">CNPJ: {estabelecimento.cnpj}</p>
          )}
          {estabelecimento?.endereco && (
            <p className="text-xs text-gray-600">{estabelecimento.endereco}</p>
          )}
          {estabelecimento?.telefone && (
            <p className="text-xs text-gray-600">Tel: {estabelecimento.telefone}</p>
          )}
        </div>

        <div className="mb-3 border-b pb-3 text-xs text-gray-700">
          <p>{fmtData(new Date().toISOString())}</p>
          <p>
            Comanda {comanda.numero_dia != null ? `#${comanda.numero_dia}` : `#${comanda.id}`} —{" "}
            {comanda.tipo_identificacao === "mesa" ? "Mesa " : ""}
            {comanda.identificacao}
          </p>
          <p>Garçom: {comanda.garcom_nome}</p>
          {comanda.pessoas.length > 0 && (
            <p>Pessoas: {comanda.pessoas.join(", ")}</p>
          )}
        </div>

        <div className="mb-3 border-b pb-3">
          {itensAtivos.length === 0 ? (
            <p className="text-xs text-gray-400">Nenhum item lançado.</p>
          ) : (
            itensAtivos.map((ic) => (
              <div key={ic.id} className="flex justify-between gap-2 text-xs mb-1">
                <span className="flex-1">
                  {formatQuantidade(ic.quantidade)}x {ic.item_nome}
                  {ic.cortesia && <span className="text-gray-500"> (cortesia)</span>}
                  {ic.pessoa_associada && <span className="text-gray-500"> [{ic.pessoa_associada}]</span>}
                  {ic.observacao && <span className="text-gray-500"> — {ic.observacao}</span>}
                </span>
                <span className="whitespace-nowrap">{brl(Number(ic.subtotal))}</span>
              </div>
            ))
          )}
        </div>

        <div className="mb-3 text-xs">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>{brl(Number(comanda.total_parcial))}</span>
          </div>
          <div className="flex justify-between font-bold text-sm mt-1">
            <span>TOTAL PARCIAL</span>
            <span>{brl(Number(comanda.total_parcial))}</span>
          </div>
        </div>

        <p className="text-center text-xs font-bold tracking-wide mt-2 border-t pt-2">
          *** NÃO É CUPOM FISCAL ***
        </p>
      </div>
    </div>
  );
}
