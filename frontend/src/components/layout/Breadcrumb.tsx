import { useLocation, Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { NAV_ITEMS } from "./navConfig";

export function Breadcrumb() {
  const { pathname } = useLocation();

  const crumbs = buildCrumbs(pathname);
  if (crumbs.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-gray-400 mb-4">
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

function buildCrumbs(pathname: string): Crumb[] {
  // Check groups with children first (most specific match wins)
  for (const item of NAV_ITEMS) {
    if (item.children) {
      // Sort children by path length desc so /estoque/movimentos matches before /estoque
      const sorted = [...item.children].sort((a, b) => b.to.length - a.to.length);
      for (const child of sorted) {
        if (matchesPath(child.to, pathname)) {
          // Skip redundant "Compras > Compras" — show just "Compras"
          if (item.label === child.label) {
            return [{ label: item.label }];
          }
          return [
            { label: item.label },
            { label: child.label, to: child.to },
          ];
        }
      }
    }

    // Direct link items — skip root-level pages (Dashboard, Cardápio)
    if (item.to && matchesPath(item.to, pathname)) {
      return [];
    }
  }

  return [];
}
