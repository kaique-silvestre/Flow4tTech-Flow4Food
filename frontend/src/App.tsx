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
import { queryClient } from "@/lib/queryClient";
import { PlaceholderPage } from "@/pages/PlaceholderPage";

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RequireAuth />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<PlaceholderPage />} />
              <Route path="/cadastros/itens" element={<ItensPage />} />
              <Route path="/cadastros/categorias" element={<CategoriasPage />} />
              <Route path="/cadastros/fornecedores" element={<FornecedoresPage />} />
              <Route path="/cadastros/garcons" element={<GarconsPage />} />
              <Route path="/cadastros/metodos-pagamento" element={<MetodosPagamentoPage />} />
              <Route path="*" element={<PlaceholderPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
