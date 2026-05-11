
# Issues — Matchpoint Ajustes e Melhorias v0.3

> Gerado a partir de `docs/prds/prd_matchpoint_v0.3.md`.
> Ordem de criação respeita dependências (blockers primeiro).

---

## Issue 1 — DB2: Debounce 350ms em inputs de busca ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar a dependência `use-debounce` no frontend e aplicar `useDebounce(busca, 350)` em todos os inputs de busca que disparam queries à API.

**Aplicar em:**
- `ComandasPage` — busca em `useComandas(busca)`
- `ComandaAbertaPage` — busca em `useProdutos(busca)`
- `EstoquePage` — `filters.busca` em `useSaldoEstoque`
- `HistoricoComandasPage` — `busca` em `useHistoricoComandas`

Padrão de uso:
```ts
import { useDebounce } from "use-debounce";
const [busca, setBusca] = useState("");
const [debouncedBusca] = useDebounce(busca, 350);
// usa debouncedBusca no hook de query
```

### Critérios de aceite

- [x] `npm install use-debounce` registrado em `package.json`
- [x] Digitar 8 letras consecutivas em `ComandasPage` → única request disparada (verificar via DevTools)
- [x] Após 350ms sem digitar, request é disparada
- [x] Buscas em todas as páginas listadas usam o mesmo padrão `useDebounce`
- [x] Limpar o input dispara nova query imediata com valor vazio (sem esperar debounce)

### User stories endereçadas

- US1: Como operador, quero que minha busca dispare uma única vez ao terminar de digitar, para resposta rápida e sem flicker.
- US2: Como sistema, quero reduzir chamadas redundantes à API, para escalabilidade.

---

## Issue 2 — CM1: Remoção de código morto `ItensPage` ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Deletar arquivos legados que não estão registrados em rotas do `App.tsx` nem no `Sidebar`. São remanescentes da época anterior à separação Insumo/Produto (PRD v0.1 M000).

**Arquivos a excluir:**
- `frontend/src/features/cadastros/itens/ItensPage.tsx`
- `frontend/src/features/cadastros/itens/ItemModal.tsx`
- `frontend/src/features/cadastros/itens/itemSchemas.ts`
- Qualquer `useItens.ts` no mesmo diretório (verificar)

**Validação:** após exclusão, rodar `grep` no projeto para garantir que nada importa de `features/cadastros/itens`.

### Critérios de aceite

- [x] Os 3 arquivos excluídos do repositório
- [x] `npm run build` no frontend passa sem erro
- [x] `npm run type-check` passa sem erro
- [x] `grep -r "cadastros/itens" frontend/src` retorna vazio
- [x] Pasta `frontend/src/features/cadastros/itens` excluída (se ficar vazia)

### User stories endereçadas

- US1: Como desenvolvedor, quero remover código morto, para reduzir confusão e tempo de manutenção.

---

## Issue 3 — EM1: `reset()` consistente em `InsumoEditModal` ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Remover a chamada `reset()` sem argumentos do `handleClose` em `InsumoEditModal.tsx`. O `useEffect([open, editing, reset])` já cuida de reinicializar os campos quando o modal reabre com novo `editing`. A chamada extra causa flash de campos vazios.

### Critérios de aceite

- [x] `handleClose` não chama `reset()` — apenas `onClose()`
- [x] Editar insumo A → fechar → editar insumo B → campos preenchem direto com dados de B sem flash
- [x] Criar novo insumo → fechar → criar outro → campos limpos (`useEffect` cuida)
- [x] Nenhum outro comportamento alterado

### User stories endereçadas

- US2: Como operador, quero abrir o modal de edição de insumo sem ver campos vazios brevemente, para fluxo visual limpo.

---

## Issue 4 — MOD1 + NC1 + NC2: `NovaComandaModal` migrado para `Dialog` + fixes ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Três alterações no mesmo arquivo `NovaComandaModal.tsx`:

**MOD1 — Dialog padronizado:** trocar wrapper `<div className="fixed inset-0...">` por `<Dialog>`, `<DialogContent>`, `<DialogHeader>`, `<DialogTitle>`, `<DialogFooter>`.

**NC1 — `valueAsNumber` no campo de mesa:** quando `tipo_identificacao === "mesa"`, registrar `identificacao` com `valueAsNumber: true` para que o backend receba inteiro em vez de string.

**NC2 — Acessibilidade dos radios:** adicionar `id` único em cada `<input type="radio">` de `tipo_identificacao` e `htmlFor` correspondente no `<label>`.

### Critérios de aceite

