# Issue 8 — Rebranding Flow4Food

**Objetivo:** Substituir todas referências "Matchpoint" por "Flow4Food"/"Flow4Tech".

## Arquivos e mudanças

| Arquivo | Mudança |
|---------|---------|
| `frontend/index.html` | `<title>Matchpoint</title>` → `<title>Flow4Food</title>` |
| `backend/src/main.py` | `title="Matchpoint API"` → `title="Flow4Food API"` |
| `frontend/src/pages/PlaceholderPage.tsx` | `"Matchpoint MVP"` → `"Flow4Food"` |
| `frontend/src/features/auth/LoginPage.tsx` | h1 "Flow4Tech" → "Flow4Food" + subtitle "por Flow4Tech" |
| `frontend/src/components/layout/Topbar.tsx` | `Flow4Tech` → `Flow4Food` |
| `frontend/src/features/auth/EsqueciSenhaPage.tsx` | h1 "Flow4Tech" → "Flow4Food" |
| `frontend/src/features/auth/RedefinirSenhaPage.tsx` | h1 "Flow4Tech" → "Flow4Food" (2 ocorrências) |
| `backend/src/services/auth_service.py` | Corpo do email: adicionar referência "Flow4Food — Flow4Tech" |
| `backend/src/core/logging.py` | `get_logger("matchpoint")` → `get_logger("flow4food")` |

## Acceptance criteria mapeado

- [x] `<title>` em `index.html` exibe "Flow4Food"
- [x] Card de login exibe "Flow4Food" e "por Flow4Tech"
- [x] Topbar exibe "Flow4Food"
- [x] Páginas auth referenciam Flow4Food/Flow4Tech
- [x] PlaceholderPage sem "Matchpoint"
- [x] `main.py`: `title="Flow4Food API"`
- [x] Email corpo referencia Flow4Food/Flow4Tech
- [x] Busca "Matchpoint" → 0 resultados em arquivos de produto
