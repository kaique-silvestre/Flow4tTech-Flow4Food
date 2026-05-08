# PRP — Issue #14: UX Sweep — Confirmações, Toasts, Sentry, QA Visual

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 14
**Documento mestre:** `docs/matchpoint_documentacao.md` §5.3
**Type:** AFK (crosscutting)
**Status:** Concluída ✓ (2026-05-08)
**Criado em:** 2026-05-08
**Depende de:** Todas as demais issues concluídas

---

## Objetivo

Sweep transversal de UX antes da entrega:
- Componente `ConfirmDialog` reutilizável em todas as ações destrutivas.
- Toast wrapper com durações padronizadas (sucesso 2.5s / erro persistente / aviso 4.5s).
- Sentry FE: ErrorBoundary + unhandledrejection + captura de respostas 500.
- Sidebar colapsável em viewport ≤1366px.
- Skeletons em páginas que usam "Carregando..." texto simples.
- Manual de operação (1 página).
- Checklist QA visual 1280×720 e 1366×768.

---

## Estado Atual (o que já existe)

- Backend Sentry: `src/core/sentry.py` + `init_sentry()` em `main.py` — **já implementado**.
- Frontend Sentry: `src/lib/sentry.ts` `initSentry()` chamado em `main.tsx` — init OK, mas sem ErrorBoundary nem captura de 500.
- Toaster: `<Toaster position="top-right" richColors />` — sem config de duração global.
- Toast calls: 13 arquivos importam `toast` de `"sonner"` diretamente — sem padronização de duração.
- `window.confirm()` em: `ItensPage.tsx`, `CategoriasPage.tsx`, `FornecedoresPage.tsx`.
- Inline confirm dialog (não reutilizável) em: `ComandaAbertaPage.tsx` (reabrir comanda).
- `ComandaAbertaPage.tsx`: loading = texto "Carregando..." — sem skeleton.
- `ComprovantePage.tsx`: loading = texto "Carregando comprovante..." — sem skeleton.
- Sidebar: largura fixa `w-48`, sem collapse.

---

## Regras de Negócio Críticas

- `ConfirmDialog` apenas para confirms simples (sem form). Modais com form (CancelarItemModal, BaixaSemVendaModal, AplicarDescontoModal) continuam como estão.
- Toast durations: sucesso 2500ms, erro `Infinity`, aviso 4500ms.
- Sentry ErrorBoundary envolve toda a app. Não interfere em dev (sem DSN).
- Sidebar: em `window.innerWidth ≤ 1366` inicia colapsado (apenas ícones/labels, não hidden — mantém navegação).
- Skeleton de loading: usar `animate-pulse` divs (padrão já existe em ItensPage) — não adicionar shadcn/Skeleton novo.
- Backend Sentry: **já OK** — não tocar.

---

## Estrutura de Arquivos a Criar/Modificar

```
frontend/
  src/
    lib/
      toast.ts                          # (criar) wrapper com durações padrão
    components/
      ui/
        confirm-dialog.tsx              # (criar) ConfirmDialog reutilizável
      layout/
        Sidebar.tsx                     # (modificar) collapse ≤1366px
        AppLayout.tsx                   # (modificar) estado collapsed + context
    features/
      cadastros/
        itens/
          ItensPage.tsx                 # (modificar) window.confirm → ConfirmDialog
        categorias/
          CategoriasPage.tsx            # (modificar) window.confirm → ConfirmDialog
        fornecedores/
          FornecedoresPage.tsx          # (modificar) window.confirm → ConfirmDialog
      comandas/
        ComandaAbertaPage.tsx           # (modificar) inline confirm → ConfirmDialog + skeleton loading
      configuracoes/
        ConfiguracoesPage.tsx           # (modificar) toast imports → @/lib/toast
    App.tsx                             # (modificar) Sentry ErrorBoundary + Toaster duration

docs/
  manual-operacao.md                    # (criar) 1 página fluxo abrir→fechar comanda
  qa-checklist.md                       # (criar) smoke test 1280×720 e 1366×768
```

**Nota:** Todos os 13 arquivos que importam `toast` de `"sonner"` devem ser atualizados para `@/lib/toast`.

---

## Tarefas

### Bloco A — Toast Wrapper

- [ ] **A1.** Criar `frontend/src/lib/toast.ts`:

```ts
import { toast as sonner } from "sonner";

export const toast = {
  success: (msg: string) => sonner.success(msg, { duration: 2500 }),
  error: (msg: string, opts?: { description?: string }) =>
    sonner.error(msg, { duration: Infinity, ...opts }),
  warning: (msg: string) => sonner.warning(msg, { duration: 4500 }),
};
```