- [x] Modal abre via `<Dialog>` — fecha com Esc, fecha com clique fora, foco aprisionado
- [x] Selecionar "mesa", digitar "5", abrir → GET retorna `identificacao` como número 5 (não string "5")
- [x] Selecionar "nome", digitar "Pedro", abrir → GET retorna `identificacao` como string "Pedro"
- [x] Radios `tipo_identificacao` têm `id` e labels conectados via `htmlFor`
- [x] Navegação por Tab acessa cada radio individualmente
- [x] DevTools "Inspect Accessibility" mostra cada radio com label associado

### User stories endereçadas

- US1: Como sistema, quero receber o número da mesa como inteiro do frontend, para validações numéricas funcionarem corretamente.
- US2: Como operador com leitor de tela, quero que o foco do radio de tipo de identificação esteja conectado ao label.
- US3: Como operador, quero fechar qualquer modal pressionando Esc ou clicando fora.

---

## Issue 5 — MOD1b: `CancelarItemModal` migrado para `Dialog` ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Substituir o wrapper `<div className="fixed inset-0...">` em `CancelarItemModal.tsx` por `<Dialog>` padrão. Mover botões de ação para `<DialogFooter>`.

### Critérios de aceite

- [x] Modal usa `<Dialog>` com `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogFooter`
- [x] Esc fecha o modal
- [x] Clique fora fecha o modal
- [x] Foco automático no primeiro elemento interativo
- [x] Comportamento de cancelamento de item inalterado

### User stories endereçadas

- US1: Como operador, quero fechar qualquer modal pressionando Esc ou clicando fora, para fluxo rápido durante o atendimento.

---

## Issue 6 — FE2: `modo_divisao` via `Controller` no fechamento ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Substituir radio inputs com `setValue` manual de `modo_divisao` em `FechamentoPage.tsx` por `<Controller>` do RHF, garantindo que o valor selecionado seja sempre persistido no submit (mesma classe de bug BG1/BG2).

### Critérios de aceite

- [x] Cada um dos 4 modos (`sem_divisao`, `igualmente`, `por_pessoa`, `parcial`) selecionado e submetido — payload contém o `modo_divisao` correto
- [x] Mudança de modo dispara atualização do valor do pagamento default (`baseTotal` para sem_divisao, `0` para outros) como hoje
- [x] Radios visualmente refletem o valor atual sem desalinhamento
- [x] `setValue("modo_divisao", ...)` direto removido — apenas `field.onChange` via `Controller`

### User stories endereçadas

- US1: Como caixa, quero que o modo de divisão selecionado seja sempre persistido corretamente no submit, para o cálculo refletir minha escolha.

---

## Issue 7 — FE4: Schema de pagamentos coerente com Z1 (total R$0) ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Alterar `fecharComandaSchema.pagamentos` removendo `.min(1)` para que aceite array vazio. Adicionar validação manual no submit handler: quando `baseTotal > 0`, o array deve ter pelo menos 1 pagamento.

### Critérios de aceite

- [x] Schema permite `pagamentos: []`
- [x] Comanda com total R$0 → confirma fechamento sem método → backend recebe `pagamentos: []`
- [x] Comanda com total > 0 sem nenhum pagamento → submit bloqueado com mensagem clara
- [x] Caminho `baseTotal === 0` continua funcionando como hoje
- [x] Nenhuma regressão em fluxos com 1 ou múltiplos pagamentos

### User stories endereçadas

- US1: Como sistema, quero schemas coerentes com os fluxos suportados, para evitar bugs futuros.

---

## Issue 8 — DE1 + DE2: Fixes em `AplicarDescontoModal` ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

**DE1 — `onOpenChange` correto:** substituir `onOpenChange={onClose}` por `onOpenChange={(v) => !v && onClose()}` para evitar chamada de `onClose` ao abrir o modal.

**DE2 — Radio "percentual / valor" via Controller:** substituir radio inputs com `setValue` manual por `<Controller>` do RHF.

### Critérios de aceite

- [x] Abrir modal de desconto → modal permanece aberto (não fecha sozinho)
- [x] Trocar entre "Percentual (%)" e "Valor fixo (R$)" → submeter → payload contém o `tipo` correto
- [x] Esc continua fechando o modal
- [x] Aplicar desconto percentual de 10% → comanda passa a refletir desconto
- [x] Aplicar desconto em valor de R$5 → comanda passa a refletir desconto

### User stories endereçadas

- US1: Como sócio, quero abrir o modal de desconto sem que ele tente fechar sozinho, para aplicar desconto sem perder o input.
- US2: Como sócio, quero que a escolha entre desconto percentual ou em valor seja sempre persistida.

