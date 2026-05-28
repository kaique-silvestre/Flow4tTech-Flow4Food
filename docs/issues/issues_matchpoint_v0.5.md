# Issues — Sprint Portela (Melhorias Operacionais)

**Parent PRD:** `ai-context/prds/prd-melhorias-operacionais-portela.md`
**Gerado em:** 2026-05-14

Cada issue abaixo é uma fatia vertical (schema → API → UI). Todas as 5 são independentes entre si — podem ser executadas em paralelo. Issues 1, 2 e 3 são puramente frontend. Issues 4 e 5 envolvem backend + frontend.

---

## Visão geral — grafo de dependências

```
1 Fix timer comanda (frontend)  ─────────────────────────────┐
2 Filtro hierárquico subcategoria (frontend)  ───────────────┤
3 Atalho garçom inline (frontend)  ──────────────────────────┤── todas independentes
4 Produção possível por produto (backend + frontend)  ───────┤
5 Alerta de estoque crítico — badge + toast (backend + frontend)
```

---

## Issue 1 — Fix timer comanda: real-time + timezone correto

**Type:** AFK
**Blocked by:** None — pode começar imediatamente.

### What to build

O timer exibido na comanda aberta ("Aberta há X min") tem dois problemas: atualiza a cada 60 segundos (não é real-time) e pode exibir tempo incorreto por problema de timezone — o backend retorna `created_at` sem sufixo UTC, e o browser interpreta como hora local. Corrigir ambos, adicionando também formato "Xh Ymin" para comandas longas.

### Acceptance criteria

- [ ] Timer atualiza a cada 1 segundo (não mais 60 segundos).
- [ ] `created_at` é parseado como UTC independente de ter ou não sufixo `Z` na string.
- [ ] Comanda aberta há menos de 60 minutos exibe "Y min".
- [ ] Comanda aberta há 60 minutos ou mais exibe "Xh Ymin".
- [ ] Comanda com status `fechada` congela o timer (não atualiza).
- [ ] O mesmo fix de timezone é aplicado na listagem de comandas (ComandasPage) se houver exibição de tempo.
- [ ] Não há regressão visual no restante da tela da comanda.

### Blocked by

None — pode começar imediatamente.

### User stories addressed

- User story 10: timer atualiza em tempo real (a cada segundo)
- User story 11: formato "Xh Ymin" quando >= 60 minutos
- User story 12: formato "Y min" quando < 60 minutos
- User story 13: tempo correto sem desvio de timezone

---

## Issue 2 — Filtro hierárquico de subcategoria (cardápio + compras)

**Type:** AFK
**Blocked by:** None — pode começar imediatamente.

### What to build

Dois problemas de consistência no filtro de categoria: (1) no cardápio, selecionar uma categoria-pai não inclui produtos das subcategorias, e o select não exibe hierarquia; (2) na tela de compras, o modal de seleção de insumos não tem filtro de categoria algum. Unificar comportamento: select hierárquico com subcategorias indentadas, seleção de pai inclui filhos.

### Acceptance criteria

- [ ] No cardápio, o select de categoria exibe subcategorias indentadas abaixo da categoria-pai (usando o utilitário `flattenCategorias` já existente).
- [ ] No cardápio, selecionar uma categoria-pai filtra produtos da própria categoria E de todas as subcategorias descendentes.
- [ ] No cardápio, selecionar "Todas" remove o filtro e exibe todos os produtos.
- [ ] No modal de seleção de insumos (tela de compras), existe um select de categoria com as mesmas regras hierárquicas.
- [ ] No modal de compras, selecionar categoria filtra a lista de insumos exibidos (client-side).
- [ ] Sem filtro de categoria selecionado, todos os insumos aparecem normalmente.
- [ ] Não há regressão nos filtros existentes de texto/busca.

### Blocked by

None — pode começar imediatamente.

### User stories addressed

- User story 14: filtrar por categoria-pai inclui subcategorias no cardápio
- User story 15: select exibe hierarquia com subcategorias indentadas no cardápio
- User story 16: filtro de categoria disponível no modal de compras
- User story 17: filtro de compras inclui subcategorias ao selecionar pai

---

## Issue 3 — Atalho "+ Novo garçom" no modal de nova comanda

**Type:** AFK
**Blocked by:** None — pode começar imediatamente.

### What to build

Ao abrir uma nova comanda, se o garçom desejado não está cadastrado, o operador precisa abandonar o fluxo, navegar para Cadastros, criar o garçom e recomeçar. Adicionar botão "+ Novo garçom" ao lado do select no modal de nova comanda. Ao clicar, abre o modal de cadastro de garçom em overlay. Após salvar, o novo garçom fica automaticamente selecionado e o fluxo continua.

### Acceptance criteria

- [ ] Botão "+ Novo garçom" visível ao lado do select de garçom no modal de nova comanda.
- [ ] Clicar no botão abre o modal de cadastro de garçom sem fechar o modal de nova comanda.
- [ ] Após salvar o novo garçom, a lista de garçons é atualizada e o novo garçom fica selecionado automaticamente no select.
- [ ] Fechar o modal de cadastro sem salvar retorna ao modal de nova comanda com o estado preservado (identificação, tipo, pessoas já preenchidas).
- [ ] O restante do formulário de nova comanda não é afetado pelo fluxo inline.

