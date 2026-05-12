import { Button } from "./button";

interface PaginationProps {
  pagina: number;
  totalPaginas: number;
  total: number;
  label?: string;
  onPageChange: (p: number) => void;
}

export function Pagination({ pagina, totalPaginas, total, label = "itens", onPageChange }: PaginationProps) {
  if (totalPaginas <= 1) return null;
  return (
    <div className="mt-4 flex items-center justify-between text-sm">
      <Button size="sm" variant="outline" disabled={pagina <= 1} onClick={() => onPageChange(pagina - 1)}>
        ← Anterior
      </Button>
      <span className="text-gray-500">
        Página {pagina} de {totalPaginas} · {total} {label}
      </span>
      <Button size="sm" variant="outline" disabled={pagina >= totalPaginas} onClick={() => onPageChange(pagina + 1)}>
        Próximo →
      </Button>
    </div>
  );
}

/** Client-side pagination helper */
export function paginar<T>(items: T[], pagina: number, porPagina: number): T[] {
  const start = (pagina - 1) * porPagina;
  return items.slice(start, start + porPagina);
}
