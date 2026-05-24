import { useState, useEffect } from "react";
import { Button } from "./button";

interface PaginationProps {
  pagina: number;
  totalPaginas: number;
  total: number;
  label?: string;
  onPageChange: (p: number) => void;
}

export function Pagination({ pagina, totalPaginas, total, label = "itens", onPageChange }: PaginationProps) {
  const [inputVal, setInputVal] = useState(String(pagina));

  useEffect(() => {
    setInputVal(String(pagina));
  }, [pagina]);

  if (totalPaginas <= 1) return null;

  function commitInput() {
    const n = parseInt(inputVal, 10);
    if (!isNaN(n) && n >= 1 && n <= totalPaginas) {
      onPageChange(n);
    } else {
      setInputVal(String(pagina));
    }
  }

  return (
    <div className="sticky bottom-0 bg-white border-t border-gray-100 mt-4 py-2 flex items-center justify-between text-sm">
      <span className="text-gray-400 text-xs">{total} {label}</span>

      <div className="flex items-center gap-1">
        <Button
          size="sm"
          variant="outline"
          disabled={pagina <= 1}
          onClick={() => onPageChange(pagina - 1)}
        >
          ← Anterior
        </Button>

        <div className="flex items-center gap-1 px-1">
          <input
            type="number"
            min={1}
            max={totalPaginas}
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onBlur={commitInput}
            onKeyDown={(e) => { if (e.key === "Enter") commitInput(); }}
            className="w-12 rounded border border-gray-300 px-1.5 py-1 text-center text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
          />
          <span className="text-gray-400">/ {totalPaginas}</span>
        </div>

        <Button
          size="sm"
          variant="outline"
          disabled={pagina >= totalPaginas}
          onClick={() => onPageChange(pagina + 1)}
        >
          Próximo →
        </Button>
      </div>

      <span className="text-gray-400 text-xs invisible select-none">{total} {label}</span>
    </div>
  );
}

/** Client-side pagination helper */
export function paginar<T>(items: T[], pagina: number, porPagina: number): T[] {
  const start = (pagina - 1) * porPagina;
  return items.slice(start, start + porPagina);
}
