# Matchpoint — Guia de Desenvolvimento

## Rodar o Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

> PowerShell não resolve `.venv\Scripts\uvicorn.exe` diretamente — sempre ativar o venv primeiro.

## Rodar o Frontend

```powershell
cd frontend
npm run dev
```

## Validações Frontend

```powershell
cd frontend
npm run type-check
npm run lint
npm run build
```

## Migrations Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
alembic upgrade head
```
