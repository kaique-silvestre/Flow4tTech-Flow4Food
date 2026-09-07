import * as Sentry from "@sentry/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { RequirePermission } from "@/components/auth/RequirePermission";
import { LoginPage } from "@/features/auth/LoginPage";
import { EsqueciSenhaPage } from "@/features/auth/EsqueciSenhaPage";
import { RedefinirSenhaPage } from "@/features/auth/RedefinirSenhaPage";
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
import { PreContaPage } from "@/features/comandas/PreContaPage";
import { VendasDoDiaPage } from "@/features/relatorios/VendasDoDiaPage";
import { HistoricoComandasPage } from "@/features/relatorios/HistoricoComandasPage";
import { FechamentoCaixaPage } from "@/features/relatorios/FechamentoCaixaPage";
import { DrePage } from "@/features/relatorios/DrePage";
import { CmvPorProdutoPage } from "@/features/relatorios/CmvPorProdutoPage";
import { PerdasCortesiasPage } from "@/features/relatorios/PerdasCortesiasPage";
import { VendasPorGarcomPage } from "@/features/relatorios/VendasPorGarcomPage";
import { ProdutosMaisVendidosPage } from "@/features/relatorios/ProdutosMaisVendidosPage";
import { PicoVendasHorarioPage } from "@/features/relatorios/PicoVendasHorarioPage";
import { VendasPorProdutoPage } from "@/features/relatorios/VendasPorProdutoPage";
import { RelatoriosIndexPage } from "@/features/relatorios/RelatoriosIndexPage";
import { ConfiguracoesPage } from "@/features/configuracoes/ConfiguracoesPage";
import { GestaoUsuariosPage } from "@/features/configuracoes/usuarios/GestaoUsuariosPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { CardapioPage } from "@/features/cardapio/CardapioPage";
import { ProdutoPage } from "@/features/cardapio/ProdutoPage";
import { ContasPagarPage } from "@/features/contas_pagar/ContasPagarPage";
import { CaixaPage } from "@/features/caixa/CaixaPage";
import { AssinaturaVencidaPage } from "@/features/assinatura/AssinaturaVencidaPage";
import { ContaSuspensaPage } from "@/features/assinatura/ContaSuspensaPage";
import { BlockedPage } from "@/features/assinatura/BlockedPage";
import { queryClient } from "@/lib/queryClient";
import { ConsumoInternoPage } from "@/features/consumo_interno/ConsumoInternoPage";
import { ConsumoInternoDetalhePage } from "@/features/consumo_interno/ConsumoInternoDetalhePage";
import { CalendarioPage } from "@/features/calendario/CalendarioPage";
import { PromocoesPage } from "@/features/cadastros/promocoes/PromocoesPage";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { RequirePlatformAuth } from "@/components/auth/RequirePlatformAuth";
import { PlatformLoginPage } from "@/features/platform/PlatformLoginPage";
import { PlatformLayout } from "@/features/platform/PlatformLayout";
import { PlatformTenantsPage } from "@/features/platform/PlatformTenantsPage";
import { PlatformTenantDetailPage } from "@/features/platform/PlatformTenantDetailPage";
import { PlatformCockpitPage } from "@/features/platform/PlatformCockpitPage";
import { PlatformAnnouncementsPage } from "@/features/platform/PlatformAnnouncementsPage";
import { PlatformAuditPage } from "@/features/platform/PlatformAuditPage";

