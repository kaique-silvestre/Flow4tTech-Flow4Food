# PRP: Issue #30 — Comunicados (broadcast e direcionados)

## Goal
Platform admin cria avisos (título, mensagem, expiração, alvo). Usuários veem banner não intrusivo no Topbar. Marcar como lido oculta banner. Admin vê contagem de leituras.

## Acceptance Criteria
- [ ] Migration 0072: `platform_announcements`, `announcement_targets`, `announcement_reads`
- [ ] Models: PlatformAnnouncement, AnnouncementTarget, AnnouncementRead
- [ ] Repository: list_active_for_user, list_with_read_counts, create, mark_read
- [ ] Endpoint `GET /api/platform/announcements` — lista com read_count (platform admin)
- [ ] Endpoint `POST /api/platform/announcements` — criar (platform admin)
- [ ] Endpoint `GET /api/app/announcements` — ativos não lidos (app user)
- [ ] Endpoint `POST /api/app/announcements/{id}/read` — marcar como lido (app user)
- [ ] Register routes in main.py
- [ ] Frontend: `PlatformAnnouncementsPage.tsx` com lista + modal criar
- [ ] Frontend: `useAnnouncements.ts` hook app-side
- [ ] Frontend: `ComunicadoBanner` em `Topbar.tsx`
- [ ] Route `/platform/announcements` em `App.tsx`
- [ ] Tests: pytest + frontend type-check + lint + build

## DB Schema

```sql
platform_announcements (
  id SERIAL PK,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE,
  target VARCHAR(20) NOT NULL DEFAULT 'all',  -- 'all' | 'specific'
  is_active BOOL NOT NULL DEFAULT true,
  created_by INT REFERENCES platform_admins(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)

announcement_targets (
  id SERIAL PK,
  announcement_id INT REFERENCES platform_announcements(id) ON DELETE CASCADE,
  tenant_id INT NOT NULL
)

announcement_reads (
  id SERIAL PK,
  announcement_id INT REFERENCES platform_announcements(id) ON DELETE CASCADE,
  user_id INT NOT NULL,
  tenant_id INT NOT NULL,
  read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(announcement_id, user_id)
)
```

## Implementation Steps

### A — Backend DB Layer
- A1: Migration 0072
- A2: Models (platform_announcements.py)
- A3: Schemas (announcements.py)
- A4: Repository (announcements_repository.py)

### B — Backend Routes
- B1: Platform routes (GET list + POST create) in platform_auth.py or new file
- B2: App routes (GET active + POST read) — new file or in existing app routes
- B3: Register in main.py

### C — Backend Tests
- C1: pytest tests for repository + routes

### D — Frontend
- D1: `usePlatformApi.ts` — add announcement types + hooks
- D2: `PlatformAnnouncementsPage.tsx`
- D3: `useAnnouncements.ts` app-side
- D4: `ComunicadoBanner` in `Topbar.tsx`
- D5: Route in `App.tsx`

### E — Validations
- E1: pytest
- E2: type-check + lint + build

## Key Patterns
- Platform routes: `dependencies=[Depends(require_platform_admin)]`, `db: Session = Depends(get_platform_db)`
- App routes: `payload: dict = Depends(get_current_user)`, read platform tables via `get_platform_db`
- Models: NO `from __future__ import annotations`, use `Optional[X]`
- PK: `mapped_column(primary_key=True)` sem tipo explícito
- Migration: last is 0071, next is 0072
- `platform_announcements` → same Base (alembic migrates it)
