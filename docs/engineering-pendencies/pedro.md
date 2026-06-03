# Pendências — Pedro

Ações que Pedro consegue executar diretamente (acesso de push ao repo, Railway staging, Vercel website).

---

## 1. Commitar e Subir as Mudanças Atuais

Mudanças prontas em `development` aguardando commit:

- `backend/alembic/versions/0050_create_app_user_role.py` — migration crítica (cria role `app_user`)
- `backend/tests/integration/` — testes de auth, RLS e CRUD
- `.github/workflows/ci.yml` — CI passa a falhar em testes quebrados (removido `continue-on-error`)
- `docs/dev-practices/README.md` — link para doc de pendências
- `docs/dev-practices/pendencias-manuais.md` — doc original de pendências

```bash
git add backend/alembic/versions/0050_create_app_user_role.py
git add backend/tests/integration/
git add .github/workflows/ci.yml
git add docs/
git commit -m "feat: add app_user role migration, integration tests, and engineering docs"
git push origin development
```

---

## 2. Abrir PR development → staging

```bash
gh pr create \
  --repo kaique-silvestre/Flow4tTech-Flow4Food \
  --base staging \
  --head development \
  --title "feat: app_user role + integration tests" \
  --body "- Migration 0050: cria role app_user (fix crítico para RLS)\n- Testes de integração: auth, RLS e CRUD\n- CI agora falha em testes quebrados"
```

O CI vai rodar automaticamente. Depois que passar, Kaique pode configurar o branch protection (item 1 do `kaique.md`).

---

## 3. Verificar CI no PR

Após abrir o PR:
1. Ir para o PR no GitHub
2. Aguardar os checks `backend` e `frontend` ficarem verdes
3. Se algum falhar: `gh run view --log-failed` para ver o erro

---

## 4. Backup via Script (se Kaique não fizer upgrade Railway)

Se Kaique decidir não fazer upgrade de plano, Pedro implementa o script de backup:
- `pg_dump` via GitHub Actions agendado (`cron: '0 3 * * *'`)
- Upload do dump para S3 ou artefato do GitHub
- Retenção de 7 dias

Aguardar decisão do Kaique antes de implementar.
