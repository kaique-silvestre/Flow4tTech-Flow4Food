# 01: Componente Table + migrar tabela do Cardápio

**What to build:** Um componente de tabela reutilizável estilo shadcn (`Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`, `TableFooter`, `TableCaption`) em `components/ui/table.tsx`, e `CardapioPage.tsx` passa a usá-lo no lugar do `<table>` cru atual — colunas numéricas (Preço, Custo Ficha, CMV%, Lucro Bruto, Produção) alinhadas à direita, colunas de texto à esquerda, hover de linha (`hover:bg-gray-50`) como estilo padrão do `TableRow`. O chevron de expandir ficha técnica inline e o botão "Editar" continuam funcionando exatamente como hoje — não são removidos aqui (saem no ticket 06, quando a página de produto existir pra substituí-los).

**Blocked by:** None (can start immediately)

**Touches:** `components/ui/table.tsx` (novo), `frontend/src/features/cardapio/CardapioPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] `components/ui/table.tsx` existe com os componentes `Table`/`TableHeader`/`TableBody`/`TableFooter`/`TableRow`/`TableHead`/`TableCell`/`TableCaption`, via `React.forwardRef` + `cn()` de `@/lib/utils` (mesmo padrão dos outros componentes de `components/ui/`)
- [x] Nenhuma dependência nova instalada (sem MUI/`@mui/x-data-grid`/TanStack Table)
- [x] `CardapioPage.tsx` usa os novos componentes em vez de `<table>` cru
- [x] Colunas Preço, Custo Ficha, CMV%, Lucro Bruto, Produção alinhadas à direita; Nome e Categoria à esquerda
- [x] Linha ganha destaque visual ao passar o mouse (`hover:bg-gray-50` no `TableRow`)
- [x] Chevron de expandir ficha técnica inline continua funcionando (sem regressão)
- [x] Botão "Editar" continua abrindo o modal de edição (sem regressão)
- [x] Botões "Desativar"/"Reativar" continuam funcionando (sem regressão)
- [x] Paginação, filtro de status e busca por nome continuam funcionando (sem regressão)