---

## Issue 9 — FE1 + CV1: `formatQuantidade` no Fechamento e no Comprovante ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Aplicar `formatQuantidade(item.quantidade)` no resumo de itens em `FechamentoPage.tsx` e no comprovante em `ComprovantePage.tsx`. Decimais devem aparecer com vírgula (padrão pt-BR).

### Critérios de aceite

- [x] Lançar item com qtd 1.5 → resumo em fechamento exibe "1,5×" (vírgula)
- [x] Mesmo item no comprovante impresso exibe "1,5x" (vírgula)
- [x] Item com qtd inteira 3 exibe "3×" sem casas decimais
- [x] Comportamento idêntico ao já existente em `ComandaAbertaPage`

### User stories endereçadas

- US1: Como caixa, quero ver "1,5×" em vez de "1.5×" para quantidades fracionárias no resumo do fechamento.
- US2: Como cliente, quero ver "1,5×" em vez de "1.5×" no comprovante impresso, para legibilidade no padrão brasileiro.

---

## Issue 10 — FE3: Label "Última pessoa paga" no modo igualitário ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `FechamentoPage.tsx`, no bloco de divisão igualitária, substituir o label "1ª pessoa paga:" por "Última pessoa paga:". O cálculo (N-1 pessoas pagam o valor base, 1 pessoa absorve a sobra) permanece igual — apenas o label muda.

### Critérios de aceite

- [x] Modo "igualmente" com 3 pessoas, total R$10 → exibe "2 pessoas pagam: R$3,33 cada" e "Última pessoa paga: R$3,34"
- [x] Total ainda bate (`R$10,00`)
- [x] Cálculo inalterado em todos os outros aspectos

### User stories endereçadas

- US1: Como caixa, quero que o label do valor diferente seja "Última pessoa", para entender corretamente quem paga a sobra do arredondamento.

---

## Issue 11 — CA1: Select de pessoa no modo edição de item ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `ComandaAbertaPage.tsx`, quando um item lançado entra em modo de edição inline, trocar o `<Input>` de texto livre do campo "pessoa" por um `<select>` populado com `comanda.pessoas` — quando existirem pessoas cadastradas. Se a comanda não tem pessoas, manter o input de texto.

### Critérios de aceite

- [x] Comanda com pessoas ["Ana", "Bruno"] → editar item → campo pessoa é `<select>` com "Ana", "Bruno", "— nenhuma —"
- [x] Comanda sem pessoas → editar item → campo pessoa é `<input>` texto livre (comportamento atual)
- [x] Selecionar pessoa no select → salvar → GET confirma persistência
- [x] Selecionar "— nenhuma —" → campo `pessoa_associada` salvo como vazio/null

### User stories endereçadas

- US1: Como operador, quero selecionar a pessoa de um item já lançado via lista de pessoas da comanda, para não digitar o nome incorretamente.

---

## Issue 12 — CA2: Recalcular "Aberta há X min" no frontend ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Calcular `tempo_aberta_minutos` no frontend a partir de `comanda.created_at`, atualizando a cada 60 segundos via `setInterval`. Aplicar em `ComandaAbertaPage.tsx` e em `ComandasPage.tsx` (lista/cards).

### Critérios de aceite

- [x] Abrir comanda → aguardar 1 minuto sem refresh → contador "Aberta há X min" incrementa
- [x] Comanda fechada não dispara o interval (cleanup correto)
- [x] Lista de comandas em `ComandasPage` atualiza igualmente
- [x] `setInterval` é limpo no `useEffect` cleanup ao desmontar componente

### User stories endereçadas

- US1: Como operador, quero ver o tempo atualizado de uma comanda aberta, mesmo sem recarregar a tela.

---

## Issue 13 — MV1 + MV2: Tipo `ESTORNO_COMPRA` + ano na data de Movimentos ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `MovimentosPage.tsx`:

**MV1:** adicionar `estorno_compra` em `TIPO_OPTIONS`, `TIPO_BADGE` e `TIPO_LABEL`.

**MV2:** adicionar `year: "2-digit"` ao `toLocaleString` da coluna de data, exibindo no formato `dd/mm/yy HH:MM`.

### Critérios de aceite

- [x] Cancelar uma compra → movimentação `estorno_compra` aparece com badge cinza e label "Estorno compra"
- [x] Filtro "Estorno compra" disponível no seletor de tipo
- [x] Coluna data exibe ano (ex: "11/05/26 14:30")
- [x] Outros tipos de movimento permanecem com badges e labels inalterados

