# Onboarding — Setup do Ambiente Local

## Pré-requisitos

| Ferramenta | Versão mínima | Verificar |
|---|---|---|
| Python | 3.12 | `python --version` |
| Node.js | 20 | `node --version` |
| npm | 10 | `npm --version` |
| PostgreSQL | 16+ | `psql --version` |
| Git | qualquer | `git --version` |

## 1. Clonar e configurar Git

```powershell
git clone https://github.com/kaique-silvestre/Flow4tTech-Flow4Food.git
cd Flow4tTech-Flow4Food
git checkout development
```

## 2. Banco de dados local

Criar o banco e o usuário (requer acesso ao superuser `postgres`):

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "CREATE USER matchpoint WITH PASSWORD 'matchpoint';"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "CREATE DATABASE matchpoint OWNER matchpoint;"
```

## 3. Backend

```powershell
cd backend

# Criar e ativar venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instalar dependências (incluindo dev: ruff, mypy, pytest)
pip install -e ".[dev]"

# Criar arquivo de configuração local
copy .env.example .env
# Editar .env com seus valores locais (DATABASE_URL já deve funcionar com os valores acima)
```

### Arquivo `.env` mínimo para rodar local

```
DATABASE_URL=postgresql://matchpoint:matchpoint@localhost:5432/matchpoint
JWT_SECRET=qualquer-string-de-no-minimo-32-caracteres-aqui
ENV=dev
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
```

```powershell
# Rodar migrations
alembic upgrade head

# Verificar que ficou no head correto
alembic current

# Rodar backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend disponível em `http://localhost:8000`. Swagger em `http://localhost:8000/docs`.

## 4. Frontend

```powershell
cd frontend

# Instalar dependências
npm install

# Criar arquivo de ambiente local
copy .env.example .env.local
# Ou criar manualmente com:
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Rodar frontend
npm run dev
```

Frontend disponível em `http://localhost:5173`.

## 5. Verificar que tudo funciona

1. Abrir `http://localhost:5173`
2. Fazer login com as credenciais de seed (criadas na migration `0036`)
3. Verificar que o dashboard carrega sem erros no console

## 6. Fluxo de trabalho

Ver [workflow-3-ambientes.md](workflow-3-ambientes.md) para o fluxo completo de desenvolvimento.

Resumo rápido:

```powershell
# Criar branch de feature a partir de development
git checkout development
git checkout -b feature/nome-da-feature

# Desenvolver, commitar...

# Subir para staging para teste
git checkout staging
git merge feature/nome-da-feature
git push origin staging

# Após validação em staging → prod
git checkout main
git merge staging
git push origin main
```

## Troubleshooting comum

### `alembic upgrade head` falha com erro de conexão

Verificar se o PostgreSQL está rodando:
```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" status -D "C:\Program Files\PostgreSQL\18\data"
```

### `SET LOCAL ROLE app_user` falha

A role `app_user` precisa existir no banco. Criar manualmente:
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d matchpoint -c "
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user;
  END IF;
END \$\$;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
"
```

> **Nota:** Isso deveria ser feito via migration. Ver pendências em [workflow-3-ambientes.md](workflow-3-ambientes.md#101-role-app_user-não-existe-no-banco).

### Frontend mostra erro de CORS

Verificar que `CORS_ORIGINS` no `.env` do backend inclui `http://localhost:5173`.

### Erro de tipo no `mypy`

```powershell
mypy src/ --ignore-missing-imports
```

Se houver muitos erros em código legado, focar apenas nos arquivos novos/alterados.
