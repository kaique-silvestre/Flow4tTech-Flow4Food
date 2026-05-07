# Matchpoint Backend

Backend FastAPI seguindo arquitetura **Deep Models**.

## Setup

Requisitos: Python 3.9+ (3.11+ recomendado), Postgres opcional para dev (testes mockam).

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
make install
cp .env.example .env
```

## Comandos

| Comando | Ação |
|---------|------|
| `make dev` | Sobe API local com reload em `:8000` |
| `make test` | Roda pytest |
| `make lint` | Roda ruff |
| `make type-check` | Roda mypy |
| `make check` | lint + type-check + test |
| `make migrate` | Aplica migrations |
| `make makemigration name="msg"` | Gera nova migration |

## Estrutura

Deep Models — ver `docs/matchpoint_documentacao.md` §10.

```
src/
├── api/          # Camada de apresentação (rotas FastAPI)
├── services/     # Lógica de negócio
├── repositories/ # Acesso a dados
├── models/       # SQLAlchemy ORM
├── schemas/      # DTOs Pydantic
└── core/         # Config, DB, logging, errors, middleware
```

## Health check

```bash
curl http://localhost:8000/health
```