### User stories endereçadas

- US1: Como sócio, quero ver claramente quais movimentos são estornos de compra cancelada.
- US2: Como sócio, quero filtrar apenas movimentos de estorno.
- US3: Como sócio, quero ver o ano da movimentação, para distinguir registros antigos de recentes.

---

## Issue 14 — CP4: `total_periodo` real no backend e exibição correta ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar campo `total_periodo: Decimal` ao `ComprasPageResponse` no backend, calculado via `SUM(total)` sobre todos os filtros (sem paginação). Frontend substitui o cálculo local pelo valor do response.

### Critérios de aceite

- [x] `GET /api/compras?pagina=1&por_pagina=10` retorna `total_periodo` com soma de todas as compras do filtro
- [x] Criar 25 compras de R$10 → filtrar tudo → UI exibe "Total no período: R$250,00" em qualquer página
- [x] Filtro por fornecedor → `total_periodo` recalcula corretamente
- [x] Filtro por data → `total_periodo` recalcula corretamente
- [x] Frontend não soma mais via `compras.reduce(...)`

### User stories endereçadas

- US1: Como sócio, quero ver o total real do período filtrado de compras, para conferir gastos com fornecedores sem somar manualmente página por página.

---

## Issue 15 — CP5: Filtro de status (Todas / Ativas / Canceladas) em compras ✅ Concluída

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar filtro de status à listagem de compras com 3 opções (Todas / Ativas / Canceladas), default "Ativas". Backend aceita parâmetro `status: Optional[str]`.

### Critérios de aceite

- [x] Toggle de 3 botões aparece no topo da listagem (padrão visual de `InsumosPage`)
- [x] Default selecionado é "Ativas"
- [x] Cancelar 3 de 5 compras → filtrar "Ativas" → 2 resultados. "Canceladas" → 3. "Todas" → 5
- [x] Backend retorna lista filtrada respeitando o parâmetro
- [x] Mudança de filtro reseta paginação para 1

### User stories endereçadas

- US1: Como sócio, quero filtrar a listagem de compras por status, para focar apenas em notas ativas ou auditar canceladas.

---

## Issue 16 — CP6: Modal de edição de compra com `Dialog` padronizado

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Substituir o JSX inline `<div className="fixed inset-0 z-50...">` do modal de edição em `ComprasPage.tsx` pelo componente `<Dialog>` padrão.

### Critérios de aceite

- [ ] Modal de edição usa `<Dialog>` com `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogFooter`
- [ ] Esc fecha o modal
- [ ] Clique fora fecha o modal
- [ ] Foco no primeiro campo ao abrir
- [ ] Salvar e cancelar continuam funcionando

### User stories endereçadas

- US1: Como sistema, quero modais com aparência consistente em todo o sistema, para evitar variação visual confusa.

---

## Issue 17 — CP7: Toast amarelo após cancelamento de compra

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `useCompras.ts → useCancelarCompra → onSuccess`, disparar `toast.warning("Nota cancelada. Verifique o custo médio dos insumos afetados.")` com persistência de 5 segundos.

### Critérios de aceite

- [ ] Cancelar uma nota com 2 ou mais insumos → toast amarelo aparece após sucesso
- [ ] Toast persiste por ~5 segundos antes de desaparecer
- [ ] Texto exatamente como especificado
- [ ] Nenhuma regressão no estorno de estoque já implementado em CP1 v0.2

### User stories endereçadas

- US1: Como sócio, quero um aviso após cancelar uma nota lembrando que o custo médio dos insumos pode ter ficado impreciso.

---

## Issue 18 — CP8: Reset de linha ao trocar item selecionado

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `NovaCompraPage.tsx`, no `onChange` do `<select>` de `item_id`, zerar quantidade, custo unitário (`unitarios[index]`) e custo total da linha. Limpar também a entrada de `lastEditedRef.current[index]`.

### Critérios de aceite

- [ ] Linha 1 com item A, qtd 5, custo unit R$10, total R$50 → trocar para item B → todos os 3 campos zerados
- [ ] Outras linhas não são afetadas
- [ ] Adicionar nova linha após troca não é prejudicado
- [ ] Comportamento normal (digitação inicial) preservado

### User stories endereçadas

- US1: Como operador, quero que a linha da compra seja zerada ao trocar o item selecionado, para não salvar valores do item anterior por engano.

---

## Issue 19 — CP9: Precisão do `custo_unitario` em 4 casas decimais

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `compras_service.criar_compra` (backend), arredondar o `custo_unitario` calculado para 4 casas decimais antes de persistir:

