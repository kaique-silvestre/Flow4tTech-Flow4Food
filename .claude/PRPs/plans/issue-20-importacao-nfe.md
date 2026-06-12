# PRP — Issue #20: Importação Automática de NF-e XML para Compras

## Goal
Upload NF-e XML → parse → auto-match fornecedor/insumos → tela de revisão → confirmar cria compra normal.

## Schema Changes

### A1 — Migration: `cnpj` em `fornecedores`
- `0070_add_cnpj_to_fornecedores.py`
- `op.add_column("fornecedores", sa.Column("cnpj", sa.String(14), nullable=True))`
- PG guard not needed (plain add_column works on both)

### A2 — Migration: `ean` em `insumos`
- `0071_add_ean_to_insumos.py`
- `op.add_column("insumos", sa.Column("ean", sa.String(14), nullable=True))`

### A3 — Model `Fornecedor` — add `cnpj: Mapped[Optional[str]]`
### A4 — Model `Insumo` — add `ean: Mapped[Optional[str]]`
### A5 — Schema `FornecedorCreateRequest` / `FornecedorUpdateRequest` — add `cnpj: Optional[str] = None`
### A6 — Schema `InsumoCreateRequest` / `InsumoUpdateRequest` — add `ean: Optional[str] = None`
### A7 — Repo `fornecedores_repository.create` / `update` — persist `cnpj`
### A8 — Repo `insumos_repository.create` / `update` — persist `ean`

## Backend — NF-e Parser

### B1 — `src/services/nfe_parser.py`
Pure function. No DB access.

```python
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional
import xml.etree.ElementTree as ET

NS = "http://www.portalfiscal.inf.br/nfe"

@dataclass
class NFeItem:
    nome: str
    ean: Optional[str]
    quantidade: Decimal
    unidade_xml: str
    custo_unitario: Decimal
    custo_total: Decimal

@dataclass
class NFeData:
    numero_nota: str
    data_emissao: date
    cnpj_emitente: str
    nome_emitente: str
    itens: list[NFeItem] = field(default_factory=list)

UNIDADE_MAP = {"KG": "kg", "GR": "g", "G": "g", "UN": "un", "PC": "un", "CX": "un", "LT": "un", "L": "un"}

def parse_nfe(xml_bytes: bytes) -> NFeData: ...
```

- Parse namespace `{NS}nfeProc` or `{NS}NFe` root
- Extract `infNFe/ide/nNF`, `dhEmi`/`dEmi`, `emit/CNPJ`, `emit/xNome`
- Each `det/prod`: `xProd`, `cEAN` (None if "SEM GTIN"), `qCom`, `uCom`, `vUnCom`, `vProd`
- Raises `AppError(ErrorCode.VALIDATION_ERROR)` on bad XML

### B2 — `src/services/nfe_match_service.py`
Read-only DB queries.

```python
def match_nfe(db: Session, data: NFeData) -> NFeImportResponse: ...
```

- Fornecedor: `select(Fornecedor).where(Fornecedor.cnpj == data.cnpj_emitente)`
- Each item: match by EAN (`Insumo.ean == item.ean`), then by nome ilike (normalize accents with `unicodedata`)
- Returns `NFeImportResponse`

## Backend — Schemas

### C1 — `src/schemas/nfe.py`
```python
class NFeItemResponse(BaseModel):
    nome_xml: str
    ean_xml: Optional[str]
    quantidade: Decimal
    unidade_xml: str
    custo_unitario: Decimal
    custo_total: Decimal
    insumo_id: Optional[int]
    insumo_nome: Optional[str]

class NFeImportResponse(BaseModel):
    numero_nota: str
    data_compra: date
    cnpj_xml: str
    fornecedor_id: Optional[int]
    fornecedor_nome_xml: str
    itens: list[NFeItemResponse]
```

## Backend — Endpoint