export function App() {
  return (
    <Sentry.ErrorBoundary fallback={<p className="p-8 text-red-600">Erro inesperado. Recarregue a página.</p>}>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/platform/login" element={<PlatformLoginPage />} />
          <Route element={<RequirePlatformAuth />}>
            <Route element={<PlatformLayout />}>
              <Route path="/platform/tenants" element={<PlatformTenantsPage />} />
              <Route path="/platform/tenants/:tenantId" element={<PlatformTenantDetailPage />} />
              <Route path="/platform/cockpit" element={<PlatformCockpitPage />} />
              <Route path="/platform/announcements" element={<PlatformAnnouncementsPage />} />
              <Route path="/platform/audit" element={<PlatformAuditPage />} />
            </Route>
          </Route>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/esqueci-senha" element={<EsqueciSenhaPage />} />
          <Route path="/redefinir-senha" element={<RedefinirSenhaPage />} />
          <Route path="/blocked" element={<BlockedPage />} />
          <Route element={<RequireAuth />}>
            <Route path="/assinatura-vencida" element={<AssinaturaVencidaPage />} />
            <Route path="/conta-suspensa" element={<ContaSuspensaPage />} />
            <Route path="/comprovante/:id" element={<ComprovantePage />} />
            <Route path="/vendas/comandas/:id/pre-conta" element={<PreContaPage />} />
            <Route element={<AppLayout />}>
              <Route element={<RequirePermission screen="dashboard" />}>
                <Route path="/" element={<DashboardPage />} />
              </Route>
              <Route element={<RequirePermission screen="comandas" />}>
                <Route path="/vendas/comandas" element={<ComandasPage />} />
                <Route path="/vendas/comandas/:id" element={<ComandaAbertaPage />} />
                <Route path="/vendas/comandas/:id/fechar" element={<FechamentoPage />} />
                <Route path="/cardapio" element={<CardapioPage />} />
                <Route path="/cardapio/:id" element={<ProdutoPage />} />
              </Route>
              <Route element={<RequirePermission screen="consumo_interno" />}>
                <Route path="/consumo-interno" element={<ConsumoInternoPage />} />
                <Route path="/consumo-interno/:consumidorId" element={<ConsumoInternoDetalhePage />} />
              </Route>
              <Route element={<RequirePermission screen="compras" />}>
                <Route path="/compras" element={<ComprasPage />} />
                <Route path="/compras/nova" element={<NovaCompraPage />} />
                <Route path="/contas-pagar" element={<ContasPagarPage />} />
              </Route>
              <Route element={<RequirePermission screen="estoque" />}>
                <Route path="/estoque" element={<EstoquePage />} />
                <Route path="/estoque/movimentos" element={<MovimentosPage />} />
              </Route>
              <Route element={<RequirePermission screen="cadastros" />}>
                <Route path="/cadastros/categorias" element={<CategoriasPage />} />
                <Route path="/cadastros/fornecedores" element={<FornecedoresPage />} />
                <Route path="/cadastros/garcons" element={<GarconsPage />} />
                <Route path="/cadastros/metodos-pagamento" element={<MetodosPagamentoPage />} />
                <Route path="/cadastros/insumos" element={<InsumosPage />} />
                <Route path="/cadastros/promocoes" element={<PromocoesPage />} />
              </Route>
              <Route element={<RequirePermission screen="relatorios" />}>
                <Route path="/relatorios" element={<Navigate to="/relatorios/vendas" replace />} />
                <Route path="/relatorios/vendas" element={<RelatoriosIndexPage />} />
                <Route path="/relatorios/compras" element={<RelatoriosIndexPage />} />
                <Route path="/relatorios/financeiro" element={<RelatoriosIndexPage />} />
                <Route path="/relatorios/vendas-do-dia" element={<VendasDoDiaPage />} />
                <Route path="/relatorios/historico" element={<HistoricoComandasPage />} />
                <Route path="/relatorios/fechamento-caixa" element={<FechamentoCaixaPage />} />
                <Route path="/relatorios/dre" element={<DrePage />} />
                <Route path="/relatorios/cmv" element={<CmvPorProdutoPage />} />
                <Route path="/relatorios/perdas-cortesias" element={<PerdasCortesiasPage />} />
                <Route path="/relatorios/vendas-por-garcom" element={<VendasPorGarcomPage />} />
                <Route path="/relatorios/produtos-mais-vendidos" element={<ProdutosMaisVendidosPage />} />
                <Route path="/relatorios/pico-vendas-horario" element={<PicoVendasHorarioPage />} />
                <Route path="/relatorios/vendas-por-produto" element={<VendasPorProdutoPage />} />
              </Route>
              <Route element={<RequirePermission screen="caixa" />}>
                <Route path="/caixa" element={<CaixaPage />} />
              </Route>
              <Route element={<RequirePermission screen="calendario" />}>
                <Route path="/calendario" element={<CalendarioPage />} />
              </Route>
              <Route element={<RequirePermission screen="configuracoes" />}>
                <Route path="/configuracoes/gerais" element={<ConfiguracoesPage />} />
              </Route>
              <Route element={<RequirePermission screen="gestao_usuarios" />}>
                <Route path="/configuracoes/usuarios" element={<GestaoUsuariosPage />} />
              </Route>
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
