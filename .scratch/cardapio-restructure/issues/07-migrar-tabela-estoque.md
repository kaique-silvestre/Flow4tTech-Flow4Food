# 07: Migrar tabela de Estoque

**What to build:** `EstoquePage.tsx` usa `components/ui/table.tsx` em vez de `<table>` cru, com o mesmo alinhamento e hover já adotados no Cardápio — as duas telas ficam visualmente idênticas em estrutura.

**Blocked by:** 01 (Componente Table + migrar tabela do Cardápio)

**Touches:** `frontend/src/features/estoque/EstoquePage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] `EstoquePage.tsx` usa `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Colunas `Estoque atual`/`Reservado`/`Disponível`/`Custo médio`/`Valor em estoque` alinhadas à direita (hoje alinhadas à esquerda, exceto a última)
- [x] Colunas `Item`/`Categoria` continuam à esquerda
- [x] Linha destacada em laranja (`bg-orange-50`) para item crítico preservada
- [x] Valores negativos em vermelho preservados
- [x] Hover de linha (herdado do `TableRow` padrão) presente
- [x] Filtro de categoria e busca por item continuam funcionando sem regressão
