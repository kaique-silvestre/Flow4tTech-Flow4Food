---
covers: backend/src/services/dashboard_service.py
---

# "Pagamento hoje" no dashboard não reusa a query de fechamento de caixa

O relatório oficial de fechamento de caixa (`fechamento_caixa`/`_build_por_metodo`) soma `Pagamento` filtrando por comandas com `status="fechada"` no período — uma comanda com pagamento parcial que reabre (status `reaberta`) fica de fora, mesmo que dinheiro/pix já tenha entrado fisicamente hoje.

O card "Formas de Pagamento Hoje" do dashboard existe para responder "quanto de troco/caixa físico eu preciso agora" — uma pergunta sobre dinheiro já recebido, não sobre comandas encerradas. Por isso ele usa uma query própria, agregando `Pagamento` por `Pagamento.created_at` no dia corrente, independente do status da comanda, em vez de reusar `_build_por_metodo`.

Consequência esperada e aceita: o total do card pode divergir do total mostrado no fechamento de caixa oficial do dia (que só fecha quando as comandas parciais também fecharem). Se um usuário comparar os dois números e estranhar a diferença, essa é a explicação — não é bug.
