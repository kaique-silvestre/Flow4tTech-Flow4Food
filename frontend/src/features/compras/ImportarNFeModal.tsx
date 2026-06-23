import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { useInsumos, type InsumoResponse } from "@/features/estoque/useInsumos";
import { useFornecedores } from "@/features/cadastros/fornecedores/useFornecedores";
import { useCreateCompra, useImportarNfe, type NFeImportResponse, type NFeItemResponse } from "./useCompras";
import { InsumoModal } from "./InsumoModal";
import { formatCurrency } from "@/lib/format";
import type { CompraFormValues } from "./compraSchemas";

interface RevisaoItem extends NFeItemResponse {
  insumo_id: number | null;
  insumo_nome: string | null;
  quantidade: number;
  custo_total: number;
  _removed?: boolean;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ImportarNFeModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);

  const [fase, setFase] = useState<"upload" | "revisao">("upload");
  const [nfeResp, setNfeResp] = useState<NFeImportResponse | null>(null);
  const [itens, setItens] = useState<RevisaoItem[]>([]);
  const [fornecedorId, setFornecedorId] = useState<string>("");
  const [novoInsumoIdx, setNovoInsumoIdx] = useState<number | null>(null);

  const importarMutation = useImportarNfe();
  const criarCompraMutation = useCreateCompra();

  const { data: insumosData } = useInsumos();
  const insumos = insumosData?.itens ?? [];
  const { data: fornecedoresData } = useFornecedores();
  const fornecedores = fornecedoresData?.itens ?? [];

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    importarMutation.mutate(file, {
      onSuccess: (resp) => {
        setNfeResp(resp);
        setFornecedorId(resp.fornecedor_id != null ? String(resp.fornecedor_id) : "");
        setItens(resp.itens.map((it) => ({ ...it })));
        setFase("revisao");
      },
    });
    e.target.value = "";
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    importarMutation.mutate(file, {
      onSuccess: (resp) => {
        setNfeResp(resp);
        setFornecedorId(resp.fornecedor_id != null ? String(resp.fornecedor_id) : "");
        setItens(resp.itens.map((it) => ({ ...it })));
        setFase("revisao");
      },
    });
  }

  function setItemField<K extends keyof RevisaoItem>(idx: number, key: K, value: RevisaoItem[K]) {
    setItens((prev) => prev.map((it, i) => (i === idx ? { ...it, [key]: value } : it)));
  }

  function removeItem(idx: number) {
    setItens((prev) => prev.filter((_, i) => i !== idx));
  }

  function handleInsumoSelect(idx: number, insumoId: string) {
    const found = insumos.find((i) => String(i.id) === insumoId);
    setItens((prev) =>
      prev.map((it, i) =>
        i === idx
          ? { ...it, insumo_id: found?.id ?? null, insumo_nome: found?.nome ?? null }
          : it
      )
    );
  }

  function handleInsumoCreated(idx: number, insumo: InsumoResponse) {
    qc.invalidateQueries({ queryKey: ["insumos"] });
    setItens((prev) =>
      prev.map((it, i) =>
        i === idx ? { ...it, insumo_id: insumo.id, insumo_nome: insumo.nome } : it
      )
    );
    setNovoInsumoIdx(null);
  }

  const itensPendentes = itens.filter((it) => it.insumo_id == null);
  const podeConfirmar = itensPendentes.length === 0 && itens.length > 0;

  function handleConfirmar() {
    if (!nfeResp) return;
    const payload: CompraFormValues = {
      fornecedor_id: fornecedorId ? Number(fornecedorId) : undefined,
      data_compra: nfeResp.data_compra,
      numero_nota: nfeResp.numero_nota || undefined,
      tipo_compra: "imediata",
      itens: itens.map((it) => ({
        item_id: it.insumo_id!,
        quantidade: it.quantidade,
        custo_total: it.custo_total,
      })),
    };
    criarCompraMutation.mutate(payload, { onSuccess: handleClose });
  }

  function handleClose() {
    setFase("upload");
    setNfeResp(null);
    setItens([]);
    setFornecedorId("");
    setNovoInsumoIdx(null);
    onClose();
  }

  const insumoParaNovoModal = novoInsumoIdx != null ? itens[novoInsumoIdx] : null;

  return (
    <>
      <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Importar NF-e XML</DialogTitle>
          </DialogHeader>

          {fase === "upload" && (
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-blue-400 transition-colors"
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileRef.current?.click()}
            >
              {importarMutation.isPending ? (
                <p className="text-gray-500">Processando XML...</p>
              ) : (
                <>
                  <p className="text-gray-600 font-medium">Arraste o XML da NF-e aqui</p>
                  <p className="text-sm text-gray-400 mt-1">ou clique para selecionar o arquivo (.xml)</p>
                </>
              )}
              <input
                ref={fileRef}
                type="file"
                accept=".xml,text/xml,application/xml"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
          )}

          {fase === "revisao" && nfeResp && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm bg-gray-50 rounded p-3">
                <div>
                  <span className="text-gray-500">Nº Nota:</span>{" "}
                  <span className="font-medium">{nfeResp.numero_nota || "—"}</span>
                </div>
                <div>
                  <span className="text-gray-500">Data emissão:</span>{" "}
                  <span className="font-medium">
                    {new Date(nfeResp.data_compra + "T00:00:00").toLocaleDateString("pt-BR")}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Emitente:</span>{" "}
                  <span className="font-medium">{nfeResp.fornecedor_nome_xml}</span>
                </div>
                <div>
                  <span className="text-gray-500">CNPJ:</span>{" "}
                  <span className="font-medium">{nfeResp.cnpj_xml}</span>
                </div>
                <div className="col-span-2">
                  <label className="text-gray-500 block mb-0.5">Fornecedor cadastrado:</label>
                  <select
                    className="w-full rounded border px-2 py-1.5 text-sm"
                    value={fornecedorId}
                    onChange={(e) => setFornecedorId(e.target.value)}
                  >
                    <option value="">— Nenhum —</option>
                    {fornecedores.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.nome}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {itensPendentes.length > 0 && (
                <p className="text-sm text-amber-600">
                  {itensPendentes.length} item(ns) sem insumo associado — associe antes de confirmar.
                </p>
              )}

              <div className="space-y-2">
                {itens.map((it, idx) => {
                  const semMatch = it.insumo_id == null;
                  return (
                    <div
                      key={idx}
                      className={`rounded border p-3 text-sm ${semMatch ? "border-amber-300 bg-amber-50" : "border-gray-200 bg-white"}`}
                    >
                      <div className="flex items-start gap-2">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            {semMatch && (
                              <span className="text-xs bg-amber-200 text-amber-800 rounded px-1.5 py-0.5 font-medium">
                                Novo
                              </span>
                            )}
                            <span className="font-medium text-gray-700">{it.nome_xml}</span>
                            {it.ean_xml && (
                              <span className="text-xs text-gray-400">EAN: {it.ean_xml}</span>
                            )}
                          </div>

                          <div className="grid grid-cols-3 gap-2">
                            <div>
                              <label className="text-xs text-gray-500 block">Insumo</label>
                              <select
                                className="w-full rounded border px-2 py-1 text-sm"
                                value={it.insumo_id != null ? String(it.insumo_id) : ""}
                                onChange={(e) => handleInsumoSelect(idx, e.target.value)}
                              >
                                <option value="">— Selecione —</option>
                                {insumos.map((ins) => (
                                  <option key={ins.id} value={ins.id}>
                                    {ins.nome}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <label className="text-xs text-gray-500 block">Qtd ({it.unidade_xml})</label>
                              <input
                                type="number"
                                min="0.001"
                                step="any"
                                className="w-full rounded border px-2 py-1 text-sm"
                                value={it.quantidade}
                                onChange={(e) => setItemField(idx, "quantidade", Number(e.target.value))}
                              />
                            </div>
                            <div>
                              <label className="text-xs text-gray-500 block">Custo total</label>
                              <input
                                type="number"
                                min="0.01"
                                step="any"
                                className="w-full rounded border px-2 py-1 text-sm"
                                value={it.custo_total}
                                onChange={(e) => setItemField(idx, "custo_total", Number(e.target.value))}
                              />
                            </div>
                          </div>

                          {semMatch && (
                            <button
                              type="button"
                              className="text-xs text-blue-600 hover:underline"
                              onClick={() => setNovoInsumoIdx(idx)}
                            >
                              + Criar insumo "{it.nome_xml}"
                            </button>
                          )}
                        </div>

                        <div className="text-right shrink-0">
                          <div className="text-sm font-medium">{formatCurrency(it.custo_total)}</div>
                          <button
                            type="button"
                            className="text-gray-400 hover:text-red-500 text-lg leading-none mt-1"
                            onClick={() => removeItem(idx)}
                            title="Remover item"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <DialogFooter className="gap-2">
            {fase === "revisao" && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setFase("upload");
                  setNfeResp(null);
                  setItens([]);
                }}
              >
                Trocar arquivo
              </Button>
            )}
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancelar
            </Button>
            {fase === "revisao" && (
              <Button
                type="button"
                disabled={!podeConfirmar || criarCompraMutation.isPending}
                onClick={handleConfirmar}
              >
                {criarCompraMutation.isPending ? "Salvando..." : "Confirmar compra"}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {novoInsumoIdx != null && insumoParaNovoModal && (
        <InsumoModal
          open={true}
          onClose={() => setNovoInsumoIdx(null)}
          onSuccess={(insumo) => handleInsumoCreated(novoInsumoIdx, insumo)}
          initialNome={insumoParaNovoModal.nome_xml}
          initialUnidade={insumoParaNovoModal.unidade_xml as "un" | "g" | "kg"}
        />
      )}
    </>
  );
}
