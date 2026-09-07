import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Pagination, paginar } from "@/components/ui/pagination";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { InsumoEditModal } from "./InsumoEditModal";
import {
  useAllInsumos,
  useToggleInsumoAtivo,
  type InsumoResponse,
} from "@/features/estoque/useInsumos";

type Filtro = "ativos" | "inativos" | "todos";

const POR_PAGINA = 12;

export function normalizarTexto(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

export function InsumosPage() {
  const { data, isLoading, isError } = useAllInsumos();
  const insumos = data?.itens ?? [];
  const toggleAtivo = useToggleInsumoAtivo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<InsumoResponse | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("ativos");
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState(1);
  const [confirmId, setConfirmId] = useState<number | null>(null);

  const insumosFiltrados = insumos.filter((i) => {
    if (filtro === "ativos" && !i.ativo) return false;
    if (filtro === "inativos" && i.ativo) return false;
    if (busca && !normalizarTexto(i.nome).includes(normalizarTexto(busca))) return false;
    return true;
  });

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(i: InsumoResponse) {
    setEditing(i);
    setModalOpen(true);
  }

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Insumos</h1>
        <Button onClick={openCreate}>Novo Insumo</Button>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
          {(["ativos", "inativos", "todos"] as const).map((f) => (
            <button
              key={f}
              onClick={() => { setFiltro(f); setPagina(1); }}
              className={`rounded border px-3 py-1 text-sm capitalize ${
                filtro === f ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <Input
          placeholder="Buscar insumo..."
          value={busca}
          onChange={(e) => { setBusca(e.target.value); setPagina(1); }}
          className="w-full sm:w-52 text-sm"
        />
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-sm text-red-500">Erro ao carregar insumos. Tente novamente.</p>
      ) : insumosFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum insumo encontrado.</p>
      ) : (
        <div className="flex-1 flex flex-col">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Nome</TableHead>
              <TableHead className="text-right">Estoque</TableHead>
              <TableHead>Unidade</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="py-2" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginar(insumosFiltrados, pagina, POR_PAGINA).map((insumo) => (
              <TableRow key={insumo.id}>
                <TableCell className={!insumo.ativo ? "text-gray-400 line-through" : ""}>
                  {insumo.nome}
                </TableCell>
                <TableCell className="text-right text-gray-600">
                  {insumo.unidade_base === "kg"
                    ? Number(insumo.estoque_atual).toFixed(3)
                    : Math.round(Number(insumo.estoque_atual)).toString()}
                </TableCell>
                <TableCell className="text-gray-600">{insumo.unidade_base}</TableCell>
                <TableCell>
                  {insumo.ativo ? (
                    <Badge variant="outline" className="border-green-200 bg-green-100 text-green-700">
                      Ativo
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="border-gray-200 bg-gray-100 text-gray-500">
                      Inativo
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEdit(insumo)}>
                      Editar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => insumo.ativo ? setConfirmId(insumo.id) : toggleAtivo.mutate(insumo.id)}
                      disabled={toggleAtivo.isPending}
                    >
                      {insumo.ativo ? "Desativar" : "Reativar"}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="flex-1" />
        <Pagination
          pagina={pagina}
          totalPaginas={Math.ceil(insumosFiltrados.length / POR_PAGINA)}
          total={insumosFiltrados.length}
          label="insumos"
          onPageChange={setPagina}
        />
        </div>
      )}

      <InsumoEditModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />

      <ConfirmDialog
        open={confirmId !== null}
        title="Desativar insumo?"
        confirmLabel="Desativar"
        onConfirm={() => {
          toggleAtivo.mutate(confirmId!);
          setConfirmId(null);
        }}
        onCancel={() => setConfirmId(null)}
        isPending={toggleAtivo.isPending}
      />
    </div>
  );
}
