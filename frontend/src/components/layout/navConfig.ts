import {
  LayoutDashboard,
  ClipboardList,
  UtensilsCrossed,
  ShoppingCart,
  Package,
  History,
  BarChart3,
  Tag,
  Truck,
  Users,
  CreditCard,
  Settings,
  BookOpen,
  FlaskConical,
  Wallet,
  Coffee,
  CalendarDays,
  Percent,
  type LucideIcon,
} from "lucide-react";

export interface SubNavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  screen?: string;
  feature?: string;
}

export interface NavItem {
  label: string;
  to: string | null;
  icon?: LucideIcon;
  screen?: string;
  feature?: string;
  children?: SubNavItem[];
}

const VENDAS_CHILDREN: SubNavItem[] = [
  { label: "Comandas", to: "/vendas/comandas", icon: ClipboardList, screen: "comandas", feature: "comandas" },
  { label: "Consumo Interno", to: "/consumo-interno", icon: Coffee, screen: "consumo_interno", feature: "consumo_interno" },
];

const COMPRAS_CHILDREN: SubNavItem[] = [
  { label: "Compras", to: "/compras", icon: ShoppingCart, screen: "compras", feature: "compras" },
];

const ESTOQUE_CHILDREN: SubNavItem[] = [
  { label: "Estoque", to: "/estoque", icon: Package, screen: "estoque", feature: "estoque" },
  { label: "Movimentos", to: "/estoque/movimentos", icon: History, screen: "estoque", feature: "estoque" },
];

const FINANCEIRO_CHILDREN: SubNavItem[] = [
  { label: "Contas a Pagar", to: "/contas-pagar", icon: Wallet, screen: "compras", feature: "financeiro" },
];

const RELATORIOS_CHILDREN: SubNavItem[] = [
  { label: "Vendas", to: "/relatorios/vendas", icon: ClipboardList, screen: "relatorios", feature: "relatorios" },
  { label: "Compras", to: "/relatorios/compras", icon: ShoppingCart, screen: "relatorios", feature: "relatorios" },
  { label: "Financeiro", to: "/relatorios/financeiro", icon: Wallet, screen: "relatorios", feature: "relatorios" },
];

const CADASTROS_CHILDREN: SubNavItem[] = [
  { label: "Categorias", to: "/cadastros/categorias", icon: Tag, screen: "cadastros", feature: "cadastros" },
  { label: "Insumos", to: "/cadastros/insumos", icon: FlaskConical, screen: "cadastros", feature: "cadastros" },
  { label: "Fornecedores", to: "/cadastros/fornecedores", icon: Truck, screen: "cadastros", feature: "cadastros" },
  { label: "Garçons", to: "/cadastros/garcons", icon: Users, screen: "cadastros", feature: "cadastros" },
  { label: "Métodos Pgto.", to: "/cadastros/metodos-pagamento", icon: CreditCard, screen: "cadastros", feature: "cadastros" },
  { label: "Promoções", to: "/cadastros/promocoes", icon: Percent, screen: "cadastros", feature: "cadastros" },
];

const CONFIGURACOES_CHILDREN: SubNavItem[] = [
  { label: "Configurações Gerais", to: "/configuracoes/gerais", icon: Settings, screen: "configuracoes", feature: "configuracoes" },
  { label: "Usuários", to: "/configuracoes/usuarios", icon: Users, screen: "gestao_usuarios", feature: "gestao_usuarios" },
];

export interface NavGroup {
  /** Section label rendered above the group (uppercase, discreet style). Omitted for the top, ungrouped items. */
  heading?: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { label: "Dashboard", to: "/", icon: LayoutDashboard, screen: "dashboard", feature: "dashboard" },
      { label: "Calendário", to: "/calendario", icon: CalendarDays, screen: "calendario", feature: "calendario" },
    ],
  },
  {
    heading: "Operação",
    items: [
      { label: "Cardápio", to: "/cardapio", icon: UtensilsCrossed, screen: "comandas", feature: "comandas" },
      { label: "Vendas", to: null, icon: ClipboardList, screen: "comandas", feature: "comandas", children: VENDAS_CHILDREN },
      { label: "Compras", to: null, icon: ShoppingCart, screen: "compras", feature: "compras", children: COMPRAS_CHILDREN },
      { label: "Estoque", to: null, icon: Package, screen: "estoque", feature: "estoque", children: ESTOQUE_CHILDREN },
    ],
  },
  {
    heading: "Gestão",
    items: [
      { label: "Financeiro", to: null, icon: Wallet, screen: "compras", feature: "financeiro", children: FINANCEIRO_CHILDREN },
      { label: "Relatórios", to: null, icon: BarChart3, screen: "relatorios", feature: "relatorios", children: RELATORIOS_CHILDREN },
      { label: "Cadastros", to: null, icon: BookOpen, screen: "cadastros", feature: "cadastros", children: CADASTROS_CHILDREN },
    ],
  },
  {
    // "Configurações" stays in the main data set for now — it only moves out
    // to a fixed footer in a later ticket (06).
    items: [
      { label: "Configurações", to: null, icon: Settings, children: CONFIGURACOES_CHILDREN },
    ],
  },
];

/**
 * Flat view of all nav items, derived from NAV_GROUPS, preserving the same
 * order as before the grouping was introduced. Kept for consumers that only
 * need the flat list (e.g. Breadcrumb.tsx).
 */
export const NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((group) => group.items);

/**
 * Local, case-insensitive filter over nav groups by item `label`.
 *
 * - Empty (or whitespace-only) query returns every group/item unchanged.
 * - A parent item is kept if it matches itself, OR if any of its children
 *   match — in that case only the matching children are kept under it.
 * - A group left with no items after filtering is dropped entirely.
 *
 * Pure, 100% client-side — no network call, no debounce (the full list is
 * already in memory and small enough that filtering is effectively free).
 */
export function filterNavItems(query: string, groups: NavGroup[]): NavGroup[] {
  const q = query.trim().toLowerCase();
  if (!q) return groups;

  return groups
    .map((group) => {
      const items = group.items.reduce<NavItem[]>((acc, item) => {
        const selfMatches = item.label.toLowerCase().includes(q);
        if (selfMatches) {
          acc.push(item);
          return acc;
        }
        if (item.children) {
          const matchingChildren = item.children.filter((child) =>
            child.label.toLowerCase().includes(q),
          );
          if (matchingChildren.length > 0) {
            acc.push({ ...item, children: matchingChildren });
          }
        }
        return acc;
      }, []);

      return { heading: group.heading, items };
    })
    .filter((group) => group.items.length > 0);
}