- [ ] **A2.** Substituir `import { toast } from "sonner"` por `import { toast } from "@/lib/toast"` em todos os 13 arquivos:
  - `features/auth/useLogin.ts`
  - `features/compras/useCompras.ts`
  - `features/cadastros/fornecedores/useFornecedores.ts`
  - `features/estoque/useEstoque.ts`
  - `features/cadastros/itens/useItens.ts`
  - `features/cadastros/metodos_pagamento/useMetodosPagamento.ts`
  - `features/comandas/useComandas.ts`
  - `features/cadastros/garcons/useGarcons.ts`
  - `features/cadastros/categorias/useCategorias.ts`
  - `features/comandas/useFechamento.ts`
  - `features/configuracoes/ConfiguracoesPage.tsx`
  - `pages/PlaceholderPage.tsx`

  Remover `duration: Infinity` hardcoded dos `toast.error()` existentes (já virá do wrapper).
  Remover `duration: 4500` hardcoded dos `toast.warning()` existentes.

---

### Bloco B — ConfirmDialog

- [ ] **B1.** Criar `frontend/src/components/ui/confirm-dialog.tsx`:

```tsx
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isPending?: boolean;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirmar",
  onConfirm,
  onCancel,
  isPending = false,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onCancel()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        {description && (
          <p className="text-sm text-gray-500">{description}</p>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onCancel} disabled={isPending}>
            Cancelar
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isPending}
          >
            {isPending ? "Aguarde..." : confirmLabel}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

### Bloco C — Substituir window.confirm em Cadastros

- [ ] **C1.** `ItensPage.tsx` — substituir `window.confirm()` por `ConfirmDialog`:
  - Adicionar estado: `const [confirmDelete, setConfirmDelete] = useState<number | null>(null);`
  - Botão "Remover": `onClick={() => setConfirmDelete(item.id)}` (sem confirm inline)
  - Adicionar ao JSX:
    ```tsx
    <ConfirmDialog
      open={confirmDelete !== null}
      title="Remover item?"
      description="Se referenciado em ficha técnica, será apenas inativado."
      confirmLabel="Remover"
      onConfirm={() => { deleteMutation.mutate(confirmDelete!); setConfirmDelete(null); }}
      onCancel={() => setConfirmDelete(null)}
      isPending={deleteMutation.isPending}
    />
    ```

- [ ] **C2.** `CategoriasPage.tsx` — mesmo padrão. Checar estado atual e adaptar.

- [ ] **C3.** `FornecedoresPage.tsx` — mesmo padrão. Checar estado atual e adaptar.

---

### Bloco D — Substituir Inline Confirm em ComandaAbertaPage

- [ ] **D1.** `ComandaAbertaPage.tsx`:
  - Remover o bloco `{confirmReabrir && <div className="fixed inset-0...">...</div>}` (linha 131–151).
  - Substituir por:
    ```tsx
    <ConfirmDialog
      open={confirmReabrir}
      title="Reabrir comanda?"
      description="Os pagamentos serão estornados e o estoque restaurado."
      confirmLabel="Reabrir"
      onConfirm={() => reopenComanda.mutate()}
      onCancel={() => setConfirmReabrir(false)}
      isPending={reopenComanda.isPending}
    />
    ```
  - Substituir loading "Carregando..." (linha 90) por skeleton:
    ```tsx
    if (isLoading || !comanda) {
      return (
        <div className="p-6 space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      );
    }
    ```

---

### Bloco E — Skeleton em ComprovantePage

- [ ] **E1.** `ComprovantePage.tsx` — substituir loading "Carregando comprovante..." por:
  ```tsx
  <div className="flex items-center justify-center min-h-screen bg-gray-100">
    <div className="w-80 space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="h-8 animate-pulse rounded bg-gray-200" />
      ))}
    </div>
  </div>
  ```

---

### Bloco F — Sentry ErrorBoundary no Frontend

- [ ] **F1.** `App.tsx` — envolver app em `Sentry.ErrorBoundary`:

```tsx
import * as Sentry from "@sentry/react";

// Dentro de return, envolver o QueryClientProvider:
<Sentry.ErrorBoundary fallback={<p className="p-8 text-red-600">Erro inesperado. Recarregue a página.</p>}>
  <QueryClientProvider ...>
    ...
    <Toaster position="top-right" richColors />
  </QueryClientProvider>
</Sentry.ErrorBoundary>
```

- [ ] **F2.** `lib/sentry.ts` — adicionar captura de `unhandledrejection`:

```ts
export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return;
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  });
  window.addEventListener("unhandledrejection", (e) => {
    Sentry.captureException(e.reason);
  });
}
```

- [ ] **F3.** `lib/api.ts` — capturar respostas 500 no interceptor de erro:

```ts
import * as Sentry from "@sentry/react";

