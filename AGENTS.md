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

## Changelog

Toda modificação de código (feature, fix, refactor, migration, config) exige entrada em `CHANGELOG.md` na raiz. Sem exceção — mesmo mudanças pequenas.

**Onde**: seção `## [Unreleased]`, topo do arquivo. Uma entrada por mudança lógica (não por commit).

**Formato de cada entrada**:

```
### Added|Changed|Fixed|Removed|Security
- Descrição objetiva da mudança — Autor, AAAA-MM-DD
```

- **Categoria**: `Added` (novo), `Changed` (comportamento existente alterado), `Fixed` (bug), `Removed` (remoção), `Security` (correção de vulnerabilidade). Agrupe entradas da mesma categoria sob um único cabeçalho.
- **Descrição**: o quê mudou e por quê, não como (o código já mostra o como). Uma frase.
- **Autor**: SEMPRE o humano responsável pela mudança — nunca o nome do agente (`Claude`, `Copilot`, etc.). Formato `Nome Sobrenome <email>`, obtido de `git config user.name` / `git config user.email` no repo local. Se a identidade não puder ser confirmada por `git config`, pergunte ao usuário antes de escrever a entrada — não adivinhe nem deixe genérico.
- **Data**: data real da mudança, formato `AAAA-MM-DD`.

Exemplo:

```
## [Unreleased]

### Fixed
- Corrige BigInteger PK que não auto-incrementa no SQLite — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20

### Added
- Endpoint de exportação de comandas em CSV — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
```

Ao cortar uma release, renomeie `[Unreleased]` para `[versão] - AAAA-MM-DD` e abra um novo `[Unreleased]` vazio acima.
