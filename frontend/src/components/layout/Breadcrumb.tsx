import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useLocation, Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { NAV_ITEMS } from "./navConfig";
import { useAuthStore } from "@/stores/authStore";
import { decodeJwtPayload } from "@/lib/jwt";

interface BreadcrumbContextValue {
  label: string | undefined;
  setLabel: (label: string | undefined) => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue | null>(null);

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [label, setLabel] = useState<string | undefined>(undefined);
  const value = useMemo(() => ({ label, setLabel }), [label]);
  return <BreadcrumbContext.Provider value={value}>{children}</BreadcrumbContext.Provider>;
}

function useBreadcrumbContext(): BreadcrumbContextValue {
  const ctx = useContext(BreadcrumbContext);
  if (!ctx) throw new Error("useBreadcrumbContext must be used within a BreadcrumbProvider");
  return ctx;
}

/**
 * Lets any detail page (e.g. /cardapio/:id) publish the dynamic label for the
 * current route's breadcrumb. Pass `undefined` while the label hasn't loaded
 * yet (or the record wasn't found) — the breadcrumb then falls back to just
 * the parent nav item, no placeholder/flicker. Cleared automatically on unmount.
 */
export function useBreadcrumbLabel(label: string | undefined) {
  const { setLabel } = useBreadcrumbContext();
  useEffect(() => {
    setLabel(label);
    return () => setLabel(undefined);
  }, [label, setLabel]);
}

/**
 * Reads `tenant_name` straight off the JWT payload. `AuthUser` doesn't expose
 * this field (yet) — decoding locally here avoids depending on/duplicating
 * work on that shared type while it's under separate development.
 */
function useTenantName(): string | undefined {
  const token = useAuthStore((s) => s.token);
  return useMemo(() => {
    if (!token) return undefined;
    const payload = decodeJwtPayload<{ tenant_name?: string }>(token);
    return payload?.tenant_name;
  }, [token]);
}

export function Breadcrumb() {
  const { pathname } = useLocation();
  const { label } = useBreadcrumbContext();
  const tenantName = useTenantName();

  const crumbs = buildCrumbs(pathname, tenantName, label);
  if (crumbs.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-gray-400">
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1;
        return (
          <span key={crumb.label + i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={14} className="text-gray-300" />}
            {isLast ? (
              <span className="font-medium text-gray-700">{crumb.label}</span>
            ) : crumb.to ? (
              <Link to={crumb.to} className="hover:text-gray-600 transition-colors">
                {crumb.label}
              </Link>
            ) : (
              <span>{crumb.label}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}

interface Crumb {
  label: string;
  to?: string;
}

function matchesPath(itemPath: string, pathname: string): boolean {
  if (itemPath === "/") return pathname === "/";
  return pathname === itemPath || pathname.startsWith(itemPath + "/");
}

/**
 * Builds the topbar breadcrumb trail: always `[tenant_name]` (unrecognized
 * route) or `[tenant_name, page label]` (recognized route) — never a 3rd
 * segment, even for a group's subitem (the group itself is dropped, e.g.
 * "Estoque > Movimentos" becomes just `[tenant_name, "Movimentos"]").
 */
export function buildCrumbs(
  pathname: string,
  tenantName: string | undefined,
  dynamicLabel?: string
): Crumb[] {
  const company: Crumb = { label: tenantName ?? "" };

  // Check groups with children first (most specific match wins)
  for (const item of NAV_ITEMS) {
    if (item.children) {
      // Sort children by path length desc so /estoque/movimentos matches before /estoque
      const sorted = [...item.children].sort((a, b) => b.to.length - a.to.length);
      for (const child of sorted) {
        if (matchesPath(child.to, pathname)) {
          // Skip redundant "Compras > Compras" — show just "Compras"
          const pageLabel = item.label === child.label ? item.label : child.label;
          return [company, { label: pageLabel }];
        }
      }
    }

    // Direct link items — including root-level pages (Dashboard, Cardápio)
    if (item.to) {
      if (pathname === item.to) {
        return [company, { label: item.label }];
      }
      if (pathname.startsWith(item.to + "/")) {
        return [company, { label: dynamicLabel ?? item.label }];
      }
    }
  }

  // Unrecognized route — company name only, never an invented page label
  return [company];
}
