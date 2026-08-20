# Changelog

Todas mudanças notáveis deste projeto documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Categorias: `Added`, `Changed`, `Fixed`, `Removed`, `Security`.

## [Unreleased]

<!-- Novas entradas entram aqui, no topo. Ver CLAUDE.md → "Changelog" para o padrão de preenchimento. -->

### Fixed

- Corrige 4 bugs financeiros em comandas/relatórios: (1) desconto era subtraído duas vezes no faturamento líquido de `vendas-do-dia` e `fechamento-caixa`, pois `comanda.total` já é o valor pós-desconto; (2) reabrir uma comanda fechada não excluía os `Pagamento`s e a `ComissaoGarcom` já gravados, duplicando-os caso a comanda fosse fechada novamente; (3) desconto percentual não era resolvido em `desconto_valor` no fechamento, fazendo relatórios reportarem R$ 0,00 de desconto para comandas com desconto em porcentagem; (4) cortesias sempre reportavam R$ 0,00 em `_cortesias_por_comanda` porque a query somava `preco_unitario` (zerado por design para itens cortesia) em vez do `preco_venda` do produto — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Corrige anotações `Mapped[X | None]` incompatíveis com Python 3.9 em src/models — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20

### Removed

- Remove funcionalidade de backup (rota, serviço e aba na UI) — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Remove tabela global config_seguranca e o endpoint PATCH /api/config/senha (rota, serviço, repositório, model, schema e aba "Senha" na UI) — código morto que compartilhava uma "senha de segurança" entre todos os tenants, sem tenant_id nem RLS (migration 0080) — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20

### Security

- Endurece `require_platform_admin`: agora rejeita tokens revogados (checagem em `revoked_tokens`) e contas de platform admin desativadas após a emissão do JWT; adiciona `POST /api/platform/auth/logout` para revogar o token de platform admin — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Adiciona RLS (ENABLE + FORCE) às tabelas permission_templates e template_permissions, que nunca tiveram isolamento por tenant no banco — a proteção existia só no repositório (get_template_by_id não filtrava por tenant_id) (migration 0081) — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Aplica FORCE ROW LEVEL SECURITY em tenant_eventos, promocoes e user_permissions — sem FORCE, o owner da tabela ignorava a policy de RLS e expunha dados entre tenants (migration 0079) — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Bloqueia auto-escalação de permissões — usuário não pode mais alterar as próprias telas de acesso — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Corrige endpoint check-email que expunha existência de e-mails de qualquer tenant sem exigir permissão — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Elimina vetor de vazamento de dados de todos os tenants (senha, tokens) via rota de backup que ignorava RLS — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
