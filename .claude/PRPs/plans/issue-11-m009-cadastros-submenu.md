# PRP — Issue #11: M009 Submenu de Cadastros no Sidebar

**Type:** AFK
**Status:** Planejado
**Criado em:** 2026-05-08
**Depende de:** Issue 4 (M000) ✓, Issue 3 (M015) ✓

---

## Objetivo

Transformar a seção "Cadastros" no Sidebar de um separador estático + links diretos em um dropdown expansível.  
No estado colapsado, hover no ícone de Cadastros exibe submenu flutuante.  
Remover rota `/cadastros/itens` de `App.tsx` se existir.

---

## Estado Atual

`Sidebar.tsx` tem:
- `{ label: "─ Cadastros ─", to: null }` — separador estático
- Seguido por: Categorias, Fornecedores, Garçons, Métodos Pgto., Configurações como itens planos

Precisa virar:
- Item "Cadastros" com ícone `BookOpen` (ou `FolderOpen`) que abre/fecha submenu
- Submenu com: Categorias, Fornecedores, Garçons, Métodos Pgto.
- "Configurações" fica fora do submenu (mantém link direto)
- No estado colapsado: hover no ícone de Cadastros → popover/div flutuante com os subitens

---

## Estrutura de Arquivos a Modificar

```
frontend/src/components/layout/Sidebar.tsx   # (modificar) — dropdown para Cadastros
```

---

## Tarefas

### A — Sidebar.tsx: refatorar para suportar submenu

**A1.** Adicionar estado `cadastrosOpen: boolean` (useState, default `true`).

**A2.** Mudar o tipo `NavItem` para suportar `children?: SubNavItem[]`:
```ts
interface SubNavItem {
  label: string;
  to: string;
  icon?: LucideIcon;
}

interface NavItem {
  label: string;
  to: string | null;
  icon?: LucideIcon;
  children?: SubNavItem[];
}
```

**A3.** Adicionar `BookOpen` (ou `FolderOpen`) ao import de lucide-react.

**A4.** Substituir o separador `"─ Cadastros ─"` e os 4 links de cadastros por um único item com `children`:
```ts
{
  label: "Cadastros",
  to: null,
  icon: BookOpen,
  children: [
    { label: "Categorias", to: "/cadastros/categorias", icon: Tag },
    { label: "Fornecedores", to: "/cadastros/fornecedores", icon: Truck },
    { label: "Garçons", to: "/cadastros/garcons", icon: Users },
    { label: "Métodos Pgto.", to: "/cadastros/metodos-pagamento", icon: CreditCard },
  ],
},
```

**A5.** Lógica de render no estado **expandido**:
- Item com `children` renderiza como botão (não NavLink) que faz toggle de `cadastrosOpen`
- Botão mostra: ícone + "Cadastros" + chevron (ChevronDown/ChevronRight conforme estado)
- Quando `cadastrosOpen === true`: renderizar subitens com indentação (`pl-6`)
- Cada subitem é NavLink normal com `end`

**A6.** Lógica de render no estado **colapsado**:
- Mostrar apenas ícone de Cadastros
- `onMouseEnter` no container → estado local `hoveredCadastros = true`
- `onMouseLeave` no container → `hoveredCadastros = false`
- Quando `hoveredCadastros`: render div absoluta flutuante à direita do sidebar com os 4 subitens
- Cada subitem no popover: NavLink com ícone + texto

**A7.** Adicionar `ChevronDown` e `ChevronRight` ao import de lucide-react.

**A8.** Remover os ícones `Tag`, `Truck`, `Users`, `CreditCard` do array `NAV_ITEMS` antigo (eles ficam no `children`). Verificar que ainda são importados.

---

## Critérios de Aceite

- [ ] Clicar em "Cadastros" expande submenu com: Categorias, Fornecedores, Garçons, Métodos Pgto.
- [ ] "Itens" não aparece no submenu
- [ ] Navegar para `/cadastros/categorias` destaca link "Categorias" (e apenas ele)
- [ ] No estado colapsado: hover no ícone de Cadastros exibe submenu flutuante
- [ ] Rota `/cadastros/itens` não existe em `App.tsx` (verificar — já não existe)
- [ ] Configurações permanece como link direto fora do submenu

---

## Validações

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```
