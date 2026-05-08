# PRP — Issue #13: Configurações

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 13
**Documento mestre:** `docs/matchpoint_documentacao.md` §8.8
**Type:** AFK
**Status:** Pendente
**Criado em:** 2026-05-08
**Depende de:** Issue #2 (Auth) — concluída

---

## Objetivo

Tela de configurações (`/configuracoes`) com 4 abas:

- **Estabelecimento** — `GET/PATCH /api/config/estabelecimento` (nome, CNPJ, endereço, telefone).
- **Senha** — `PATCH /api/config/senha` (valida senha atual, atualiza hash).
- **Impressora** — tela estática com instruções para configurar térmica Obitech WD-80R7 no SO.
- **Backup** — `GET /api/backup?formato=json|xlsx` (dump completo JSON ou 3 planilhas XLSX).

---

## Regras de Negócio Críticas

- `Estabelecimento` é singleton (id=1). `GET` retorna o registro ou defaults; `PATCH` faz upsert.
- Backup **JSON**: serializa todas as tabelas (todas as SQLAlchemy models registradas em `Base`).
- Backup **XLSX**: 3 planilhas — `comandas`, `itens`, `movimento_estoque`. Colunas = nomes das colunas da tabela.
- `PATCH /api/config/senha`: requer `senha_atual` + `nova_senha`. Falha com 401 se `senha_atual` inválida. **Sem revogação de JWT no MVP** — tokens antigos continuam válidos. Contrato: comentário no service.
- `openpyxl` não está em `pyproject.toml` — adicionar em `dependencies`.
- Todos os endpoints requerem autenticação (`get_current_user`).

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  pyproject.toml                          # (modificar) adicionar openpyxl>=3.1

  src/
    schemas/
      config_schemas.py                   # (criar)
    repositories/
      estabelecimento_repository.py       # (modificar) adicionar upsert_estabelecimento
    services/
      config_service.py                   # (criar)
      backup_service.py                   # (criar)
    api/
      routes/
        config.py                         # (criar) 3 endpoints
        backup.py                         # (criar) 1 endpoint
  main.py                                 # (modificar) registrar 2 novos routers

  tests/
    test_configuracoes.py                 # (criar) 6 testes

frontend/
  src/
    features/
      configuracoes/
        useEstabelecimento.ts             # (criar)
        ConfiguracoesPage.tsx             # (criar) 4 abas
    App.tsx                               # (modificar) rota /configuracoes
```

---

## Tarefas

### Bloco A — Schemas (backend)

- [ ] **A1.** Criar `backend/src/schemas/config_schemas.py`:

```python
from typing import Optional

from pydantic import BaseModel


class EstabelecimentoResponse(BaseModel):
    id: int
    nome: str
    cnpj: Optional[str]
    endereco: Optional[str]
    telefone: Optional[str]

    model_config = {"from_attributes": True}


class EstabelecimentoUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str
```

---

### Bloco B — Repository (backend)

- [ ] **B1.** Modificar `backend/src/repositories/estabelecimento_repository.py` — adicionar `upsert_estabelecimento`:

```python
from typing import Optional

from sqlalchemy.orm import Session

from src.models.estabelecimento import Estabelecimento


def get_estabelecimento(db: Session) -> Optional[Estabelecimento]:
    return db.get(Estabelecimento, 1)


def upsert_estabelecimento(
    db: Session,
    nome: Optional[str] = None,
    cnpj: Optional[str] = None,
    endereco: Optional[str] = None,
    telefone: Optional[str] = None,
) -> Estabelecimento:
    est = db.get(Estabelecimento, 1)
    if est is None:
        est = Estabelecimento(id=1, nome=nome or "Estabelecimento")
        db.add(est)
    if nome is not None:
        est.nome = nome
    if cnpj is not None:
        est.cnpj = cnpj
    if endereco is not None:
        est.endereco = endereco
    if telefone is not None:
        est.telefone = telefone
    db.commit()
    db.refresh(est)
    return est
