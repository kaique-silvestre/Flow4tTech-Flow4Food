# PRD Matchpoint v0.4 — Melhorias de UX, Correções e Reserva de Estoque

**Data:** 2026-05-12
**Status:** Aprovado para implementação

---

## Problem Statement

O sistema de gestão Matchpoint apresenta uma série de problemas de usabilidade e lógica que prejudicam a operação diária do estabelecimento:

1. O modal de nova comanda abre com "Número da mesa" selecionado, mas o negócio identifica comandas por nome do responsável — operadores precisam trocar manualmente toda vez.
2. Produtos desativados continuam aparecendo na busca de itens durante uma comanda aberta, causando confusão.
3. Pagamentos em dinheiro não possuem suporte a troco — o sistema não captura o valor da nota recebida nem calcula o troco a devolver.
4. Criar um produto sem selecionar categoria dispara um toast de erro genérico, sem indicar o campo problemático.
5. Toasts de erro ficam na tela indefinidamente (duração `Infinity`), bloqueando a interface visualmente.
6. Produtos com subcategoria exibem apenas o nome da subcategoria no cardápio, sem contexto hierárquico ("Sucos" em vez de "Bebidas > Sucos").
7. Campos de valor monetário (preço de venda, custo de compra) são inputs numéricos simples sem máscara de dinheiro, facilitando erros de digitação.
8. O sistema só verifica insuficiência de estoque no fechamento da comanda — tarde demais para o operador reagir. Além disso, o estoque não é reservado durante a comanda aberta, permitindo que múltiplas comandas consumam o mesmo insumo sem aviso.

---

## Solution

Oito melhorias incrementais que corrigem os problemas acima sem quebrar funcionalidades existentes:

1. Inverter a ordem e o padrão do seletor de tipo de identificação na nova comanda.
2. Adicionar filtro `ativo=true` na busca de produtos dentro da comanda aberta.
3. Implementar captura de valor da nota e cálculo de troco para pagamentos em dinheiro, com persistência no banco de dados.
4. Adicionar validação Zod com erro inline no campo de categoria ao criar/editar produto.
5. Definir duração de 8 segundos para toasts de erro.
6. Exibir hierarquia de categorias no cardápio no formato `"Categoria > Subcategoria"`.
7. Criar componente `MoneyInput` com máscara BRL e aplicá-lo em todos os campos de valor monetário.
8. Implementar sistema de reserva de estoque: reservar insumos ao adicionar item à comanda, avisar imediatamente quando estoque for insuficiente, liberar ao cancelar, confirmar ao fechar.

---

## User Stories

### Comanda — Identificação

1. Como garçom, quero que o modal de nova comanda abra já com "Nome do responsável" selecionado, para não precisar trocar manualmente em cada atendimento.
2. Como garçom, quero que o campo "Nome do responsável" apareça primeiro na lista de opções, para encontrá-lo mais rapidamente.

### Comanda — Produtos

3. Como garçom, quero que a busca de itens na comanda aberta mostre apenas produtos ativos, para não adicionar por engano um produto que foi desativado.
4. Como gerente, quero que produtos desativados continuem visíveis na tela de cardápio (com toggle de filtro), para gerenciar o histórico completo.

### Pagamento em dinheiro

5. Como operador de caixa, quero informar o valor da nota recebida ao selecionar "Dinheiro" como método de pagamento, para calcular automaticamente o troco.
6. Como operador de caixa, quero ver o troco calculado em tempo real enquanto digito o valor da nota, para confirmar antes de fechar a comanda.
7. Como operador de caixa, quero ser avisado quando o valor da nota for inferior ao total a pagar, para corrigir antes de confirmar.
8. Como operador de caixa, quero que o valor da nota e o troco sejam registrados no banco de dados, para auditoria e conferência de caixa.
9. Como cliente, quero que o comprovante da comanda mostre o valor recebido e o troco, para ter registro completo da transação.
10. Como gerente, quero classificar métodos de pagamento por tipo (dinheiro, crédito, débito, pix, outro), para que o sistema identifique corretamente quando exibir o campo de troco.

### Produtos — Validação de categoria

11. Como gerente, quero ver uma mensagem de erro diretamente abaixo do campo de categoria quando tento salvar um produto sem categoria, para saber exatamente o que corrigir.
12. Como gerente, quero que o botão de salvar produto não dispare uma chamada ao servidor quando campos obrigatórios estão vazios, para evitar erros desnecessários.

### Toasts

13. Como operador, quero que toasts de erro somam automaticamente após 8 segundos, para que não bloqueiem a interface indefinidamente.
14. Como operador, quero poder fechar um toast clicando nele a qualquer momento, independentemente da duração configurada.
15. Como operador, quero que toasts de sucesso somam em 2,5 segundos e toasts de aviso em 4,5 segundos, pois são informações menos críticas que erros.

### Subcategorias no cardápio

