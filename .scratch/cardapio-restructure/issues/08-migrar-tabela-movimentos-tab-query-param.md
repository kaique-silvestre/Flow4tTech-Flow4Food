# 08: Migrar tabela de Movimentos + aba via query param

**What to build:** `MovimentosPage.tsx` (as duas abas, Insumos e Produtos) usa `components/ui/table.tsx` com o mesmo alinhamento/hover das outras telas já padronizadas, e a aba ativa passa a ser um query param (`?tab=insumos` | `?tab=produtos`) em vez de `useState` local — endereçável, compartilhável, e o botão voltar do navegador desfaz a troca de aba.

**Blocked by:** 01 (Componente Table + migrar tabela do Cardápio)

**Touches:** `frontend/src/features/estoque/MovimentosPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Ambas as tabelas (aba Insumos, aba Produtos) usam `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Aba Insumos: colunas `Quantidade`/`Saldo após` alinhadas à direita (hoje à esquerda, exceto a última)
- [x] Aba Produtos: colunas `Qtd`/`Preço unit.`/`Subtotal` alinhadas à direita (hoje à esquerda, exceto a última)
- [x] Badges de tipo coloridos (`TIPO_BADGE`) preservados na aba Insumos
- [x] Cor verde/vermelho por entrada/saída preservada
- [x] Linha riscada (`line-through`) para movimento cancelado preservada na aba Produtos
- [x] Aba ativa lida de `useSearchParams` (`?tab=insumos` default, `?tab=produtos`), trocar de aba chama `setSearchParams`
- [x] Abrir a URL `/estoque/movimentos?tab=produtos` diretamente já carrega na aba Produtos
- [x] Botão voltar do navegador desfaz a troca de aba
- [x] Filtros internos de cada aba (item/produto, tipo, datas) continuam como estado local — não entram na URL
- [x] Breadcrumb "Estoque > Movimentos" continua funcionando sem alteração
