import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { LoginPage } from "@/features/auth/LoginPage";
import { CategoriasPage } from "@/features/cadastros/categorias/CategoriasPage";
import { ItensPage } from "@/features/cadastros/itens/ItensPage";
import { FornecedoresPage } from "@/features/cadastros/fornecedores/FornecedoresPage";
import { GarconsPage } from "@/features/cadastros/garcons/GarconsPage";
import { MetodosPagamentoPage } from "@/features/cadastros/metodos_pagamento/MetodosPagamentoPage";
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
import { queryClient } from "@/lib/queryClient";
import { PlaceholderPage } from "@/pages/PlaceholderPage";

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RequireAuth />}>
            <Route path="/comprovante/:id" element={<ComprovantePage />} />
            <Route element={<AppLayout />}>
              <Route path="/" element={<PlaceholderPage />} />
              <Route path="/comandas" element={<ComandasPage />} />
              <Route path="/comandas/:id" element={<ComandaAbertaPage />} />
              <Route path="/comandas/:id/fechar" element={<FechamentoPage />} />
              <Route path="/compras" element={<ComprasPage />} />
              <Route path="/compras/nova" element={<NovaCompraPage />} />
              <Route path="/estoque" element={<EstoquePage />} />
              <Route path="/estoque/movimentos" element={<MovimentosPage />} />
              <Route path="/cadastros/itens" element={<ItensPage />} />
              <Route path="/cadastros/categorias" element={<CategoriasPage />} />
              <Route path="/cadastros/fornecedores" element={<FornecedoresPage />} />
              <Route path="/cadastros/garcons" element={<GarconsPage />} />
              <Route path="/cadastros/metodos-pagamento" element={<MetodosPagamentoPage />} />
              <Route path="/relatorios/vendas-do-dia" element={<VendasDoDiaPage />} />
              <Route path="/relatorios/historico" element={<HistoricoComandasPage />} />
              <Route path="/relatorios/fechamento-caixa" element={<FechamentoCaixaPage />} />
              <Route path="*" element={<PlaceholderPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
