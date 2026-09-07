# 02: Badge de status Ativo/Inativo em Cardápio

**What to build:** `CardapioPage.tsx` ganha uma coluna/indicador de status usando `<Badge variant="outline">` (verde "Ativo"/cinza "Inativo"), igual às demais telas de Cadastros (Insumos, Fornecedores, Garçons, Métodos de Pagamento). Hoje a lista só tacha o nome do produto inativo (`line-through`), sem badge nenhum.

**Blocked by:** None (can start immediately)

**Touches:** `frontend/src/features/cardapio/CardapioPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [ ] Nova coluna "Status" (ou badge inline perto do nome, seguir o padrão mais próximo do que já existe em `InsumosPage.tsx`) usando `<Badge variant="outline" className="border-green-200 bg-green-100 text-green-700">Ativo</Badge>` / `<Badge variant="outline" className="border-gray-200 bg-gray-100 text-gray-500">Inativo</Badge>` — mesmas classes usadas em Insumos/Fornecedores/Métodos de Pagamento (copiar exatamente, não reinventar cor)
- [ ] Nome do produto inativo mantém `line-through`, sem `opacity` extra (comportamento já existente preservado)
- [ ] Badge aparece nos filtros "Inativos" e "Todos"; no filtro "Ativos" todo mundo mostra Badge "Ativo" (comportamento redundante mas consistente com as outras telas, que fazem o mesmo)
- [ ] Nenhuma regressão em busca, filtro de categoria, paginação, clique na linha, botão Desativar/Reativar
