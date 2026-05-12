import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Pagination, paginar } from "@/components/ui/pagination";
import { GarcomModal } from "./GarcomModal";
import { GarcomComissoesModal } from "./GarcomComissoesModal";
import { useGarcons, useToggleGarcomAtivo, type Garcom } from "./useGarcons";

const POR_PAGINA = 8;

export function GarconsPage() {
  const { data: garcons = [], isLoading } = useGarcons();
  const toggle = useToggleGarcomAtivo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Garcom | null>(null);
  const [filtro, setFiltro] = useState<"ativos" | "inativos" | "todos">("ativos");
  const [pagina, setPagina] = useState(1);
  const [comissoesGarcom, setComissoesGarcom] = useState<Garcom | null>(null);

  const garconsFiltrados = garcons.filter((g) =>
    filtro === "todos" ? true : filtro === "ativos" ? g.ativo : !g.ativo
  );

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(g: Garcom) {
    setEditing(g);
    setModalOpen(true);
  }

  function openComissoes(g: Garcom) {
    setComissoesGarcom(g);
  }

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Garçons</h1>
        <Button onClick={openCreate}>Novo Garçom</Button>
      </div>

      <div className="mb-3 flex gap-1">
        {(["ativos", "inativos", "todos"] as const).map((f) => (
          <button
            key={f}
            onClick={() => { setFiltro(f); setPagina(1); }}
            className={`rounded border px-3 py-1 text-sm capitalize ${filtro === f ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : garconsFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum garçom encontrado.</p>
      ) : (
        <div className="flex-1 flex flex-col">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {paginar(garconsFiltrados, pagina, POR_PAGINA).map((g) => (
              <tr key={g.id} className="border-b last:border-0">
                <td className={`py-2 pr-4 ${!g.ativo ? "text-gray-400 line-through" : ""}`}>
                  {g.nome}
                </td>
                <td className="py-2 pr-4">
                  {g.ativo ? (
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
                      Ativo
                    </span>
                  ) : (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                      Inativo
                    </span>
                  )}
                </td>
                <td className="py-2 text-right space-x-2">
                  <Button size="sm" variant="outline" onClick={() => openComissoes(g)}>
                    Ver Comissões
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => openEdit(g)}>
                    Editar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toggle.mutate(g.id)}
                    className={g.ativo ? "text-yellow-600 hover:text-yellow-700" : "text-green-600 hover:text-green-700"}
                  >
                    {g.ativo ? "Desativar" : "Ativar"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex-1" />
        <Pagination
          pagina={pagina}
          totalPaginas={Math.ceil(garconsFiltrados.length / POR_PAGINA)}
          total={garconsFiltrados.length}
          label="garçons"
          onPageChange={setPagina}
        />
        </div>
      )}

      <GarcomModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />

      {comissoesGarcom && (
        <GarcomComissoesModal
          open={comissoesGarcom !== null}
          onClose={() => setComissoesGarcom(null)}
          garcom={comissoesGarcom}
        />
      )}
    </div>
  );
}