```python
custo_unitario = (item_req.custo_total / item_req.quantidade).quantize(Decimal("0.0001"))
```

### Critérios de aceite

- [ ] Registrar compra de 3 unidades a R$10 → `custo_unitario` salvo como `3.3333` (não `3.333333333...`)
- [ ] Compra com quantidades inteiras e custo divisível → `custo_unitario` sem casas extras desnecessárias
- [ ] Relatórios que consomem `custo_unitario` não quebram
- [ ] Nenhuma regressão em CMV ou custo médio

### User stories endereçadas

- US1: Como sistema, quero arredondar o custo unitário a uma precisão suficiente sem introduzir dízimas longas no banco.

---

## Issue 20 — CP10: Warning amarelo para `numero_nota` duplicado

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Backend `compras_service.criar_compra`: antes de persistir, verificar se já existe outra compra com mesmo `numero_nota` (quando informado). Se sim, incluir campo opcional `warning: Optional[str]` no `CompraResponse` com a mensagem `"Número de nota já registrado na compra #0042"`. **Não bloquear** o cadastro.

Frontend `useCompras.ts → useCreateCompra → onSuccess`: se `data.warning`, disparar `toast.warning(data.warning)`.

### Critérios de aceite

- [ ] Cadastrar compra com `numero_nota = "X1"` → sem warning, salva normalmente
- [ ] Cadastrar segunda compra com `numero_nota = "X1"` → response inclui `warning` com mensagem padronizada
- [ ] Frontend exibe toast amarelo com a mensagem
- [ ] Compra é salva mesmo com duplicidade
- [ ] Cadastrar compra sem `numero_nota` → nenhum warning

### User stories endereçadas

- US1: Como sócio, quero ser avisado quando estou cadastrando uma nota com número que já existe, para verificar se não é duplicata sem bloquear o cadastro legítimo.

---

## Issue 21 — CP11: Transação atômica em `criar_compra` e `cancelar_compra`

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Envolver `criar_compra` e `cancelar_compra` em `compras_service.py` em bloco `try/except` com `db.rollback()` em caso de erro. Garante atomicidade: se falhar no meio do loop de itens, nenhuma alteração de estoque persiste.

### Critérios de aceite

- [ ] Simular exceção na 2ª iteração do loop de `criar_compra` → estoque do 1º insumo não foi alterado no banco
- [ ] Mesmo cenário em `cancelar_compra` → estorno parcial revertido
- [ ] Caso feliz (sem exceção) continua funcionando idêntico
- [ ] Logs/Sentry capturam a exceção original (não suprimir)

### User stories endereçadas

- US1: Como sistema, quero que falhas no meio do registro de compra não deixem o estoque parcialmente alterado, para garantir consistência dos dados.

---

## Issue 22 — AR1 + AR2: Histórico unificado em Relatórios

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

**AR1:** remover `/historico` (`HistoricoPage`) do `Sidebar` e do roteamento em `App.tsx`. Excluir o arquivo `HistoricoPage.tsx`.

**AR2:** tornar as linhas da tabela em `HistoricoComandasPage` (`/relatorios/historico`) clicáveis, navegando para `/comandas/:id`.

### Critérios de aceite

- [ ] Item "Histórico" não aparece mais no `Sidebar`
- [ ] Rota `/historico` removida do `App.tsx`
- [ ] Arquivo `HistoricoPage.tsx` excluído
- [ ] `npm run build` passa sem erros
- [ ] Em `/relatorios/historico`, clicar em qualquer linha de comanda navega para `/comandas/:id`
- [ ] Hover em linha mostra cursor `pointer` e fundo cinza

### User stories endereçadas

- US1: Como sócio, quero um único lugar para consultar histórico de comandas fechadas, para não me confundir com duas telas parecidas.
- US2: Como sócio, quero clicar em uma comanda no histórico para abrir seu detalhe.

---

## Issue 23 — CD1 + CD2: Cardápio com filtro ativo/inativo + Reativar + busca

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

**CD1 — Filtro + Reativar:** adicionar toggle de filtro (Todos / Ativos / Inativos) com default "Ativos" em `CardapioPage.tsx`. Botão da linha exibe "Desativar" quando ativo e "Reativar" quando inativo.

**CD2 — Busca:** adicionar input de busca por nome no topo da página, filtragem client-side combinada com o filtro de status.

**Backend:** se necessário, adicionar endpoint de reativação de produto ou reutilizar update genérico passando `ativo: true`.

### Critérios de aceite

