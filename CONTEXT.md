# Matchpoint (Flow4Tech)

Sistema de gestão para bar/restaurante, multi-tenant. Cobre operação de salão (comandas, garçons), suprimentos (compras, estoque, insumos) e visão financeira (CMV, comissões, fechamento de caixa, relatórios).

## Language

**Comanda**:
Uma conta aberta associada a uma mesa/cliente, onde itens são lançados até o fechamento. Estados: `aberta`, `fechada`, `cancelada`, `reaberta` (reabre quando um pagamento parcial não cobre o saldo total).
_Avoid_: Mesa, pedido, conta (usar "comanda" sempre)

**Saldo Pendente**:
O valor de uma comanda que ainda falta ser pago após um pagamento parcial. Só existe em comandas `reaberta`; uma comanda `fechada` não tem saldo pendente.
_Avoid_: Saldo devedor, restante

**Pagamento**:
Um registro de dinheiro recebido para uma comanda, associado a um método (dinheiro/cartão/pix/etc). Uma comanda pode ter múltiplos pagamentos ao longo do tempo (pagamento parcial) antes de fechar — o pagamento existe independente do status da comanda estar `fechada`.
_Avoid_: Recebimento, transação

**Fechamento de Caixa**:
O relatório oficial que soma pagamentos apenas de comandas com status `fechada` em um período. Não reflete pagamentos parciais recebidos em comandas ainda `abertas`/`reaberta` — ver ADR-0001 para o caso em que essa distinção importa.
_Avoid_: Caixa do dia, resumo de vendas

**Insumo**:
Um item de estoque (ingrediente/matéria-prima) usado para compor produtos via ficha técnica. Tem `estoque_atual`, `estoque_reservado`, `custo_medio` e opcionalmente um `nivel_critico`.
_Avoid_: Ingrediente, item de estoque, matéria-prima

**Nível Crítico**:
Um limite mínimo de `estoque_disponivel` (estoque_atual − estoque_reservado) configurado manualmente por insumo. Abaixo dele, o insumo é considerado crítico. Não existe hoje um nível máximo/ideal equivalente — não inventar essa classificação sem um campo novo no schema.
_Avoid_: Estoque mínimo, ponto de reposição

**Produto**:
Um item vendável do cardápio. Tem `nome`, `categoria` (opcional, hierárquica em até 2 níveis), `preco_venda`, `preco_promocional` (opcional, sobrepõe `preco_venda` quando presente) e uma Ficha Técnica opcional que determina seu CMV. Um produto pode estar `ativo` ou inativo (desativado); produto inativo não desaparece do sistema, só some do filtro padrão "Ativos".
_Avoid_: Item, item do cardápio (usar "produto" sempre)

**Ficha Técnica**:
A composição de um produto em termos de quantidades de insumos, usada para calcular `custo_medio` do produto. Um produto sem ficha técnica cadastrada não tem CMV calculável (classificado como `sem_custo` nos relatórios).
_Avoid_: Receita, composição

**CMV** (Custo da Mercadoria Vendida):
O custo dos insumos consumidos para produzir o que foi vendido, calculado a partir da ficha técnica × custo médio. Expresso como valor absoluto ou como percentual do faturamento/preço de venda.
_Avoid_: Custo de produção, custo de venda

**Motivo de Perda**:
Uma classificação fechada (enum: `perda`, `quebra`, `cortesia`, `outro`) atribuída a uma baixa de estoque sem venda associada. "Cortesia" é um dos quatro motivos possíveis, não uma categoria separada de "perda" — ambas vivem no mesmo relatório (`perdas_cortesias`), agrupadas por motivo.
_Avoid_: Desperdício, quebra de estoque (usar "perda"/"quebra" conforme o motivo específico)

**Comissão**:
Um valor devido a um garçom sobre vendas atribuídas a ele, com um flag `pago` (booleano) indicando se já foi quitada. Não tem corte mensal automático — comissões não pagas se acumulam como dívida em aberto até serem marcadas como pagas individualmente.
_Avoid_: Bônus, gorjeta

**Usuário**:
Uma conta de acesso ao sistema, vinculada a exatamente um Perfil (opcionalmente nenhum, usuário "sem perfil" fica sem permissões). Tem `is_active` (pode ser desativado/reativado sem apagar histórico) e `is_owner` (o usuário dono do tenant — não pode ser desativado nem ter seu Perfil alterado por ninguém, nem por si mesmo). Um usuário não pode alterar o próprio Perfil nem as próprias permissões (regra do servidor, `users_service.py`) — evita autopromoção e autobloqueio acidental.
_Avoid_: Conta, login, membro

**Perfil**:
Um conjunto nomeado de permissões (`permissions`, lista de telas liberadas) atribuível a Usuários. Pode ser `is_system` (perfil que vem pronto com o sistema, ex. "Admin" — não editável como os perfis criados pelo tenant) e `is_active`. Um Perfil com usuários vinculados (`user_count > 0`) não pode ser desativado nem excluído — precisa remover os usuários dele primeiro.
_Avoid_: Role, cargo, função (usar "perfil" sempre)

**Tenant**:
Uma organização/cliente do sistema (um bar/restaurante), isolada dos demais via RLS (Row-Level Security) no banco. Todo dado operacional (comandas, insumos, pagamentos etc.) pertence a exatamente um tenant. Na UI, o tenant é rotulado **"Empresa"** (ex: bloco de identidade no topo da sidebar).
_Avoid_: Cliente (ambíguo com cliente do bar), organização, conta
