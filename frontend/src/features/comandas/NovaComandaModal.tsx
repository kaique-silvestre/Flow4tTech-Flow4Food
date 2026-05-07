import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGarcons } from "@/features/cadastros/garcons/useGarcons";
import { novaComandaSchema, type NovaComandaValues } from "./comandaSchemas";
import { useAbrirComanda } from "./useComandas";

interface Props {
  onClose: () => void;
}

export function NovaComandaModal({ onClose }: Props) {
  const { data: garcons = [] } = useGarcons();
  const garçonsAtivos = garcons.filter((g) => g.ativo);
  const abrirComanda = useAbrirComanda();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<NovaComandaValues>({
    resolver: zodResolver(novaComandaSchema),
    defaultValues: { tipo_identificacao: "mesa", pessoas: [] },
  });

  const [pessoaInput, setPessoaInput] = useState("");
  const pessoas = watch("pessoas");

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Nova Comanda</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Tipo */}
          <div>
            <Label>Tipo de identificação</Label>
            <div className="mt-1 flex gap-4">
              {(["mesa", "nome"] as const).map((tipo) => (
                <label key={tipo} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="radio" value={tipo} {...register("tipo_identificacao")} />
                  {tipo === "mesa" ? "Número da mesa" : "Nome do responsável"}
                </label>
              ))}
            </div>
          </div>

          {/* Identificação */}
          <div>
            <Label htmlFor="identificacao">Identificação</Label>
            <Input id="identificacao" {...register("identificacao")} className="mt-1" />
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
            {errors.garcom_id && (
              <p className="mt-1 text-xs text-red-500">{errors.garcom_id.message}</p>
            )}
          </div>

          {/* Pessoas */}
          <div>
            <Label>Pessoas (opcional)</Label>
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
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={abrirComanda.isPending}>
              {abrirComanda.isPending ? "Abrindo..." : "Abrir Comanda"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