- [ ] Toggle de 3 botões (Todos / Ativos / Inativos) com default "Ativos"
- [ ] Cadastrar 2 ativos e 1 inativo → filtrar "Ativos" → 2 resultados; "Inativos" → 1; "Todos" → 3
- [ ] Botão "Desativar" aparece em produto ativo; clicar desativa
- [ ] Botão "Reativar" aparece em produto inativo; clicar reativa
- [ ] Input de busca filtra produtos por substring case-insensitive do nome
- [ ] Filtro de status + busca podem ser combinados

### User stories endereçadas

- US1: Como sócio, quero ver apenas produtos ativos por padrão no cardápio.
- US2: Como sócio, quero alternar para inativos quando quiser reativar algum produto antigo.
- US3: Como sócio, quero reativar um produto desativado clicando "Reativar" diretamente na lista.
- US4: Como sócio, quero buscar produtos por nome rapidamente.

---

## Issue 24 — VD1 + VD2: VendasDoDia com seletor de data + rows clicáveis

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

**VD1 — Seletor de data:** adicionar input `<input type="date">` em `VendasDoDiaPage.tsx`, default = hoje. Hook `useVendasDoDia` aceita parâmetro `data?: string`. Backend aceita parâmetro `data` (verificar se já aceita; adicionar se não).

**VD2 — Rows clicáveis:** linhas da tabela de comandas navegam para `/comandas/:id` ao clicar.

### Critérios de aceite

- [ ] Seletor de data aparece no topo, default = hoje
- [ ] Trocar data para 1 dia anterior → totais e tabela atualizam com dados daquele dia
- [ ] Backend retorna dados do dia selecionado
- [ ] Clicar em linha de comanda na tabela navega para `/comandas/:id`
- [ ] Hover em linha mostra cursor `pointer` e fundo cinza

### User stories endereçadas

- US1: Como sócio, quero ver vendas de ontem ou de qualquer dia anterior, para comparar desempenho.
- US2: Como sócio, quero clicar na linha de uma comanda para abrir o detalhe, para revisar pedidos.

---

## Issue 25 — CG1: Toggle inline ativar/desativar em Garçons e Métodos de Pagamento

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar botão "Ativar" / "Desativar" diretamente na linha da tabela em `GarconsPage.tsx` e `MetodosPagamentoPage.tsx`. Hooks `useToggleGarcomAtivo` e `useToggleMetodoAtivo` chamam o endpoint genérico de update passando `{ ativo: !current }`.

### Critérios de aceite

- [ ] Cada linha de garçom tem botão "Ativar" (se inativo) ou "Desativar" (se ativo)
- [ ] Clicar alterna o status sem abrir modal — feedback imediato via invalidação de query
- [ ] Mesmo comportamento para métodos de pagamento
- [ ] Botão "Editar" permanece disponível ao lado
- [ ] Botão "Remover" em métodos permanece (PRD v0.2 MP1)

### User stories endereçadas

- US1: Como sócio, quero desativar um garçom diretamente da lista, sem precisar abrir o modal de edição.
- US2: Como sócio, quero o mesmo comportamento para métodos de pagamento.

---

## Issue 26 — DB1: Hooks de histórico montados só na aba ativa do Dashboard

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Garantir que `useDashboardHistorico` e `useDashboardResumoAnual` só sejam montados quando a aba "Histórico" do Dashboard está ativa. Verificar a estrutura atual e, se necessário, encapsular esses hooks dentro do componente `TabHistorico` (e não no `DashboardPage` raiz).

### Critérios de aceite

- [ ] Abrir Dashboard em aba "Resumo" → DevTools Network não mostra chamada a `/api/dashboard/historico` nem `/api/dashboard/resumo-anual`
- [ ] Trocar para aba "Histórico" → as duas chamadas ocorrem
- [ ] Voltar para "Resumo" → chamadas anteriores não se repetem
- [ ] Aba "Resumo" continua funcionando normalmente

### User stories endereçadas

- US1: Como sistema, quero evitar chamadas de API desnecessárias, para reduzir carga no backend.

---

## Issue 27 — SB1: Badge com contagem de comandas abertas no Sidebar

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar endpoint leve `GET /api/comandas/count-abertas` no backend retornando inteiro. Frontend `useComandasAbertasCount` em `useComandas.ts`. No `Sidebar.tsx`, renderizar badge âmbar ao lado de "Comandas" quando contagem > 0.

### Critérios de aceite

