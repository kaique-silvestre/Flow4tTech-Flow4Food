# 05: Migrar tabela do GarcomComissoesModal

**What to build:** A tabela dentro de `GarcomComissoesModal.tsx` (Comanda/Data/Valor/Status) usa `components/ui/table.tsx`, com a coluna "Valor" alinhada à direita.

**Blocked by:** Ticket 01 da spec `.scratch/cardapio-restructure/` (Componente Table)

**Touches:** `frontend/src/features/cadastros/garcons/GarcomComissoesModal.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Tabela usa `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Coluna "Valor" alinhada à direita; "Comanda"/"Data"/"Status" continuam à esquerda
- [x] Comportamento e dados exibidos idênticos aos de hoje — só a estrutura de marcação muda