### D1 — `POST /compras/importar-nfe` in `src/api/routes/compras.py`
```python
from fastapi import UploadFile, File

@router.post("/importar-nfe", response_model=NFeImportResponse)
def importar_nfe(
    file: UploadFile = File(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> NFeImportResponse:
    xml_bytes = file.file.read()
    data = nfe_parser.parse_nfe(xml_bytes)
    return nfe_match_service.match_nfe(db, data)
```

**NOTE:** Route `/importar-nfe` must be registered BEFORE `/{compra_id}` to avoid path conflict.

## Tests

### E1 — `tests/test_nfe_parser.py`
Pure unit tests — no DB, no client. Fixtures: synthetic XML strings.

Cases:
1. NF-e válida múltiplos itens → verifica count, numero_nota, cnpj, valores
2. Item com `cEAN = "SEM GTIN"` → `ean = None`
3. Unidades KG, GR, UN, CX → mapeamento correto
4. XML inválido (not XML) → raises AppError
5. XML sem namespace NF-e → raises AppError

### E2 — `tests/test_nfe_match.py`
SQLite in-memory tests following `test_compras.py` pattern.

Cases:
1. CNPJ bate → `fornecedor_id` correto
2. CNPJ não bate → `fornecedor_id = None`
3. EAN bate → `insumo_id` correto
4. Nome case-insensitive sem acento bate → `insumo_id` correto
5. Sem match → `insumo_id = None`

## Frontend

### F1 — `src/lib/api.ts` (or useCompras.ts) — add `useImportarNfe` hook
```ts
export function useImportarNfe() {
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const res = await api.post("/compras/importar-nfe", form);
      return res.data as NFeImportResponse;
    },
  });
}
```

Types:
```ts
export interface NFeItemResponse {
  nome_xml: string; ean_xml: string | null;
  quantidade: number; unidade_xml: string;
  custo_unitario: number; custo_total: number;
  insumo_id: number | null; insumo_nome: string | null;
}
export interface NFeImportResponse {
  numero_nota: string; data_compra: string;
  cnpj_xml: string; fornecedor_id: number | null;
  fornecedor_nome_xml: string;
  itens: NFeItemResponse[];
}
```

### F2 — `src/features/compras/ImportarNFeModal.tsx`
Estado 1: upload (drag-drop ou file picker `.xml`)
Estado 2: revisão
- Header: numero_nota, data_compra, fornecedor (select pré-selecionado ou vazio)
- Tabela itens: linha normal (insumo_id set) vs linha amarela "Novo"
- Cada linha: select insumo, quantidade editável, custo_total editável, botão × remove
- Itens sem insumo_id: botão "Criar insumo" → abre InsumoModal pré-preenchido
- Botão "Confirmar compra" disabled enquanto qualquer item sem insumo_id
- Ao confirmar: `POST /compras` com `tipo_compra: "imediata"` + itens resolvidos

### F3 — `src/features/compras/ComprasPage.tsx`
- Add botão "Importar NF-e" ao lado de "Nova Compra"
- Gerencia `showImportModal` state

## Validation Commands

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_nfe_parser.py tests/test_nfe_match.py -v
cd backend && source .venv/bin/activate && python -m pytest --tb=short -q
cd frontend && npm run type-check
cd frontend && npm run lint
```

## Checklist

- [ ] A1 migration 0070 cnpj fornecedores
- [ ] A2 migration 0071 ean insumos
- [ ] A3 Model Fornecedor cnpj
- [ ] A4 Model Insumo ean
- [ ] A5 Schema fornecedor cnpj
- [ ] A6 Schema insumo ean
- [ ] A7 Repo fornecedor persist cnpj
- [ ] A8 Repo insumo persist ean
- [ ] B1 nfe_parser.py
- [ ] B2 nfe_match_service.py
- [ ] C1 schemas/nfe.py
- [ ] D1 endpoint POST /compras/importar-nfe
- [ ] E1 test_nfe_parser.py
- [ ] E2 test_nfe_match.py
- [ ] F1 useImportarNfe hook + types
- [ ] F2 ImportarNFeModal.tsx
- [ ] F3 ComprasPage.tsx botão
- [ ] All tests pass
- [ ] Commit
