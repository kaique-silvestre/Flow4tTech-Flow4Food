import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { GarcomModal } from "./GarcomModal";
import { GarcomComissoesModal } from "./GarcomComissoesModal";
import { useGarcons, useToggleGarcomAtivo, type Garcom } from "./useGarcons";

type Filtro = "ativos" | "inativos" | "todos";

const POR_PAGINA = 8;

export function normalizarTexto(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

export function GarconsPage() {
  const { data, isLoading } = useGarcons();
  const garcons = data?.itens ?? [];
  const toggle = useToggleGarcomAtivo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Garcom | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("ativos");
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState(1);
  const [comissoesGarcom, setComissoesGarcom] = useState<Garcom | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);

  const garconsFiltrados = garcons.filter((g) => {
    if (filtro === "ativos" && !g.ativo) return false;
    if (filtro === "inativos" && g.ativo) return false;
    if (busca && !normalizarTexto(g.nome).includes(normalizarTexto(busca))) return false;
    return true;
  });

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

      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
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
        <Input
          placeholder="Buscar garçom..."
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
      ) : garconsFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum garçom encontrado.</p>
      ) : (
        <div className="flex-1 flex flex-col">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Nome</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="py-2" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginar(garconsFiltrados, pagina, POR_PAGINA).map((g) => (
              <TableRow key={g.id}>
                <TableCell className={!g.ativo ? "text-gray-400 line-through" : ""}>
                  {g.nome}
                </TableCell>
                <TableCell>
                  {g.ativo ? (
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
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button size="icon" variant="ghost" aria-label="Ações">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => openComissoes(g)}>
                        Ver Comissões
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => openEdit(g)}>
                        Editar
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => g.ativo ? setConfirmId(g.id) : toggle.mutate(g.id)}
                        className={g.ativo ? "text-yellow-600" : "text-green-600"}
                      >
                        {g.ativo ? "Desativar" : "Ativar"}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
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

      <ConfirmDialog
        open={confirmId !== null}
        title="Desativar garçom?"
        confirmLabel="Desativar"
        onConfirm={() => {
          toggle.mutate(confirmId!);
          setConfirmId(null);
        }}
        onCancel={() => setConfirmId(null)}
        isPending={toggle.isPending}
      />
    </div>
  );
}
