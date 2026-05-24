import { useNavigate } from "react-router-dom";
import { BarChart3, History, DollarSign, TrendingDown, Users, FileText, BarChart2, Trophy, Clock, ShoppingBag } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface RelatorioCard {
  titulo: string;
  descricao: string;
  rota: string;
  icon: LucideIcon;
}

const RELATORIOS: RelatorioCard[] = [
  {
    titulo: "Vendas do Dia",
    descricao: "Resumo de vendas e itens mais vendidos no dia atual.",
    rota: "/relatorios/vendas-do-dia",
    icon: BarChart3,
  },
  {
    titulo: "Histórico de Comandas",
    descricao: "Lista de todas as comandas fechadas com filtros por período.",
    rota: "/relatorios/historico",
    icon: History,
  },
  {
    titulo: "Fechamento de Caixa",
    descricao: "Totais por método de pagamento no período selecionado.",
    rota: "/relatorios/fechamento-caixa",
    icon: FileText,
  },
  {
    titulo: "DRE",
    descricao: "Demonstração de resultado: faturamento, CMV, perdas e lucro bruto.",
    rota: "/relatorios/dre",
    icon: DollarSign,
  },
  {
    titulo: "CMV por Produto",
    descricao: "Custo de mercadoria vendida e margem de cada produto do cardápio.",
    rota: "/relatorios/cmv",
    icon: BarChart2,
  },
  {
    titulo: "Perdas e Cortesias",
    descricao: "Baixas sem venda agrupadas por motivo no período.",
    rota: "/relatorios/perdas-cortesias",
    icon: TrendingDown,
  },
  {
    titulo: "Vendas por Garçom",
    descricao: "Ranking de faturamento e ticket médio por garçom.",
    rota: "/relatorios/vendas-por-garcom",
    icon: Users,
  },
  {
    titulo: "Produtos Mais Vendidos",
    descricao: "Ranking de itens por quantidade e receita no período.",
    rota: "/relatorios/produtos-mais-vendidos",
    icon: Trophy,
  },
  {
    titulo: "Pico de Vendas por Horário",
    descricao: "Distribuição de fechamentos por hora do dia — identifique horários de pico.",
    rota: "/relatorios/pico-vendas-horario",
    icon: Clock,
  },
  {
    titulo: "Vendas por Produto",
    descricao: "Ranking de produtos por faturamento, quantidade vendida e ticket médio.",
    rota: "/relatorios/vendas-por-produto",
    icon: ShoppingBag,
  },
];

export function RelatoriosIndexPage() {
  const navigate = useNavigate();

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Relatórios</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {RELATORIOS.map((r) => (
          <button
            key={r.rota}
            onClick={() => navigate(r.rota)}
            className="flex items-start gap-4 rounded-lg border bg-white p-5 text-left shadow-sm transition-shadow hover:shadow-md"
          >
            <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-700">
              <r.icon size={20} />
            </span>
            <div>
              <p className="font-medium text-gray-900">{r.titulo}</p>
              <p className="mt-0.5 text-sm text-gray-500">{r.descricao}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
