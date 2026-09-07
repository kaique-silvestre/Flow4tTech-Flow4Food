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
import { MetodoPagamentoModal } from "./MetodoPagamentoModal";
import { useDeleteMetodoPagamento, useMetodosPagamento, useToggleMetodoAtivo, type MetodoPagamento } from "./useMetodosPagamento";

type Filtro = "ativos" | "inativos" | "todos";

const POR_PAGINA = 10;

export function normalizarTexto(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

export function MetodosPagamentoPage() {
  const { data: metodos = [], isLoading } = useMetodosPagamento();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<MetodoPagamento | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("ativos");
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState(1);
  const [removendo, setRemovendo] = useState<MetodoPagamento | null>(null);
  const deleteMutation = useDeleteMetodoPagamento();
  const toggle = useToggleMetodoAtivo();

  const metodosFiltrados = metodos.filter((m) => {
    if (filtro === "ativos" && !m.ativo) return false;
    if (filtro === "inativos" && m.ativo) return false;
    if (busca && !normalizarTexto(m.nome).includes(normalizarTexto(busca))) return false;
    return true;
  });

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(m: MetodoPagamento) {
    setEditing(m);
    setModalOpen(true);
  }

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Métodos de Pagamento</h1>
        <Button onClick={openCreate}>Novo Método</Button>
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
          placeholder="Buscar método..."
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
      ) : metodosFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum método de pagamento encontrado.</p>
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
              {paginar(metodosFiltrados, pagina, POR_PAGINA).map((m) => (
                <TableRow key={m.id}>
                  <TableCell className={!m.ativo ? "text-gray-400 line-through" : ""}>
                    {m.nome}
                  </TableCell>
                  <TableCell>
                    {m.ativo ? (
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
                      <Button size="sm" variant="outline" onClick={() => openEdit(m)}>
                        Editar
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => toggle.mutate(m.id)}
                        disabled={m.padrao}
                        title={m.padrao ? "Método padrão não pode ser desativado" : undefined}
                        className={m.ativo ? "text-yellow-600 hover:text-yellow-700" : "text-green-600 hover:text-green-700"}
                      >
                        {m.ativo ? "Desativar" : "Ativar"}
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => setRemovendo(m)}
                        disabled={m.padrao}
                        title={m.padrao ? "Método padrão não pode ser removido" : undefined}
                      >
                        Remover
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
            totalPaginas={Math.ceil(metodosFiltrados.length / POR_PAGINA)}
            total={metodosFiltrados.length}
            label="métodos"
            onPageChange={setPagina}
          />
        </div>
      )}

      <MetodoPagamentoModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />

      <ConfirmDialog
        open={!!removendo}
        title="Remover método de pagamento?"
        description={`Tem certeza que deseja remover "${removendo?.nome}"? Esta ação não pode ser desfeita.`}
        confirmLabel="Remover"
        onConfirm={() => {
          if (!removendo) return;
          deleteMutation.mutate(removendo.id, { onSuccess: () => setRemovendo(null), onError: () => setRemovendo(null) });
        }}
        onCancel={() => setRemovendo(null)}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
