# Práticas de Desenvolvimento — Flow4Tech

Documentação interna de engenharia. Leitura obrigatória antes de contribuir.

## Documentos

| Doc | O que cobre |
|---|---|
| [workflow-3-ambientes.md](workflow-3-ambientes.md) | Dev → Staging → Prod, migrations seguras, RLS/multi-tenant |
| [ci-cd.md](ci-cd.md) | Pipeline GitHub Actions, o que roda em cada etapa |
| [onboarding.md](onboarding.md) | Setup do ambiente local do zero |
| [convencoes.md](convencoes.md) | Commits, branches, naming, code style |

## Princípios

1. **Banco do cliente é sagrado** — nenhuma migration vai pra prod sem passar por staging
2. **Migrations são irreversíveis em prod** — escreva como se não houvesse downgrade
3. **Toda tabela nova com dados de tenant leva RLS** — sem exceção
4. **Segredos nunca no git** — `.env` está no `.gitignore`, mantenha assim