// No interceptor de response error, antes de return Promise.reject(error):
if (error.response?.status && error.response.status >= 500) {
  Sentry.captureException(error);
}
```

---

### Bloco G — Sidebar Colapsável

- [ ] **G1.** `AppLayout.tsx` — adicionar estado `collapsed` com `useState(window.innerWidth <= 1366)`:

```tsx
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(window.innerWidth <= 1366);

  return (
    <div className="flex h-screen">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

- [ ] **G2.** `Sidebar.tsx` — aceitar `collapsed` e `onToggle` props. Quando colapsado: `w-12`, mostrar apenas ícones/abreviações e botão toggle. Quando expandido: `w-48`, comportamento atual.

```tsx
interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside className={`flex flex-col border-r bg-white transition-all ${collapsed ? "w-12" : "w-48"}`}>
      <button
        className="flex items-center justify-center h-10 border-b text-gray-400 hover:text-gray-700"
        onClick={onToggle}
        title={collapsed ? "Expandir menu" : "Colapsar menu"}
      >
        {collapsed ? "›" : "‹"}
      </button>
      <nav className="flex flex-col gap-1 p-2 pt-2">
        {NAV_ITEMS.map((item) =>
          item.to === null ? (
            collapsed ? null : (
              <span key={item.label} className="px-3 py-1 text-xs text-gray-400 select-none">
                {item.label}
              </span>
            )
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm transition-colors truncate ${
                  isActive
                    ? "bg-gray-100 font-medium text-gray-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              {collapsed ? item.label.slice(0, 2) : item.label}
            </NavLink>
          )
        )}
      </nav>
    </aside>
  );
}
```

---

### Bloco H — Docs: Manual de Operação e QA Checklist

- [ ] **H1.** Criar `docs/manual-operacao.md` — fluxo abrir→fechar comanda (1 página):

  Conteúdo mínimo:
  1. Login (`/login`)
  2. Abrir nova comanda (Comandas → Nova Comanda → mesa/número/garçom → Abrir)
  3. Lançar itens (selecionar item na comanda aberta → qtd → Lançar)
  4. Aplicar desconto ou cortesia (botões na comanda)
  5. Fechar comanda (Fechar → selecionar métodos de pagamento → Confirmar)
  6. Ver comprovante / imprimir
  7. Backup (Configurações → Backup → Exportar JSON ou Excel)

- [ ] **H2.** Criar `docs/qa-checklist.md` — checklist de smoke test visual.

  Conteúdo:
  - Resolução 1280×720: verificar cada tela principal (Dashboard, Comandas, Comanda Aberta, Fechamento, Estoque, Relatórios, Cadastros, Configurações) sem scroll horizontal, sem clipping de texto.
  - Resolução 1366×768: idem.
  - Sidebar colapsa automaticamente em 1366px.
  - Botões: altura `h-10`, espaçamento `p-3`.
  - Loading states: skeleton em tabelas/listas antes de dados carregarem.
  - Empty states: mensagem amigável quando lista vazia.
  - Toasts: sucesso some em ~2.5s, erro persiste, aviso some em ~4.5s.
  - ConfirmDialog aparece para: excluir item, excluir categoria, excluir fornecedor, reabrir comanda.

---

## Validações

### Frontend
```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

### Critérios de Aceite
- [ ] `window.confirm` removido de ItensPage, CategoriasPage, FornecedoresPage.
- [ ] ConfirmDialog usado para excluir item, categoria, fornecedor, reabrir comanda.
- [ ] `toast.error` persistente, `toast.success` 2.5s, `toast.warning` 4.5s.
- [ ] Sentry ErrorBoundary envolve App.
- [ ] `unhandledrejection` capturado no initSentry.
- [ ] Respostas 500 capturadas em api.ts.
- [ ] Sidebar colapsa em ≤1366px por padrão.
- [ ] ComandaAbertaPage e ComprovantePage têm skeleton de loading.
- [ ] `npm run build` PASS.
- [ ] `npm run type-check` PASS.
- [ ] Manual de operação criado em `docs/manual-operacao.md`.
- [ ] QA checklist criado em `docs/qa-checklist.md`.

---

## Notas Importantes

- Backend Sentry já implementado — não modificar.
- `@sentry/react` já está em `package.json` (referenciado em `sentry.ts`) — não reinstalar.
- PlaceholderPage usa `toast` de sonner para demo — atualizar para `@/lib/toast` também.
- GarconsPage não tem botão de excluir (soft delete via edit) — sem ConfirmDialog necessário.
- MetodosPagamentoPage: verificar se tem delete com window.confirm — se sim, adicionar ConfirmDialog.
- `CancelarItemModal`, `BaixaSemVendaModal`, `AplicarDescontoModal`: são formulários, não confirms simples — manter como estão.
- Cortesia: é um checkbox dentro do form de lançar item, não uma ação destrutiva independente — manter como está.
