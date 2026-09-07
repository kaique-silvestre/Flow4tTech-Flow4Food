import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import type { Categoria } from "@/features/cadastros/categorias/useCategorias";

/** Builds "Pai > Filho" display paths for every category id in the tree. */
export function buildCategoryPaths(tree: Categoria[], prefix = ""): Record<number, string> {
  const result: Record<number, string> = {};
  for (const cat of tree) {
    const path = prefix ? `${prefix} > ${cat.nome}` : cat.nome;
    result[cat.id] = path;
    if (cat.children?.length) {
      Object.assign(result, buildCategoryPaths(cat.children, path));
    }
  }
  return result;
}

/** Collects the id plus all descendant ids for a given category (used to filter by parent). */
export function collectIds(id: number, tree: Categoria[]): Set<number> {
  const ids = new Set<number>([id]);
  for (const c of tree) {
    if (c.id === id) {
      for (const ch of c.children ?? []) {
        ids.add(ch.id);
        for (const gch of ch.children ?? []) ids.add(gch.id);
      }
    } else {
      for (const ch of c.children ?? []) {
        if (ch.id === id) {
          for (const gch of ch.children ?? []) ids.add(gch.id);
        }
      }
    }
  }
  return ids;
}

interface CategoriaFilterPopoverProps {
  categorias: Categoria[];
  catPathMap: Record<number, string>;
  value: number | null;
  onChange: (id: number | null) => void;
  expandidos: Set<number>;
  onToggleExpand: (id: number) => void;
}

export function CategoriaFilterPopover({
  categorias,
  catPathMap,
  value,
  onChange,
  expandidos,
  onToggleExpand,
}: CategoriaFilterPopoverProps) {
  const [open, setOpen] = useState(false);
  const label = value !== null ? catPathMap[value] ?? "Todas as categorias" : "Todas as categorias";

  function select(id: number | null) {
    onChange(id);
    setOpen(false);
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="justify-between gap-2 font-normal text-gray-700"
        >
          {label}
          <ChevronDown size={14} className="text-gray-400" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        className={cn("w-64 p-1", "motion-reduce:!animate-none motion-reduce:!duration-0")}
      >
        <div className="max-h-72 overflow-y-auto">
          <button
            type="button"
            onClick={() => select(null)}
            className={cn(
              "flex w-full items-center rounded px-2 py-1.5 text-left text-sm hover:bg-gray-100",
              value === null && "bg-gray-100 font-medium",
            )}
          >
            Todas as categorias
          </button>

          {categorias.map((cat) => {
            const expandido = expandidos.has(cat.id);
            const temFilhos = (cat.children?.length ?? 0) > 0;

            return (
              <div key={cat.id}>
                <div className="flex items-center">
                  {temFilhos ? (
                    <button
                      type="button"
                      onClick={() => onToggleExpand(cat.id)}
                      className="p-1 text-gray-400 hover:text-gray-700"
                      aria-label={`${expandido ? "Recolher" : "Expandir"} ${cat.nome}`}
                    >
                      {expandido ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>
                  ) : (
                    <span className="inline-block w-6" />
                  )}
                  <button
                    type="button"
                    onClick={() => select(cat.id)}
                    className={cn(
                      "flex-1 rounded px-2 py-1.5 text-left text-sm font-medium hover:bg-gray-100",
                      value === cat.id && "bg-gray-100",
                    )}
                  >
                    {cat.nome}
                  </button>
                </div>

                {expandido &&
                  cat.children?.map((sub) => (
                    <button
                      key={sub.id}
                      type="button"
                      onClick={() => select(sub.id)}
                      className={cn(
                        "block w-full rounded py-1.5 pl-8 pr-2 text-left text-sm font-normal text-gray-500 hover:bg-gray-100",
                        value === sub.id && "bg-gray-100",
                      )}
                    >
                      {sub.nome}
                    </button>
                  ))}
              </div>
            );
          })}
        </div>
      </PopoverContent>
    </Popover>
  );
}