```

---

### Bloco C — Config Service (backend)

- [ ] **C1.** Criar `backend/src/services/config_service.py`:

```python
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import auth_repository, estabelecimento_repository
from src.schemas.config_schemas import (
    AlterarSenhaRequest,
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)
from src.services.auth_service import hash_password, verify_password


def get_estabelecimento(db: Session) -> EstabelecimentoResponse:
    est = estabelecimento_repository.get_estabelecimento(db)
    if est is None:
        return EstabelecimentoResponse(
            id=1, nome="Estabelecimento", cnpj=None, endereco=None, telefone=None
        )
    return EstabelecimentoResponse.model_validate(est)


def update_estabelecimento(
    db: Session, body: EstabelecimentoUpdate
) -> EstabelecimentoResponse:
    est = estabelecimento_repository.upsert_estabelecimento(
        db,
        nome=body.nome,
        cnpj=body.cnpj,
        endereco=body.endereco,
        telefone=body.telefone,
    )
    return EstabelecimentoResponse.model_validate(est)


def alterar_senha(db: Session, body: AlterarSenhaRequest) -> None:
    # MVP: sem revogação de JWT — tokens emitidos antes da troca continuam válidos.
    config = auth_repository.get_config(db)
    if config is None or not verify_password(body.senha_atual, config.senha_hash):
        raise AppError(
            code=ErrorCode.SENHA_INCORRETA,
            message="Senha atual incorreta",
            http_status=401,
        )
    auth_repository.upsert_config(db, hash_password(body.nova_senha))
```

---

### Bloco D — Backup Service (backend)

- [ ] **D1.** Criar `backend/src/services/backup_service.py`:

```python
import io
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import openpyxl
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from src.core.database import Base
from src.models.comandas import Comanda
from src.models.itens import Item
from src.models.movimentos_estoque import MovimentoEstoque


def _serialize(val: Any) -> Any:
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return str(val)
    return val


def backup_json(db: Session) -> bytes:
    result: dict[str, list] = {}
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        table = mapper.persist_selectable
        rows = db.execute(select(table)).mappings().all()
        result[table.name] = [{k: _serialize(v) for k, v in row.items()} for row in rows]
    return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")


def _table_rows(db: Session, cls: type) -> tuple[list[str], list[list]]:
    mapper = inspect(cls)
    cols = [c.key for c in mapper.mapper.columns]
    rows = db.execute(select(cls)).scalars().all()
    data = [[_serialize(getattr(r, c)) for c in cols] for r in rows]
    return cols, data


def backup_xlsx(db: Session) -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default sheet

    for sheet_name, cls in [
        ("comandas", Comanda),
        ("itens", Item),
        ("movimento_estoque", MovimentoEstoque),
    ]:
        cols, data = _table_rows(db, cls)
        ws = wb.create_sheet(title=sheet_name)
        ws.append(cols)
        for row in data:
            ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

---

### Bloco E — Routes (backend)

- [ ] **E1.** Criar `backend/src/api/routes/config.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.config_schemas import (
    AlterarSenhaRequest,
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)
from src.services import config_service

router = APIRouter()


@router.get("/estabelecimento", response_model=EstabelecimentoResponse)
def get_estabelecimento(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> EstabelecimentoResponse:
    return config_service.get_estabelecimento(db)


@router.patch("/estabelecimento", response_model=EstabelecimentoResponse)
def update_estabelecimento(
    body: EstabelecimentoUpdate,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> EstabelecimentoResponse:
    return config_service.update_estabelecimento(db, body)


@router.patch("/senha", status_code=204)
def alterar_senha(
    body: AlterarSenhaRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    config_service.alterar_senha(db, body)
```

- [ ] **E2.** Criar `backend/src/api/routes/backup.py`:

