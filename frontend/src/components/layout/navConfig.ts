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
  type LucideIcon,
} from "lucide-react";

export interface SubNavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  screen?: string;
}

export interface NavItem {
  label: string;
  to: string | null;
  icon?: LucideIcon;
  screen?: string;
  children?: SubNavItem[];
}

const VENDAS_CHILDREN: SubNavItem[] = [
  { label: "Comandas", to: "/vendas/comandas", icon: ClipboardList, screen: "comandas" },
  { label: "Consumo Interno", to: "/consumo-interno", icon: Coffee, screen: "consumo_interno" },
];

const COMPRAS_CHILDREN: SubNavItem[] = [
  { label: "Compras", to: "/compras", icon: ShoppingCart, screen: "compras" },
];

const ESTOQUE_CHILDREN: SubNavItem[] = [
  { label: "Estoque", to: "/estoque", icon: Package, screen: "estoque" },
  { label: "Movimentos", to: "/estoque/movimentos", icon: History, screen: "estoque" },
];

const FINANCEIRO_CHILDREN: SubNavItem[] = [
  { label: "Contas a Pagar", to: "/contas-pagar", icon: Wallet, screen: "compras" },
];

const RELATORIOS_CHILDREN: SubNavItem[] = [
  { label: "Vendas", to: "/relatorios/vendas", icon: ClipboardList, screen: "relatorios" },
  { label: "Compras", to: "/relatorios/compras", icon: ShoppingCart, screen: "relatorios" },
  { label: "Financeiro", to: "/relatorios/financeiro", icon: Wallet, screen: "relatorios" },
];

const CADASTROS_CHILDREN: SubNavItem[] = [
  { label: "Categorias", to: "/cadastros/categorias", icon: Tag, screen: "cadastros" },
  { label: "Insumos", to: "/cadastros/insumos", icon: FlaskConical, screen: "cadastros" },
  { label: "Fornecedores", to: "/cadastros/fornecedores", icon: Truck, screen: "cadastros" },
  { label: "Garçons", to: "/cadastros/garcons", icon: Users, screen: "cadastros" },
  { label: "Métodos Pgto.", to: "/cadastros/metodos-pagamento", icon: CreditCard, screen: "cadastros" },
];

const CONFIGURACOES_CHILDREN: SubNavItem[] = [
  { label: "Configurações Gerais", to: "/configuracoes/gerais", icon: Settings, screen: "configuracoes" },
  { label: "Usuários", to: "/configuracoes/usuarios", icon: Users, screen: "gestao_usuarios" },
];

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard, screen: "dashboard" },
  { label: "Cardápio", to: "/cardapio", icon: UtensilsCrossed, screen: "comandas" },
  { label: "Vendas", to: null, icon: ClipboardList, screen: "comandas", children: VENDAS_CHILDREN },
  { label: "Compras", to: null, icon: ShoppingCart, screen: "compras", children: COMPRAS_CHILDREN },
  { label: "Estoque", to: null, icon: Package, screen: "estoque", children: ESTOQUE_CHILDREN },
  { label: "Financeiro", to: null, icon: Wallet, screen: "compras", children: FINANCEIRO_CHILDREN },
  { label: "Relatórios", to: null, icon: BarChart3, screen: "relatorios", children: RELATORIOS_CHILDREN },
  { label: "Cadastros", to: null, icon: BookOpen, screen: "cadastros", children: CADASTROS_CHILDREN },
  { label: "Configurações", to: null, icon: Settings, children: CONFIGURACOES_CHILDREN },
];
