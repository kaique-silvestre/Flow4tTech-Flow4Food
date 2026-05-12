import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Pagination, paginar } from "@/components/ui/pagination";
import { FornecedorModal } from "./FornecedorModal";
import { useFornecedores, useToggleFornecedorAtivo, type Fornecedor } from "./useFornecedores";

type Filtro = "ativos" | "inativos" | "todos";

const POR_PAGINA = 12;

export function FornecedoresPage() {
  const { data: fornecedores = [], isLoading } = useFornecedores();
  const toggleAtivo = useToggleFornecedorAtivo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Fornecedor | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("ativos");
  const [pagina, setPagina] = useState(1);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(f: Fornecedor) {
    setEditing(f);
    setModalOpen(true);
  }

  const fornecedoresFiltrados = fornecedores.filter((f) => {
    if (filtro === "ativos") return f.ativo;
    if (filtro === "inativos") return !f.ativo;
    return true;
  });

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Fornecedores</h1>
        <Button onClick={openCreate}>Novo Fornecedor</Button>
      </div>

      <div className="mb-3 flex gap-1">
        {(["ativos", "inativos", "todos"] as const).map((f) => (
          <button
            key={f}
            onClick={() => { setFiltro(f); setPagina(1); }}
            className={`rounded border px-3 py-1 text-sm ${
              filtro === f ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            {f === "ativos" ? "Ativos" : f === "inativos" ? "Inativos" : "Todos"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : fornecedoresFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum fornecedor encontrado.</p>
      ) : (
        <div>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 pr-4">Nome</th>
                <th className="py-2 pr-4">Telefone</th>
                <th className="py-2 pr-4">E-mail</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {paginar(fornecedoresFiltrados, pagina, POR_PAGINA).map((f) => (
                <tr key={f.id} className={`border-b last:border-0 ${!f.ativo ? "opacity-60" : ""}`}>
                  <td className={`py-2 pr-4 ${!f.ativo ? "text-gray-400 line-through" : ""}`}>
                    {f.nome}
                  </td>
                  <td className="py-2 pr-4 text-gray-600">{f.telefone ?? "—"}</td>
                  <td className="py-2 pr-4 text-gray-600">{f.email ?? "—"}</td>
                  <td className="py-2 text-right space-x-2">
                    <Button size="sm" variant="outline" onClick={() => openEdit(f)}>
                      Editar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => toggleAtivo.mutate(f.id)}
                      disabled={toggleAtivo.isPending}
                      className={f.ativo ? "text-yellow-600 hover:text-yellow-700" : "text-green-600 hover:text-green-700"}
                    >
                      {f.ativo ? "Desativar" : "Reativar"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination
            pagina={pagina}
            totalPaginas={Math.ceil(fornecedoresFiltrados.length / POR_PAGINA)}
            total={fornecedoresFiltrados.length}
            label="fornecedores"
            onPageChange={setPagina}
          />
        </div>
      )}

      <FornecedorModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />
    </div>
  );
}