```python
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.core.errors import AppError, ErrorCode
from src.services import backup_service

router = APIRouter()


@router.get("")
def backup(
    formato: str = "json",
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> Response:
    if formato == "json":
        data = backup_service.backup_json(db)
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="backup.json"'},
        )
    if formato == "xlsx":
        data = backup_service.backup_xlsx(db)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="backup.xlsx"'},
        )
    raise AppError(
        code=ErrorCode.VALIDATION_ERROR,
        message="formato deve ser 'json' ou 'xlsx'",
        http_status=422,
    )
```

- [ ] **E3.** Modificar `backend/src/main.py` — adicionar imports e routers:

```python
from src.api.routes import backup as backup_routes
from src.api.routes import config as config_routes
# ...
app.include_router(config_routes.router, prefix="/api/config", tags=["config"])
app.include_router(backup_routes.router, prefix="/api/backup", tags=["backup"])
```

  Inserir após o router de `dashboard` (ordem alfabética: backup vem antes de categorias, config entre categorias e comandas).

---

### Bloco F — pyproject.toml

- [ ] **F1.** Adicionar `openpyxl>=3.1` em `dependencies` no `backend/pyproject.toml`.

---

### Bloco G — Tests (backend)

- [ ] **G1.** Criar `backend/tests/test_configuracoes.py` (6 testes):

  - `test_get_estabelecimento_defaults` — sem registro no banco → retorna defaults (`nome="Estabelecimento"`, campos opcionais `None`).
  - `test_patch_estabelecimento` — PATCH com `{"nome": "Bar do Ze", "telefone": "11999"}` → retorna campos atualizados.
  - `test_alterar_senha_senha_incorreta` — cria hash, chama PATCH senha com senha errada → 401.
  - `test_alterar_senha_sucesso` — cria hash, chama PATCH senha com senha correta → 204. Verifica que novo hash aceita nova senha.
  - `test_backup_json` — GET `/api/backup?formato=json` → status 200, content-type application/json, body é JSON válido com chave "estabelecimento".
  - `test_backup_xlsx` — GET `/api/backup?formato=xlsx` → status 200, content-type xlsx, body não vazio.

  **Padrão:** mesmo que `test_dashboard.py` — fixture `c`, `_fake_user`, engine SQLite em memória, `_setup_db` autouse.

  **Nota senha nos testes:** criar `ConfigSeguranca` diretamente com `hash_password("senha123")` antes de chamar o endpoint.

---

### Bloco H — Frontend: useEstabelecimento.ts

- [ ] **H1.** Criar `frontend/src/features/configuracoes/useEstabelecimento.ts`:

```ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface EstabelecimentoData {
  id: number;
  nome: string;
  cnpj: string | null;
  endereco: string | null;
  telefone: string | null;
}

export interface EstabelecimentoUpdate {
  nome?: string;
  cnpj?: string;
  endereco?: string;
  telefone?: string;
}

export function useEstabelecimento() {
  return useQuery<EstabelecimentoData>({
    queryKey: ["config", "estabelecimento"],
    queryFn: () =>
      api.get<EstabelecimentoData>("/api/config/estabelecimento").then((r) => r.data),
  });
}

export function useUpdateEstabelecimento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: EstabelecimentoUpdate) =>
      api.patch<EstabelecimentoData>("/api/config/estabelecimento", body).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["config", "estabelecimento"] }),
  });
}
```

---

### Bloco I — Frontend: ConfiguracoesPage.tsx

