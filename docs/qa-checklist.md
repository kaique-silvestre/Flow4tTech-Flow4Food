# QA Checklist — Smoke Test Visual

**Resoluções alvo:** 1280×720 e 1366×768

---

## Checklist Geral (todas as telas)

- [ ] Sem scroll horizontal em nenhuma tela
- [ ] Sem clipping de texto em títulos, labels, botões
- [ ] Sidebar colapsa automaticamente ao abrir em 1366px
- [ ] Botão de toggle da sidebar (‹/›) funciona
- [ ] Sidebar expandida: labels completos visíveis
- [ ] Sidebar colapsada: abreviações visíveis, tooltip no hover
- [ ] Loading skeleton aparece antes dos dados carregarem
- [ ] Empty state com mensagem amigável quando lista vazia

---

## Telas Principais

### Dashboard (`/`)
- [ ] 4 cards de indicadores sem overlap
- [ ] 2 gráficos (Recharts) renderizando sem erro
- [ ] Lista de comandas abertas visível
- [ ] Skeleton de loading antes dos dados

### Comandas (`/comandas`)
- [ ] Lista de comandas com status correto
- [ ] Botão "Nova Comanda" acessível
- [ ] Empty state quando sem comandas

### Comanda Aberta (`/comandas/:id`)
- [ ] Skeleton de loading substituiu "Carregando..."
- [ ] Campo de busca de itens funcional
- [ ] Top itens frequentes visíveis
- [ ] Lançar item funciona com toast sucesso (some em ~2.5s)
- [ ] ConfirmDialog ao reabrir comanda fechada (botão destrutivo vermelho)
- [ ] CancelarItemModal abre corretamente

### Fechamento (`/comandas/:id/fechar`)
- [ ] Formulário de pagamento sem clipping
- [ ] Divisão por pessoa funcional
- [ ] Toast de aviso estoque negativo (some em ~4.5s)

### Comprovante (`/comprovante/:id`)
- [ ] Skeleton de loading substituiu "Carregando comprovante..."
- [ ] Layout de impressão correto (sem elementos de UI)
- [ ] Botão imprimir funcional

### Estoque (`/estoque`)
- [ ] Tabela de saldos sem overflow
- [ ] BaixaSemVendaModal abre (ação destrutiva — form, não ConfirmDialog)

### Relatórios
- [ ] Cada relatório carrega sem erro de layout
- [ ] Tabelas com scroll vertical se muitas linhas (sem horizontal)

### Cadastros
- [ ] **Itens** (`/cadastros/itens`): ConfirmDialog ao clicar Remover (botão destrutivo vermelho)
- [ ] **Categorias** (`/cadastros/categorias`): ConfirmDialog ao clicar Remover
- [ ] **Fornecedores** (`/cadastros/fornecedores`): ConfirmDialog ao clicar Remover
- [ ] **Garçons**: sem botão remover (soft delete via edit)
- [ ] **Métodos Pagamento**: sem botão remover

### Configurações (`/configuracoes`)
- [ ] 4 abas funcionais: Estabelecimento, Senha, Impressora, Backup
- [ ] Form Estabelecimento preenche com dados atuais
- [ ] Toast sucesso ao salvar (some em ~2.5s)
- [ ] Toast erro ao senha incorreta (persiste até fechar)
- [ ] Botões de backup baixam arquivos

---

## Toasts (verificar durações)

| Tipo | Cor | Duração esperada |
|------|-----|-----------------|
| Sucesso | Verde | ~2.5s (some sozinho) |
| Erro | Vermelho | Persistente (requer X para fechar) |
| Aviso | Amarelo | ~4.5s (some sozinho) |

---

## Densidade Visual

- [ ] Botões com altura adequada (não muito pequenos em 720p)
- [ ] Padding interno das páginas adequado
- [ ] Texto legível sem zoom em 1280×720

---

## Sentry (verificar em dev console)

- [ ] Sem erros de render no console (ErrorBoundary não disparou)
- [ ] `window.onerror` / `unhandledrejection` não disparam para fluxos normais
