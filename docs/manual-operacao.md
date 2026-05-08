# Manual de Operação — Matchpoint MVP

**Fluxo principal: abrir → lançar itens → fechar comanda**

---

## 1. Login

Acesse `/login`. Digite a senha configurada pelo administrador. Clique em **Entrar**.

---

## 2. Abrir nova comanda

1. No menu lateral, clique em **Comandas**.
2. Clique em **Nova Comanda**.
3. Preencha:
   - **Tipo**: Mesa ou Balcão
   - **Identificação**: número da mesa (ex: "12") ou nome (ex: "Balcão")
   - **Garçom**: selecione o responsável
4. Clique em **Abrir Comanda**.

---

## 3. Lançar itens

Na tela da comanda aberta:

1. **Busca rápida**: digite o nome do item no campo de busca, ou clique em um dos itens frequentes.
2. Ajuste **quantidade** (padrão: 1).
3. Opcional: informe **pessoa associada** (para dividir por pessoa) ou **observação**.
4. Para **cortesia**: marque a caixa "Cortesia" (item vai a R$ 0,00).
5. Clique em **Lançar**.

Para cancelar um item lançado: clique em **Cancelar** ao lado do item, informe o motivo.

---

## 4. Fechar comanda

1. Na comanda aberta, clique em **Fechar Comanda**.
2. Escolha a forma de divisão: **Total**, **Por pessoa**, ou **Itens por pessoa**.
3. Adicione os pagamentos (método + valor). Você pode dividir em múltiplos métodos.
4. Clique em **Confirmar Fechamento**.
5. O sistema exibe o comprovante. Clique em **Imprimir** para imprimir na térmica.

---

## 5. Reabrir comanda (se necessário)

Na tela da comanda fechada, clique em **Reabrir Comanda** → confirme no diálogo. Os pagamentos são estornados e o estoque restaurado.

---

## 6. Backup dos dados

1. No menu lateral, clique em **Configurações** → aba **Backup**.
2. Clique em **Exportar JSON** (dump completo de todas as tabelas) ou **Exportar Excel** (comandas, itens, movimento de estoque).
3. O arquivo é baixado automaticamente.

---

## 7. Atalhos importantes

| Tela | Ação |
|------|------|
| Comandas | Nova comanda |
| Comanda aberta | Lançar item, cancelar item |
| Fechamento | Confirmar pagamento |
| Configurações | Alterar senha, dados do estabelecimento, backup |
