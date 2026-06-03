# Flow4Tech — Sistema de Gestão (Matchpoint)

Monorepo do sistema Matchpoint MVP.

## Apps

| App | Stack | Pasta | README |
|-----|-------|-------|--------|
| Backend | Python 3.9+, FastAPI, SQLAlchemy 2.0, PostgreSQL | `backend/` | [`backend/README.md`](backend/README.md) |
| Frontend | React 18, Vite 5, TypeScript, Tailwind, TanStack Query, Zustand, RHF/Zod, shadcn/ui | `frontend/` | [`frontend/README.md`](frontend/README.md) |

## Documentação

- `docs/matchpoint_documentacao.md` — documento mestre (fluxo + arquitetura Deep Models)
- `docs/prd_matchpoint_mvp.md` — PRD do MVP
- `docs/issues_matchpoint_mvp.md` — fatias verticais para implementação.

## Setup rápido

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
make install
cp .env.example .env
make dev

# Frontend (em outro terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Status

- [x] Foundation (Issue #1) — skeleton + observabilidade
- [ ] Auth (Issue #2)
- [ ] Cadastros base (Issue #3)
- [ ] Itens + ficha técnica (Issue #4)
- [ ] Estoque & Compras (Issue #5)
- [ ] Comandas — núcleo (Issue #6)
- [ ] Fechamento (Issue #7)
- [ ] Comprovante (Issue #8)
- [ ] Reabertura (Issue #9)
- [ ] Relatórios operacionais (Issue #10)
- [ ] Relatórios financeiros (Issue #11)
- [ ] Dashboard (Issue #12)
- [ ] Configurações (Issue #13)
- [ ] UX sweep (Issue #14)

## Hospedagem

Vercel (FE) + Railway (BE+DB) — decisão arquitetural; integração ainda não ativada. Desenvolvimento e testes locais.
