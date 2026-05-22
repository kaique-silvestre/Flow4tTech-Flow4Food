import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGarcons, type Garcom } from "@/features/cadastros/garcons/useGarcons";
import { GarcomModal } from "@/features/cadastros/garcons/GarcomModal";
import { novaComandaSchema, type NovaComandaValues } from "./comandaSchemas";
import { useAbrirComanda } from "./useComandas";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function NovaComandaModal({ open, onClose }: Props) {
  const { data: garcons = [] } = useGarcons();
  const garçonsAtivos = garcons.filter((g) => g.ativo);
  const abrirComanda = useAbrirComanda();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    getValues,
    formState: { errors },
  } = useForm<NovaComandaValues>({
    resolver: zodResolver(novaComandaSchema),
    defaultValues: { tipo_identificacao: "nome", pessoas: [] },
  });

  const [pessoaInput, setPessoaInput] = useState("");
  const [garcomModalOpen, setGarcomModalOpen] = useState(false);

  function handleGarcomCreated(garcom: Garcom) {
    setValue("garcom_id", garcom.id);
  }
  const pessoas = watch("pessoas");
  const tipo = watch("tipo_identificacao");
  const identificacao = watch("identificacao");
  const prevIdentificacaoRef = useRef("");

  useEffect(() => {
    if (tipo !== "nome") return;
    const raw = typeof identificacao === "string" ? identificacao : "";
    const trimmed = raw.trim();
    const prev = prevIdentificacaoRef.current;
    prevIdentificacaoRef.current = trimmed;
    const atual = getValues("pessoas") ?? [];
    const semPrev = prev ? atual.filter((p) => p !== prev) : atual;
    if (trimmed && !semPrev.includes(trimmed)) {
      setValue("pessoas", [trimmed, ...semPrev]);
    } else {
      setValue("pessoas", semPrev);
    }
  }, [tipo, identificacao, getValues, setValue]);

  function addPessoa() {
    const nome = pessoaInput.trim();
    if (!nome) return;
    setValue("pessoas", [...pessoas, nome]);
    setPessoaInput("");
  }

  function removePessoa(idx: number) {
    setValue(
      "pessoas",
      pessoas.filter((_, i) => i !== idx),
    );
  }

  function onSubmit(values: NovaComandaValues) {
    abrirComanda.mutate(values, { onSuccess: () => onClose() });
  }

  return (
    <>
    <GarcomModal
      open={garcomModalOpen}
      onClose={() => setGarcomModalOpen(false)}
      onCreated={handleGarcomCreated}
    />
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nova Comanda</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Tipo */}
          <div>
            <Label>Tipo de identificação</Label>
            <div className="mt-1 flex gap-4">
              {(["nome", "mesa"] as const).map((t) => (
                <div key={t} className="flex items-center gap-2">
                  <input
                    type="radio"
                    id={`tipo-identificacao-${t}`}
                    value={t}
                    {...register("tipo_identificacao")}
                  />
                  <label
                    htmlFor={`tipo-identificacao-${t}`}
                    className="text-sm cursor-pointer"
                  >
                    {t === "mesa" ? "Número da mesa" : "Nome do responsável"}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Identificação */}
          <div>
            <Label htmlFor="identificacao">Identificação</Label>
            <Input
              id="identificacao"
              type={tipo === "mesa" ? "number" : "text"}
              min={tipo === "mesa" ? 1 : undefined}
              step={tipo === "mesa" ? 1 : undefined}
              {...register("identificacao")}
              className="mt-1"
            />
            {errors.identificacao && (
              <p className="mt-1 text-xs text-red-500">{errors.identificacao.message}</p>
            )}
          </div>

          {/* Garçom */}
          <div>
            <Label htmlFor="garcom_id">Garçom</Label>
            <select
              id="garcom_id"
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              {...register("garcom_id", { valueAsNumber: true })}
            >
              <option value="">Selecione um garçom</option>
              {garçonsAtivos.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.nome}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="text-xs text-blue-600 hover:underline mt-0.5"
              onClick={() => setGarcomModalOpen(true)}
            >
              [ + Cadastrar novo garçom ]
            </button>
            {errors.garcom_id && (
              <p className="mt-1 text-xs text-red-500">{errors.garcom_id.message}</p>
            )}
          </div>

          {/* Pessoas */}
          <div>
            <Label>Pessoas</Label>
            <div className="mt-1 flex gap-2">
              <Input
                value={pessoaInput}
                onChange={(e) => setPessoaInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addPessoa())}
                placeholder="Nome da pessoa"
              />
              <Button type="button" variant="outline" onClick={addPessoa}>
                Adicionar
              </Button>
            </div>
            {pessoas.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {pessoas.map((p, i) => (
                  <span
                    key={i}
                    className="flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 text-sm"
                  >
                    {p}
                    <button
                      type="button"
                      onClick={() => removePessoa(i)}
                      className="text-gray-400 hover:text-gray-700"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
            {errors.pessoas && (
              <p className="mt-1 text-xs text-red-500">{errors.pessoas.message}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={abrirComanda.isPending}>
              {abrirComanda.isPending ? "Abrindo..." : "Abrir Comanda"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
    </>
  );
}