- [ ] Endpoint `GET /api/comandas/count-abertas` retorna inteiro
- [ ] Sem comandas abertas → nenhum badge no item "Comandas"
- [ ] Abrir 3 comandas → badge "3" aparece ao lado de "Comandas"
- [ ] Fechar todas → badge desaparece
- [ ] Badge atualiza após invalidação de cache de comandas
- [ ] Badge visível tanto no modo expandido quanto colapsado do Sidebar

### User stories endereçadas

- US1: Como operador, quero ver a contagem de comandas abertas direto no menu lateral, para saber rapidamente se há trabalho pendente.

---

## Issue 28 — ES1: Valor total em estoque

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `EstoquePage.tsx`, adicionar coluna "Valor em estoque" (saldo × custo_medio) na tabela e rodapé `<tfoot>` totalizando o valor de todos os itens visíveis (respeitando filtros aplicados).

### Critérios de aceite

- [ ] Nova coluna "Valor em estoque" exibida na tabela
- [ ] Item sem custo médio → mostra "—" na célula
- [ ] Rodapé soma corretamente os valores dos itens visíveis
- [ ] Aplicar filtro de categoria → totais recalculam apenas com itens filtrados
- [ ] Valor formatado em pt-BR com `formatCurrency`

### User stories endereçadas

- US1: Como sócio, quero ver o valor financeiro do estoque atual, para saber quanto capital está parado.

---

## Issue 29 — BK1: Nome do arquivo de backup com data

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `ConfiguracoesPage.tsx → TabBackup → download`, adicionar a data ISO no nome do arquivo baixado: `backup_YYYY-MM-DD.json` ou `backup_YYYY-MM-DD.xlsx`.

### Critérios de aceite

- [ ] Baixar backup JSON em 2026-05-11 → arquivo `backup_2026-05-11.json`
- [ ] Baixar backup Excel mesmo dia → arquivo `backup_2026-05-11.xlsx`
- [ ] Baixar 2 vezes no mesmo dia → navegador adiciona sufixo `(1)` automaticamente (não sobrescreve)
- [ ] Conteúdo do backup inalterado

### User stories endereçadas

- US1: Como sócio, quero baixar vários backups sem que se sobrescrevam, para manter histórico de versões.

---

## Issue 30 — UNI2: Reset de tabelas operacionais do banco

**Tipo:** HITL
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Criar uma migração Alembic que executa `DELETE FROM` nas tabelas operacionais (respeitando FKs) e reseta sequências de ID. **Mantém** tabelas administrativas (usuários, estabelecimento, categorias, fornecedores, garçons, métodos_pagamento, produtos com ficha técnica zerada).

**Ordem de deleção:**
1. `pagamentos`
2. `itens_comanda`
3. `comandas`
4. `movimentos_estoque`
5. `itens_compra`
6. `compras`
7. `ficha_tecnica`
8. `insumos`

**Reset de sequências:** `ALTER SEQUENCE <table>_id_seq RESTART WITH 1` para cada tabela.

**Decisão arquitetural (HITL):** confirmar com o usuário antes de executar — operação destrutiva.

### Critérios de aceite

- [ ] Migração criada e versionada via Alembic
- [ ] `alembic upgrade head` em DB de teste deleta dados operacionais sem erro
- [ ] Tabelas administrativas (garçons, métodos, categorias, fornecedores, produtos sem ficha) permanecem com dados
- [ ] Sequências de ID resetadas — próxima compra criada terá id=1
- [ ] Migração possui `downgrade` consistente (pode ser no-op por ser destrutiva)
- [ ] Validação manual em DB local antes de aplicar em qualquer ambiente

### User stories endereçadas

- US (transversal): Como sistema, quero alinhar os dados de insumos e compras com o novo modelo de unidades por família, evitando inconsistências com dados criados sob a decisão U3 anterior.

---

## Issue 31 — UNI1 + CP12 + FT1: Sistema de unidades por família (compra + ficha técnica)

**Tipo:** HITL
**Bloqueado por:** Issue 30 (UNI2) — reset banco precisa ocorrer antes para testes consistentes

### O que construir

Introduzir o conceito de **família de unidade** com conversão automática em compras e ficha técnica. Backend mantém `unidade_base` único por insumo — toda conversão acontece no frontend antes do submit.

**Frontend — `lib/units.ts` (novo):** módulo com `getFamilyOptions(unidadeBase, quantidadeCaixa)` e `toBase(value, option)`.

**Famílias suportadas:**
- Peso: `kg` ↔ `g` (fator 1000)
- Volume: `l` ↔ `ml` (fator 1000)
- Contagem: `un` ↔ `cx` (fator = `quantidade_caixa`)

