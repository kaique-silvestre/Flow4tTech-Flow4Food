# PRP — Issue #12: M010 Índice de Relatórios em /relatorios

**Type:** AFK
**Status:** Planejado
**Criado em:** 2026-05-08
**Depende de:** Nenhum

---

## Objetivo

Substituir o `PlaceholderPage` que aparece em `/relatorios` por uma página índice com cards navegáveis para cada sub-relatório disponível.

---

## Estado Atual

`App.tsx` tem rota `path="*"` → `PlaceholderPage`. A rota `/relatorios` não está explícita e cai no catch-all.

Sub-relatórios existentes:
- `/relatorios/vendas-do-dia` → `VendasDoDiaPage`
- `/relatorios/historico` → `HistoricoComandasPage`
- `/relatorios/fechamento-caixa` → `FechamentoCaixaPage`
- `/relatorios/dre` → `DrePage`
- `/relatorios/cmv` → `CmvPorProdutoPage`
- `/relatorios/perdas-cortesias` → `PerdasCortesiasPage`
- `/relatorios/vendas-por-garcom` → `VendasPorGarcomPage`

---

## Estrutura de Arquivos a Criar/Modificar

```
frontend/src/features/relatorios/RelatoriosIndexPage.tsx   # (criar)
frontend/src/App.tsx                                        # (modificar) rota /relatorios
```

---

## Tarefas

### A — Criar RelatoriosIndexPage.tsx

**A1.** Criar `frontend/src/features/relatorios/RelatoriosIndexPage.tsx`:

```tsx
import { useNavigate } from "react-router-dom";
import { BarChart3, History, DollarSign, TrendingDown, Users, FileText, BarChart2 } from "lucide-react";
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
```

### B — Modificar App.tsx

**B1.** Adicionar import:
```tsx
import { RelatoriosIndexPage } from "@/features/relatorios/RelatoriosIndexPage";
```

**B2.** Adicionar rota explícita **antes** do catch-all `path="*"`:
```tsx
<Route path="/relatorios" element={<RelatoriosIndexPage />} />
```

---

## Critérios de Aceite

- [ ] `/relatorios` não exibe mais placeholder vazio
- [ ] Página exibe grid de cards com todos os 7 sub-relatórios listados
- [ ] Cada card tem título e descrição de 1 linha
- [ ] Clicar em card navega para a rota do relatório correspondente
- [ ] Sidebar link "Relatórios" navega para `/relatorios` (índice)

---

## Validações

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```