16. Como gerente, quero ver o caminho completo da categoria de cada produto no cardápio (ex: "Bebidas > Sucos"), para identificar a hierarquia sem precisar abrir cada produto.
17. Como gerente, quero que produtos sem subcategoria mostrem apenas o nome da categoria principal, sem quebrar o layout.

### Máscara de dinheiro

18. Como gerente, quero que o campo de preço de venda no cadastro de produtos exiba o prefixo "R$" e formate automaticamente os centavos enquanto digito, para reduzir erros de valor.
19. Como gerente, quero que os campos de custo total e custo unitário na tela de compras tenham a mesma formatação monetária, para consistência visual.
20. Como gerente, quero digitar "1050" e ver "R$ 10,50" formatado automaticamente, com vírgula decimal e ponto separador de milhar no padrão brasileiro.

### Reserva de estoque

21. Como garçom, quero receber um aviso imediato quando adiciono um produto cujos insumos estão insuficientes em estoque, para informar o cliente na hora.
22. Como garçom, quero poder adicionar o produto mesmo com estoque insuficiente (o aviso não bloqueia), para casos em que o gerente já sabe do reabastecimento pendente.
23. Como gerente, quero que os insumos sejam "reservados" quando adicionados a uma comanda aberta, para que o estoque disponível reflita apenas o que não está comprometido.
24. Como gerente, quero que a reserva de insumos seja liberada automaticamente quando um item é cancelado dentro de uma comanda, para que o estoque disponível seja atualizado em tempo real.
25. Como gerente, quero que a reserva seja liberada quando uma comanda inteira é cancelada, sem afetar o estoque definitivo.
26. Como gerente, quero que o estoque seja debitado definitivamente apenas quando a comanda é fechada com pagamento confirmado.
27. Como gerente, quero que pagamentos parciais não debitam o estoque — o débito ocorre apenas no fechamento total da comanda.
28. Como gerente, quero ver na tela de estoque/insumos três valores separados: "Estoque atual", "Reservado em comandas" e "Disponível", para entender o estado real do estoque.
29. Como gerente, quero que o campo "Disponível" fique destacado em vermelho quando for negativo, para identificar imediatamente insumos críticos.

---

## Implementation Decisions

### Módulos a modificar

**Frontend**

- `NovaComandaModal` — trocar `defaultValues.tipo_identificacao` de `"mesa"` para `"nome"`; inverter ordem dos radio buttons.
- `useProdutos` hook — adicionar parâmetro opcional `apenasAtivos: boolean` que envia `?ativo=true` na query.
- `ComandaAbertaPage` — passar `apenasAtivos=true` ao chamar `useProdutos`.
- `FechamentoPage` — detectar quando método selecionado é do tipo `"dinheiro"`; exibir campo `valor_nota` e troco calculado inline.
- `ComprovantePage` — exibir linhas de "Valor recebido" e "Troco" quando pagamento tem troco.
- `MetodoPagamentoModal` — adicionar campo de seleção de `tipo`.
- `produtoSchemas.ts` — tornar `categoria_id` obrigatório com mensagem de validação.
- `ProdutoModal` — exibir erro inline abaixo do select de categoria.
- `src/lib/toast.ts` — alterar duração do `error` de `Infinity` para `8000`.
- `CardapioPage` — substituir `catMap` simples por função que constrói caminhos hierárquicos recursivamente.
- `MoneyInput` (novo componente) — wrapper de `NumericFormat` (react-number-format) com prefixo `"R$ "`, separadores BRL e `fixedDecimalScale`.
- `NovaCompraPage` — aplicar `MoneyInput` nos campos de custo.
- Tela de estoque/insumos — adicionar colunas "Reservado" e "Disponível".

**Backend**

- Rota `GET /api/produtos` — aceitar query param `ativo: Optional[bool]`; repassar ao service e repository.
- `produtos_service.list_produtos` — aceitar e repassar parâmetro `ativo`.
- `MetodoPagamento` model — adicionar coluna `tipo` (enum: `dinheiro`, `credito`, `debito`, `pix`, `outro`), `server_default="outro"`.
- `Pagamento` model — adicionar colunas `valor_nota` (Numeric, nullable) e `troco` (Numeric, nullable).
- Schema de fechamento — adicionar `valor_nota` opcional ao `PagamentoRequest`; validar `valor_nota >= valor` quando fornecido.
- `pagamentos_repository` — persistir `valor_nota` e `troco` ao criar pagamento.
- `MetodoPagamentoResponse` — incluir campo `tipo`.
- `Insumo` model — adicionar coluna `estoque_reservado` (Numeric 12,4, `server_default=0`).
- `InsumoResponse` — incluir `estoque_reservado` e `estoque_disponivel` (calculado).
- `adicionar_item` service — após persistir item, calcular insumos via ficha técnica e incrementar `estoque_reservado`; retornar lista `estoque_insuficiente` na resposta.
- `cancelar_item` service — decrementar `estoque_reservado` dos insumos do item cancelado.
- `cancelar_comanda` service — decrementar `estoque_reservado` para todos os itens ativos da comanda.
- `_dar_baixa_estoque` (fechamento) — além de debitar `estoque_atual`, decrementar `estoque_reservado` pela mesma quantidade.
- `ComandaResponse` — adicionar campo `estoque_insuficiente: list[str]` (lista de nomes de insumos).

