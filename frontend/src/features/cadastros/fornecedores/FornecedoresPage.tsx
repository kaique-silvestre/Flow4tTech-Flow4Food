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
import { FornecedorModal } from "./FornecedorModal";
import { useFornecedores, useToggleFornecedorAtivo, type Fornecedor } from "./useFornecedores";

type Filtro = "ativos" | "inativos" | "todos";

const POR_PAGINA = 10;

export function normalizarTexto(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

export function FornecedoresPage() {
  const { data, isLoading } = useFornecedores();
  const fornecedores = data?.itens ?? [];
  const toggleAtivo = useToggleFornecedorAtivo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Fornecedor | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("ativos");
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState(1);
  const [confirmId, setConfirmId] = useState<number | null>(null);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(f: Fornecedor) {
    setEditing(f);
    setModalOpen(true);
  }

  const fornecedoresFiltrados = fornecedores.filter((f) => {
    if (filtro === "ativos" && !f.ativo) return false;
    if (filtro === "inativos" && f.ativo) return false;
    if (busca && !normalizarTexto(f.nome).includes(normalizarTexto(busca))) return false;
    return true;
  });

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Fornecedores</h1>
        <Button onClick={openCreate}>Novo Fornecedor</Button>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
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
        <Input
          placeholder="Buscar fornecedor..."
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
      ) : fornecedoresFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum fornecedor encontrado.</p>
      ) : (
        <div className="flex-1 flex flex-col">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Nome</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead>Telefone</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="py-2" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginar(fornecedoresFiltrados, pagina, POR_PAGINA).map((f) => (
                <TableRow key={f.id}>
                  <TableCell className={!f.ativo ? "text-gray-400 line-through" : ""}>
                    {f.nome}
                  </TableCell>
                  <TableCell className="text-gray-600">{f.email ?? "—"}</TableCell>
                  <TableCell className="text-gray-600">{f.telefone ?? "—"}</TableCell>
                  <TableCell>
                    {f.ativo ? (
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
                      <Button size="sm" variant="outline" onClick={() => openEdit(f)}>
                        Editar
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => f.ativo ? setConfirmId(f.id) : toggleAtivo.mutate(f.id)}
                        disabled={toggleAtivo.isPending}
                        className={f.ativo ? "text-yellow-600 hover:text-yellow-700" : "text-green-600 hover:text-green-700"}
                      >
                        {f.ativo ? "Desativar" : "Reativar"}
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

      <ConfirmDialog
        open={confirmId !== null}
        title="Desativar fornecedor?"
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
