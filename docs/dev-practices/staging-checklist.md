# Checklist de Validação — Staging antes de ir pra Prod

> Executar após cada merge em `staging` e antes de abrir PR para `main`.
> Se qualquer item falhar, investigar e corrigir em `development` antes de prosseguir.

---

## 0. Pré-requisitos

- [ ] Smoke test do GitHub Actions passou (`GET /health` retornou 200)
- [ ] Railway dashboard mostra o deploy como `SUCCESS`
- [ ] Frontend local apontando para staging:
  ```powershell
  $env:VITE_API_URL="https://flow4tech-flow4food-staging.up.railway.app"
  cd frontend && npm run dev
  ```

---

## 1. Autenticação

- [ ] Login com credenciais válidas funciona
- [ ] Token de refresh funciona (recarregar página após login)
- [ ] Logout limpa sessão

---

## 2. Migrations

- [ ] Verificar que todas as migrations foram aplicadas:
  ```bash
  # No Console Railway (staging)
  /opt/venv/bin/alembic current
  # Deve mostrar a revision mais recente com (head)
  ```

---

## 3. Consumo Interno (se houve mudança no módulo)

- [ ] Tela carrega sem erro
- [ ] KPIs exibem valores (mesmo que zero)
- [ ] Calendário renderiza corretamente nas 3 abas (Semana, Mês, Ano)
- [ ] Modal "Lançar Consumo" abre
- [ ] Busca de produto no modal retorna resultados
- [ ] Adicionar produto ao carrinho funciona
- [ ] Mesmo produto adicionado duas vezes acumula quantidade
- [ ] Preview de custo estimado aparece
- [ ] Confirmar lançamento persiste no banco (aparece na lista)
- [ ] Timestamps aparecem no horário local correto (não 3h à frente)

---

## 4. Comandas

- [ ] Lista de comandas abertas carrega
- [ ] Nova comanda pode ser criada
- [ ] Item pode ser adicionado à comanda
- [ ] Pré-conta abre e imprime corretamente
- [ ] Fechamento de comanda funciona

---

## 5. Estoque — Movimentos

- [ ] Aba Insumos: lista movimentos com filtros funcionando
- [ ] Badges de tipo exibem cor correta:
  - `entrada` → verde
  - `saida_venda` → azul
  - `saida_perda` → laranja
  - `saida_consumo_interno` → roxo
  - `entrada_estorno` → teal

---

## 6. Configurações gerais

- [ ] Dados do estabelecimento carregam
- [ ] Nenhum erro 500 no console do browser durante navegação normal

---

## 7. Após validação completa

- [ ] Abrir PR `staging → main` no GitHub
- [ ] Verificar que CI passa no PR
- [ ] Confirmar com Kaique antes do merge se houver migration
