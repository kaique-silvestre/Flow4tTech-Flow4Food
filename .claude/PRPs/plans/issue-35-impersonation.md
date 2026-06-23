# Issue #35 — feat(platform): impersonation

## Context
Infrastructure for impersonation was partially built in issue #25. This plan fixes
the gaps to meet all acceptance criteria.

## What already exists (from #25)
- `POST /api/platform/tenants/{id}/users/{uid}/impersonate` endpoint — returns 2h JWT
- `handleImpersonate` + "Impersonar" button in `PlatformTenantDetailPage.tsx`
- `ImpersonationBanner` in `Topbar.tsx` (wrong text/nav)
- `AuditLog` model with `impersonated_by` field
- `useImpersonateUser` hook in `usePlatformApi.ts`

## Gaps to fix

### Backend
1. Add `impersonated_by_email` to impersonation JWT payload
   - File: `backend/src/api/routes/platform_auth.py` — `impersonate_user()`
   - `payload.get("email")` already has admin email (from platform token)

### Frontend
2. Fix impersonation flow — pass token via URL, not setToken (localStorage is shared!)
   - `PlatformTenantDetailPage.tsx` `handleImpersonate`: remove `setToken`, open
     `/?impersonation_token=${access_token}` in new tab
   - Change button text "Impersonar" → "Entrar como"

3. App.tsx — handle `?impersonation_token=` on load
   - Detect param, store in `sessionStorage`, clean URL (replaceState)

4. `lib/api.ts` — prefer sessionStorage impersonation_token over zustand store
   - In request interceptor: check `sessionStorage.getItem("impersonation_token")` first

5. `components/auth/RequireAuth.tsx` — allow impersonation sessionStorage token as auth
   - If `sessionStorage.getItem("impersonation_token")` exists → treat as authenticated

6. `Topbar.tsx` `ImpersonationBanner` — fix text, button, exit behavior
   - Read sessionStorage token, decode for `impersonated_by_email`
   - Show: "Sessão de suporte ativa — {email}"
   - Button: "Encerrar sessão de suporte"
   - Exit: `sessionStorage.removeItem("impersonation_token")` + `window.close()` or
     navigate to "/"

## Acceptance criteria checklist
- [ ] JWT has `impersonated_by_email`
- [ ] Button text "Entrar como"
- [ ] Clicking opens new tab with impersonation token (admin session unaffected)
- [ ] App in new tab authenticates via sessionStorage impersonation token
- [ ] Banner shows "Sessão de suporte ativa — {admin_email}"
- [ ] Button "Encerrar sessão de suporte" exits + clears token
- [ ] Middleware (get_current_user) exposes `impersonated_by` in payload dict ✅ (already works)

## Validations
- `cd frontend && npm run type-check && npm run lint && npm run build`
- `cd backend && uv run ruff check && uv run pytest -x -q`
