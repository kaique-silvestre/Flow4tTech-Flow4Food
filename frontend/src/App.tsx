import * as Sentry from "@sentry/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { LoginPage } from "@/features/auth/LoginPage";
import { CategoriasPage } from "@/features/cadastros/categorias/CategoriasPage";
import { FornecedoresPage } from "@/features/cadastros/fornecedores/FornecedoresPage";
import { GarconsPage } from "@/features/cadastros/garcons/GarconsPage";
import { MetodosPagamentoPage } from "@/features/cadastros/metodos_pagamento/MetodosPagamentoPage";
import { InsumosPage } from "@/features/cadastros/insumos/InsumosPage";
import { ComprasPage } from "@/features/compras/ComprasPage";
import { NovaCompraPage } from "@/features/compras/NovaCompraPage";
import { EstoquePage } from "@/features/estoque/EstoquePage";
import { MovimentosPage } from "@/features/estoque/MovimentosPage";
import { ComandasPage } from "@/features/comandas/ComandasPage";
import { ComandaAbertaPage } from "@/features/comandas/ComandaAbertaPage";
import FechamentoPage from "@/features/comandas/FechamentoPage";
import { ComprovantePage } from "@/features/comandas/ComprovantePage";
import { VendasDoDiaPage } from "@/features/relatorios/VendasDoDiaPage";
import { HistoricoComandasPage } from "@/features/relatorios/HistoricoComandasPage";
import { FechamentoCaixaPage } from "@/features/relatorios/FechamentoCaixaPage";
import { DrePage } from "@/features/relatorios/DrePage";
import { CmvPorProdutoPage } from "@/features/relatorios/CmvPorProdutoPage";
import { PerdasCortesiasPage } from "@/features/relatorios/PerdasCortesiasPage";
import { VendasPorGarcomPage } from "@/features/relatorios/VendasPorGarcomPage";
import { RelatoriosIndexPage } from "@/features/relatorios/RelatoriosIndexPage";
import { HistoricoPage } from "@/features/historico/HistoricoPage";
import { ConfiguracoesPage } from "@/features/configuracoes/ConfiguracoesPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { CardapioPage } from "@/features/cardapio/CardapioPage";
import { queryClient } from "@/lib/queryClient";
import { PlaceholderPage } from "@/pages/PlaceholderPage";

export function App() {
  return (
    <Sentry.ErrorBoundary fallback={<p className="p-8 text-red-600">Erro inesperado. Recarregue a página.</p>}>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RequireAuth />}>
            <Route path="/comprovante/:id" element={<ComprovantePage />} />
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/comandas" element={<ComandasPage />} />
              <Route path="/comandas/:id" element={<ComandaAbertaPage />} />
              <Route path="/comandas/:id/fechar" element={<FechamentoPage />} />
              <Route path="/compras" element={<ComprasPage />} />
              <Route path="/compras/nova" element={<NovaCompraPage />} />
              <Route path="/estoque" element={<EstoquePage />} />
              <Route path="/estoque/movimentos" element={<MovimentosPage />} />
              <Route path="/cadastros/categorias" element={<CategoriasPage />} />
              <Route path="/cadastros/fornecedores" element={<FornecedoresPage />} />
              <Route path="/cadastros/garcons" element={<GarconsPage />} />
              <Route path="/cadastros/metodos-pagamento" element={<MetodosPagamentoPage />} />
              <Route path="/cadastros/insumos" element={<InsumosPage />} />
              <Route path="/historico" element={<HistoricoPage />} />
              <Route path="/relatorios" element={<RelatoriosIndexPage />} />
              <Route path="/relatorios/vendas-do-dia" element={<VendasDoDiaPage />} />
              <Route path="/relatorios/historico" element={<HistoricoComandasPage />} />
              <Route path="/relatorios/fechamento-caixa" element={<FechamentoCaixaPage />} />
              <Route path="/relatorios/dre" element={<DrePage />} />
              <Route path="/relatorios/cmv" element={<CmvPorProdutoPage />} />
              <Route path="/relatorios/perdas-cortesias" element={<PerdasCortesiasPage />} />
              <Route path="/relatorios/vendas-por-garcom" element={<VendasPorGarcomPage />} />
              <Route path="/cardapio" element={<CardapioPage />} />
              <Route path="/configuracoes" element={<ConfiguracoesPage />} />
              <Route path="*" element={<PlaceholderPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors closeButton />
    </QueryClientProvider>
    </Sentry.ErrorBoundary>
  );
}