### Blocked by

None — pode começar imediatamente.

### User stories addressed

- User story 1: cadastrar garçom novo diretamente no modal de nova comanda sem abandonar o fluxo
- User story 2: novo garçom automaticamente selecionado após cadastro inline

---

## Issue 4 — Produção possível por produto no cardápio

**Type:** AFK
**Blocked by:** None — pode começar imediatamente.

### What to build

O cardápio mostra preços e categorias, mas não informa quantas unidades de cada produto podem ser produzidas com o estoque atual. Calcular isso via ficha técnica: para cada insumo da receita, `floor(estoque_disponivel / quantidade_ficha)`; o mínimo entre todos os insumos é a produção possível. Exibir como coluna/badge na listagem do cardápio.

### Acceptance criteria

- [ ] Endpoint de listagem de produtos retorna campo `producao_possivel: int | null` para cada produto.
- [ ] Cálculo: `min(floor(estoque_disponivel_insumo / quantidade_ficha))` para todos os insumos da ficha técnica do produto.
- [ ] Produto sem ficha técnica cadastrada retorna `producao_possivel: null` (exibido como "—" no frontend).
- [ ] Produto com ficha técnica mas insumo sem estoque (estoque_disponivel = 0) retorna `producao_possivel: 0`.
- [ ] Produto com ficha técnica mas insumo com estoque negativo retorna `producao_possivel: 0` (não negativo).
- [ ] Cardápio exibe coluna ou badge "Produção possível" com o valor calculado.
- [ ] Valor "0" é exibido em destaque visual (ex: texto vermelho) para indicar impossibilidade de produção.
- [ ] Não há regressão nos demais dados do cardápio.

### Blocked by

None — pode começar imediatamente.

### User stories addressed

- User story 3: ver no cardápio quantas unidades de cada produto podem ser produzidas agora
- User story 4: cálculo baseado na ficha técnica do produto
- User story 5: produtos com ficha incompleta ou insumo sem estoque mostram 0 ou "—"

---

## Issue 5 — Alerta de estoque crítico: badge no navbar + toast no carregamento

**Type:** AFK
**Blocked by:** None — pode começar imediatamente.

### What to build

Insumos atingem nível crítico sem que o operador perceba — não há alerta visual nem notificação. Implementar três componentes: (1) campo `nivel_critico` configurável por insumo no formulário de edição; (2) endpoint que retorna insumos abaixo do threshold; (3) badge vermelho no navbar de Estoque com o count de insumos críticos; (4) toast ao carregar o app listando os insumos em estado crítico.

### Acceptance criteria

- [ ] Novo campo `nivel_critico` (decimal, nullable) na tabela `insumos` com migration Alembic.
- [ ] Campo `nivel_critico` disponível no formulário de edição de insumo (input numérico opcional, sem valor = sem alerta para aquele insumo).
- [ ] Endpoint `GET /api/estoque/criticos` retorna lista de insumos onde `estoque_disponivel < nivel_critico` e `nivel_critico IS NOT NULL`.
- [ ] Badge vermelho no item de menu "Estoque" na sidebar exibe o count de insumos críticos.
- [ ] Badge some (ou exibe 0 sem destaque) quando não há insumos críticos.
- [ ] Clicar no badge navega para a EstoquePage normal (todos os insumos visíveis, sem filtro pré-aplicado).
- [ ] Ao carregar o app (layout raiz), um toast é exibido para cada insumo crítico com mensagem "Estoque crítico: [nome do insumo] — X [unidade] restantes".
- [ ] Toast de estoque crítico dispara apenas uma vez por sessão (não repete a cada navegação entre páginas).
- [ ] Insumo sem `nivel_critico` configurado não aparece no endpoint nem gera toast.
- [ ] Não há regressão nos dados de estoque existentes.

### Blocked by

None — pode começar imediatamente.

### User stories addressed

- User story 6: configurar nível crítico por insumo
- User story 7: badge vermelho no menu Estoque com count de críticos
- User story 8: toast ao abrir o sistema quando há insumos críticos
- User story 9: toast mostra nome do insumo e quantidade restante

---

## Resumo de criação via gh (quando disponível)

```bash
# Criar issues nesta ordem (todas independentes, ordem é indiferente):
gh issue create --title "fix: timer comanda — real-time + timezone correto" --body-file <recorte issue 1>
gh issue create --title "feat: filtro hierárquico de subcategoria no cardápio e compras" --body-file <recorte issue 2>
gh issue create --title "feat: atalho cadastro garçom inline no modal de nova comanda" --body-file <recorte issue 3>
gh issue create --title "feat: produção possível por produto no cardápio" --body-file <recorte issue 4>
gh issue create --title "feat: badge estoque crítico no navbar + toast no carregamento" --body-file <recorte issue 5>
```