### Decisões arquiteturais

- **Identificação de "dinheiro"**: via coluna `tipo` no model, não por match de string no nome. Motivo: nome pode ser renomeado pelo usuário.
- **Reserva de estoque**: campo `estoque_reservado` no próprio `Insumo`, não tabela separada. Motivo: suficiente para a escala do sistema; simplifica queries de disponibilidade.
- **Aviso vs bloqueio**: adição de item com estoque insuficiente exibe toast de `warning` mas não bloqueia. Decisão operacional — garçom não pode travar no atendimento.
- **Pagamento parcial e reserva**: reserva permanece até fechamento total. `_dar_baixa_estoque` só executa em fechamento definitivo (comportamento já existente).
- **Consistência pós-deploy**: comandas abertas antes da migration terão `estoque_reservado=0` para seus itens. Aceitar inconsistência inicial; novas adições passam a reservar corretamente.
- **Subcategoria**: coluna única com breadcrumb `"A > B"`, sem nova coluna na tabela. Evita reestruturação do layout com 7+ colunas.
- **Máscara monetária**: entrada da esquerda para direita (`10` → `R$ 10,00`), não de caixa registradora. Mais natural para input web.

### Migrations necessárias

| # | Tabela | Alteração |
|---|--------|-----------|
| 1 | `metodos_pagamento` | + coluna `tipo` VARCHAR enum, `server_default='outro'` |
| 2 | `pagamentos` | + colunas `valor_nota` NUMERIC(10,2) nullable, `troco` NUMERIC(10,2) nullable |
| 3 | `insumos` | + coluna `estoque_reservado` NUMERIC(12,4) NOT NULL `default=0` |

Todas as migrations são additive (não removem nem alteram colunas existentes).

### API contracts relevantes

- `GET /api/produtos?ativo=true` — retorna apenas produtos com `ativo=true`
- `POST /api/comandas/{id}/itens` response — inclui campo `estoque_insuficiente: list[str]`
- `GET /api/insumos` response — inclui `estoque_reservado` e `estoque_disponivel`
- `POST /api/comandas/{id}/fechar` body — `pagamentos[].valor_nota` opcional; backend calcula e persiste `troco`
- `GET /api/metodos-pagamento` response — inclui campo `tipo`

---

## Testing Decisions

### O que faz um bom teste aqui

Testar comportamento externo observável, não implementação interna. Para o backend: testar via chamadas HTTP (endpoints), verificando status code, body e efeitos colaterais no banco. Não testar funções privadas (`_dar_baixa_estoque`, `_reservar_estoque`) diretamente — testá-las indiretamente via endpoint de fechar/adicionar item.

### Módulos prioritários para testes

**Backend (maior risco)**

- `adicionar_item`: verificar que `estoque_reservado` aumenta corretamente após adição; verificar que `estoque_insuficiente` lista insumos negativos.
- `cancelar_item`: verificar que `estoque_reservado` decresce corretamente.
- `fechar_comanda`: verificar que `estoque_atual` é debitado E `estoque_reservado` decresce; verificar que pagamento com `valor_nota` persiste `troco` correto.
- `cancelar_comanda`: verificar que todos os `estoque_reservado` são liberados.

**Frontend (menor risco para lógica de negócio)**

- `MoneyInput`: testar que formata corretamente entrada e retorna valor numérico sem máscara.
- `buildCatPaths`: testar com árvore de 2 níveis e com nó raiz (sem pai).

### Prior art nos testes

Seguir padrão dos testes existentes de comandas e estoque no backend (pytest + SQLite in-memory ou fixtures de banco).

---

## Out of Scope

- Histórico de reservas de estoque (audit trail de `estoque_reservado`).
- Notificação push/realtime para outros garçons quando estoque fica crítico.
- Bloqueio de adição quando estoque é zero (pode ser avaliado futuramente).
- Relatório de troco por período.
- Integração com impressora fiscal para comprovante com troco.
- Script automático de recálculo de `estoque_reservado` para comandas abertas pré-migration (pode ser feito manualmente se necessário).
- Alteração de comportamento do pagamento parcial em relação ao estoque.

---

## Further Notes

- A coluna `tipo` em `metodos_pagamento` pode ser usada futuramente para regras de comissão diferenciadas por método (ex: não contabilizar PIX na taxa de serviço do garçom).
- O campo `estoque_reservado` abre caminho para relatório de "previsão de ruptura": cruzar reservas com estoque e alertar o gerente proativamente.
- A máscara monetária (`MoneyInput`) deve ser extraída como componente compartilhado para garantir consistência em qualquer novo campo de valor que for adicionado ao sistema.