**CP12 — `NovaCompraPage.tsx`:** substituir coluna fixa "Unidade" por `<select>` adjacente ao input de quantidade, populado por `getFamilyOptions(item.unidade_base, item.quantidade_caixa)`. Estado local de unidade selecionada por linha. Submit converte para a `unidade_base` do insumo via `toBase`.

**FT1 — `ProdutoModal.tsx` (ficha técnica):** cada linha da ficha ganha seletor de unidade ao lado da quantidade. `calcCmv` converte para unidade base antes de multiplicar pelo `custo_medio`. Payload submetido com quantidade convertida.

**Backend:** nenhuma mudança — continua recebendo e armazenando na `unidade_base` do insumo.

### Critérios de aceite

- [ ] Módulo `lib/units.ts` criado com `getFamilyOptions` e `toBase` testados
- [ ] Insumo `unidade_base = kg` → na compra, seletor lateral oferece `kg` e `g`
- [ ] Digitar "1" + selecionar `kg` → backend recebe `quantidade = 1` (em kg)
- [ ] Digitar "1000" + selecionar `g` → backend recebe `quantidade = 1` (em kg, convertido)
- [ ] Insumo `unidade_base = un` com `quantidade_caixa = 12` → seletor oferece `un` e `cx`
- [ ] Digitar "5" + selecionar `cx` → backend recebe `quantidade = 60` (em un, convertido)
- [ ] Insumo `un` sem `quantidade_caixa` → seletor mostra apenas `un`
- [ ] Insumo `g` puro → seletor oferece `g` e `kg`
- [ ] Em `ProdutoModal`, ficha técnica de carne (`kg`) com "200 g" → payload tem `quantidade = 0.2` (em kg)
- [ ] CMV exibido na `ProdutoModal` reflete a conversão correta
- [ ] Trocar item na compra reseta também a unidade selecionada (consistência com CP8)
- [ ] Estoque e relatórios pré-existentes não regridem (testes manuais de happy path)

### User stories endereçadas

- US1: Como sócio, quero cadastrar carne com `unidade_base = kg` e usá-la na ficha técnica do X-Burguer digitando "200 g", para não precisar converter mentalmente.
- US2: Como sócio, quero registrar a compra de 5 caixas de Heineken digitando "5 cx" em vez de calcular 60 unidades, para reduzir erro de operação.
- US3: Como sistema, quero armazenar internamente sempre na `unidade_base` do insumo, para que relatórios e cálculos de CMV continuem funcionando sem alteração.

---

## Resumo

| # | ID PRD | Tipo | Bloqueado por |
|---|--------|------|---------------|
| 1 | DB2 | AFK | — |
| 2 | CM1 | AFK | — |
| 3 | EM1 | AFK | — |
| 4 | MOD1+NC1+NC2 | AFK | — |
| 5 | MOD1b | AFK | — |
| 6 | FE2 | AFK | — |
| 7 | FE4 | AFK | — |
| 8 | DE1+DE2 | AFK | — |
| 9 | FE1+CV1 | AFK | — |
| 10 | FE3 | AFK | — |
| 11 | CA1 | AFK | — |
| 12 | CA2 | AFK | — |
| 13 | MV1+MV2 | AFK | — |
| 14 | CP4 | AFK | — |
| 15 | CP5 | AFK | — |
| 16 | CP6 | AFK | — |
| 17 | CP7 | AFK | — |
| 18 | CP8 | AFK | — |
| 19 | CP9 | AFK | — |
| 20 | CP10 | AFK | — |
| 21 | CP11 | AFK | — |
| 22 | AR1+AR2 | AFK | — |
| 23 | CD1+CD2 | AFK | — |
| 24 | VD1+VD2 | AFK | — |
| 25 | CG1 | AFK | — |
| 26 | DB1 | AFK | — |
| 27 | SB1 | AFK | — |
| 28 | ES1 | AFK | — |
| 29 | BK1 | AFK | — |
| 30 | UNI2 | HITL | — |
| 31 | UNI1+CP12+FT1 | HITL | #30 |

**31 issues no total.** 29 AFK (paralelos), 2 HITL (UNI2 → UNI1 em sequência).

**Recomendação de execução:**
- Bloco 1 (paralelo): issues 1-13 (limpeza, fixes de schema/RHF, UX pontuais)
- Bloco 2 (paralelo): issues 14-21 (todas as correções de compras pré-unidades)
- Bloco 3 (paralelo): issues 22-29 (navegação, listagens, features pequenas)
- Bloco 4 (sequencial): issue 30 → issue 31 (reset banco → unidades)
