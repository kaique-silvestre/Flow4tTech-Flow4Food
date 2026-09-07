# 03: DropdownMenu em Insumos e Fornecedores (ações por linha)

**What to build:** `InsumosPage.tsx` e `FornecedoresPage.tsx` trocam os dois botões soltos por linha ("Editar" + "Desativar"/"Ativar") por um único `DropdownMenu`, mesmo padrão já usado em `GarconsPage.tsx` (commit `f7b9a7e`) e `GestaoUsuariosPage.tsx` (commit `10e1851`).

**Blocked by:** None (can start immediately) — `components/ui/dropdown-menu.tsx` já existe

**Touches:** `frontend/src/features/cadastros/insumos/InsumosPage.tsx`, `frontend/src/features/cadastros/fornecedores/FornecedoresPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [ ] Linha de Insumo tem um único `DropdownMenu` com itens "Editar" e "Desativar"/"Ativar" (rótulo conforme status atual)
- [ ] Linha de Fornecedor tem um único `DropdownMenu` com os mesmos dois itens
- [ ] Nenhum item novo adicionado além dos dois que já existem hoje como botões
- [ ] Todas as ações continuam disparando exatamente o mesmo comportamento de antes (mutations, modais de edição)
- [ ] Badge de status e busca normalizada (já existentes nessas duas telas) continuam funcionando sem regressão
- [ ] Reusar o padrão de teste RTL com polyfill de `PointerEvent` para jsdom+Radix DropdownMenu já estabelecido em `GarconsPage.test.tsx`
