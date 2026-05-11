import { useNavigate, useParams } from "react-router-dom";
import { useComprovante } from "./useComprovante";
import { formatQuantidade } from "@/lib/format";

const brl = (value: number | null | undefined) =>
  value != null
    ? new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value)
    : null;

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

export function ComprovantePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useComprovante(id);

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

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 gap-4">
        <p className="text-red-600 font-medium">Comprovante não encontrado.</p>
        <button
          onClick={() => navigate("/comandas")}
          className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700"
        >
          Voltar às comandas
        </button>
      </div>
    );
  }

  const temDesconto = data.desconto_percentual != null || data.desconto_valor != null;
  const descontoLabel = data.desconto_percentual != null
    ? `-${data.desconto_percentual}%`
    : data.desconto_valor != null
    ? `-${brl(data.desconto_valor)}`
    : null;

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center py-8 px-4">
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; }
          .print-container { box-shadow: none !important; border: none !important; }
        }
      `}</style>

      {/* Botões de ação (ocultos no print) */}
      <div className="no-print flex gap-3 mb-6 w-full max-w-sm">
        <button
          onClick={() => window.print()}
          className="flex-1 px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 font-medium"
        >
          Imprimir
        </button>
        <button
          onClick={() => navigate("/comandas")}
          className="flex-1 px-4 py-2 border border-gray-400 text-gray-700 rounded hover:bg-gray-50 font-medium"
        >
          Voltar às comandas
        </button>
      </div>

      {/* Comprovante */}
      <div
        className="print-container bg-white w-full max-w-sm p-6 font-mono text-sm shadow-md rounded"
        style={{ maxWidth: "320px" }}
      >
        {/* Cabeçalho estabelecimento */}
        <div className="text-center mb-4 border-b pb-3">
          <p className="font-bold text-base uppercase">{data.estabelecimento.nome}</p>
          {data.estabelecimento.cnpj && (
            <p className="text-xs text-gray-600">CNPJ: {data.estabelecimento.cnpj}</p>
          )}
          {data.estabelecimento.endereco && (
            <p className="text-xs text-gray-600">{data.estabelecimento.endereco}</p>
          )}
          {data.estabelecimento.telefone && (
            <p className="text-xs text-gray-600">Tel: {data.estabelecimento.telefone}</p>
          )}
        </div>

        {/* Info da comanda */}
        <div className="mb-3 border-b pb-3 text-xs text-gray-700">
          <p>{fmtData(data.data_fechamento)}</p>
          <p>
            Comanda #{data.comanda_id} — {data.identificacao}
          </p>
          <p>Garçom: {data.garcom_nome}</p>
        </div>

        {/* Itens */}
        <div className="mb-3 border-b pb-3">
          {data.itens.map((item, i) => (
            <div key={i} className="flex justify-between gap-2 text-xs mb-1">
              <span className="flex-1 truncate">
                {formatQuantidade(item.quantidade)}x {item.nome}
                {item.cortesia && (
                  <span className="text-gray-500"> (cortesia)</span>
                )}
              </span>
              <span className="whitespace-nowrap">{brl(item.subtotal)}</span>
            </div>
          ))}
        </div>

        {/* Totais */}
        <div className="mb-3 border-b pb-3 text-xs">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>{brl(data.subtotal)}</span>
          </div>
          {temDesconto && descontoLabel && (
            <div className="flex justify-between text-gray-600">
              <span>Desconto</span>
              <span>{descontoLabel}</span>
            </div>
          )}
          <div className="flex justify-between font-bold text-sm mt-1">
            <span>TOTAL</span>
            <span>{brl(data.total ?? data.subtotal)}</span>
          </div>
        </div>

        {/* Pagamentos */}
        {data.pagamentos.length > 0 && (
          <div className="mb-3 border-b pb-3 text-xs">
            {data.pagamentos.map((p, i) => (
              <div key={i} className="flex justify-between">
                <span>{p.metodo_nome}</span>
                <span>{brl(p.valor)}</span>
              </div>
            ))}
          </div>
        )}

        {/* Aviso fiscal */}
        <p className="text-center text-xs font-bold tracking-wide mt-2">
          *** NÃO É CUPOM FISCAL ***
        </p>
      </div>
    </div>
  );
}
