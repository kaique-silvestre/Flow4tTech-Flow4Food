# Matchpoint Frontend

React + Vite + TypeScript + Tailwind + TanStack Query + Zustand + RHF/Zod + shadcn/ui + sonner.

## Setup

Requisitos: Node 18+.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Abre em `http://localhost:5173`.

## Comandos

| Comando | Ação |
|---------|------|
| `npm run dev` | Vite dev server |
| `npm run build` | Build produção (`tsc -b && vite build`) |
| `npm run lint` | ESLint |
| `npm run type-check` | `tsc --noEmit` |
| `npm run test` | Vitest |
| `npm run preview` | Preview do build |

## Estrutura

```
src/
├── pages/        # rotas top-level
├── features/     # lógica + componentes por feature
├── components/ui # shadcn primitives
├── hooks/
├── stores/       # zustand
├── schemas/      # zod
└── lib/          # api, format, queryClient, sentry, utils
```

Resolução mínima suportada: 1280×720.