- [ ] **I1.** Criar `frontend/src/features/configuracoes/ConfiguracoesPage.tsx`:

  - **Tabs** (shadcn `Tabs`) com 4 abas: Estabelecimento | Senha | Impressora | Backup.
  - **Aba Estabelecimento:**
    - Formulário RHF+Zod com campos: Nome Fantasia (obrigatório), CNPJ, Endereço, Telefone.
    - Botão "Salvar" chama `PATCH /api/config/estabelecimento`. Toast verde sucesso / vermelho erro.
    - Preenche campos com `useEstabelecimento()` na montagem.
  - **Aba Senha:**
    - Formulário RHF com campos: Senha Atual (obrigatório), Nova Senha (obrigatório, min 4), Confirmar Nova Senha (deve igual nova).
    - Botão "Alterar Senha" chama `PATCH /api/config/senha`. Toast sucesso / erro (senha atual incorreta).
    - Limpa campos após sucesso.
  - **Aba Impressora:**
    - Conteúdo estático — instruções para configurar Obitech WD-80R7:
      1. Conecte a impressora via USB.
      2. Acesse Configurações do SO → Impressoras → Adicionar impressora.
      3. Selecione o driver Obitech WD-80R7 ou genérico de 80mm.
      4. Imprima página de teste pelo navegador (Ctrl+P, selecione a impressora).
      5. Sem integração técnica nesta versão.
  - **Aba Backup:**
    - Dois botões: "Exportar JSON" e "Exportar Excel".
    - Cada botão faz `GET /api/backup?formato=json|xlsx` e dispara download via `URL.createObjectURL`.
    - Loading state durante download. Toast erro se falhar.

---

### Bloco J — App.tsx

- [ ] **J1.** Modificar `frontend/src/App.tsx` — adicionar rota `/configuracoes`:

```tsx
import { ConfiguracoesPage } from "@/features/configuracoes/ConfiguracoesPage";
// Adicionar dentro de <AppLayout>:
<Route path="/configuracoes" element={<ConfiguracoesPage />} />
```

---

## Validações

### Backend
```bash
cd backend
pip install openpyxl
ruff check .
mypy src/
pytest tests/test_configuracoes.py -v
```

### Frontend
```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

---

## Critérios de Aceite

- [ ] `GET /api/config/estabelecimento` retorna dados (defaults se sem registro).
- [ ] `PATCH /api/config/estabelecimento` atualiza apenas os campos enviados (PATCH semântico).
- [ ] `PATCH /api/config/senha` com senha incorreta retorna 401.
- [ ] `PATCH /api/config/senha` com senha correta → 204, novo hash validado.
- [ ] `GET /api/backup?formato=json` retorna JSON com dump de todas as tabelas.
- [ ] `GET /api/backup?formato=xlsx` retorna arquivo .xlsx com 3 planilhas (comandas, itens, movimento_estoque).
- [ ] `GET /api/backup?formato=invalido` retorna 422.
- [ ] FE: aba Estabelecimento preenche form com dados atuais, salva com toast.
- [ ] FE: aba Senha altera senha com sucesso (toast verde), rejeita senha errada (toast vermelho).
- [ ] FE: aba Impressora exibe instruções estáticas.
- [ ] FE: aba Backup baixa arquivos JSON e XLSX via download.
- [ ] Testes: 6 cenários passando.

---

## Notas Importantes

- **openpyxl**: adicionar em `pyproject.toml` e instalar antes de rodar testes (`pip install openpyxl`).
- **Backup JSON `Base.registry.mappers`**: itera todos os mappers registrados. Inclui todas as tabelas automaticamente.
- **Download no FE**: usar `window.URL.createObjectURL(new Blob([response.data]))` com `responseType: 'blob'` no axios.
- **PATCH semântico**: `upsert_estabelecimento` só atualiza campos não-None. Campos omitidos na requisição ficam inalterados.
- **Revogação de JWT**: não implementada no MVP. Tokens anteriores à troca de senha continuam válidos. Documentado via comentário no `config_service.py`.
- **ErrorCode.VALIDATION_ERROR**: verificar se existe em `src/core/errors.py` antes de usar no backup route. Se não existir, usar `ErrorCode.VALIDATION_ERROR` ou lançar `HTTPException(status_code=422, detail="...")` diretamente.
