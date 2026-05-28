import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MoneyInput } from "@/components/ui/money-input";
import { formatCurrency, formatDate } from "@/lib/format";
import {
  useSessaoAberta,
  useAbrirCaixa,
  useFecharCaixa,
  useRegistrarMovimento,
  type CaixaSessao,
} from "./useCaixa";

type ViewState = "turno" | "fechando" | "resultado";

const abrirSchema = z.object({
  valor_abertura: z.number({ invalid_type_error: "Informe o valor" }).min(0),
});
type AbrirValues = z.infer<typeof abrirSchema>;

const fecharSchema = z.object({
  valor_informado: z.number({ invalid_type_error: "Informe o valor" }).min(0),
  observacao: z.string().optional(),
});
type FecharValues = z.infer<typeof fecharSchema>;

const movimentoSchema = z.object({
  tipo: z.enum(["sangria", "suprimento"]),
  valor: z.number({ invalid_type_error: "Informe o valor" }).positive("Valor deve ser positivo"),
  motivo: z.string().min(1, "Informe o motivo"),
});
type MovimentoValues = z.infer<typeof movimentoSchema>;

function AberturaCaixa() {
  const { mutate: abrir, isPending } = useAbrirCaixa();
  const { handleSubmit, setValue, formState: { errors } } = useForm<AbrirValues>({
    resolver: zodResolver(abrirSchema),
    defaultValues: { valor_abertura: 0 },
  });

  return (
    <div className="max-w-sm mx-auto mt-10 border rounded-lg p-6 space-y-4">
      <h2 className="text-lg font-semibold">Abrir Caixa</h2>
      <form onSubmit={handleSubmit((d) => abrir(d.valor_abertura))} className="space-y-4">
        <div className="space-y-1">
          <Label htmlFor="valor_abertura">Fundo de troco (R$)</Label>
          <MoneyInput
            id="valor_abertura"
            onValueChange={(raw) => setValue("valor_abertura", raw ? parseFloat(raw) : 0)}
          />
          {errors.valor_abertura && (
            <p className="text-xs text-destructive">{errors.valor_abertura.message}</p>
          )}
        </div>
        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending ? "Abrindo..." : "Abrir Caixa"}
        </Button>
      </form>
    </div>
  );
}

function MovimentoForm({ onClose }: { onClose: () => void }) {
  const { mutate: registrar, isPending } = useRegistrarMovimento();
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<MovimentoValues>({
    resolver: zodResolver(movimentoSchema),
    defaultValues: { tipo: "sangria", valor: 0, motivo: "" },
  });
  const tipo = watch("tipo");

  function onSubmit(data: MovimentoValues) {
    registrar(data, { onSuccess: onClose });
  }

  return (
    <div className="border rounded-lg p-4 space-y-3 bg-gray-50">
      <h3 className="font-medium">Registrar Movimento</h3>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        <div className="flex gap-3">
          {(["sangria", "suprimento"] as const).map((t) => (
            <label key={t} className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                value={t}
                checked={tipo === t}
                onChange={() => setValue("tipo", t)}
                className="accent-blue-600"
              />
              <span className="text-sm capitalize">{t}</span>
            </label>
          ))}
        </div>
        <div className="space-y-1">
          <Label htmlFor="mov_valor">Valor (R$)</Label>
          <MoneyInput
            id="mov_valor"
            onValueChange={(raw) => setValue("valor", raw ? parseFloat(raw) : 0)}
          />
          {errors.valor && <p className="text-xs text-destructive">{errors.valor.message}</p>}
        </div>
        <div className="space-y-1">
          <Label htmlFor="mov_motivo">Motivo</Label>
          <Input id="mov_motivo" {...register("motivo")} placeholder="Descreva o motivo" />
          {errors.motivo && <p className="text-xs text-destructive">{errors.motivo.message}</p>}
        </div>
        <div className="flex gap-2 justify-end">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" size="sm" disabled={isPending}>
            {isPending ? "Salvando..." : "Confirmar"}
          </Button>
        </div>
      </form>
    </div>
  );
}

function TurnoAtivo({
  sessao,
  onFechar,
}: {
  sessao: CaixaSessao;
  onFechar: () => void;
}) {
  const [movimentoOpen, setMovimentoOpen] = useState(false);

  const sangrias = sessao.movimentos.filter((m) => m.tipo === "sangria");
  const suprimentos = sessao.movimentos.filter((m) => m.tipo === "suprimento");

  return (
    <div className="max-w-2xl mx-auto space-y-5 p-4 lg:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Caixa Aberto</h1>
          <p className="text-sm text-gray-500">
            Aberto em {formatDate(sessao.opened_at)} · Fundo:{" "}
            {formatCurrency(sessao.valor_abertura)}
          </p>
        </div>
        <Button variant="destructive" onClick={onFechar}>
          Fechar Caixa
        </Button>
      </div>

      {movimentoOpen ? (
        <MovimentoForm onClose={() => setMovimentoOpen(false)} />
      ) : (
        <Button variant="outline" onClick={() => setMovimentoOpen(true)}>
          + Sangria / Suprimento
        </Button>
      )}

      {sessao.movimentos.length > 0 && (
        <div className="border rounded-lg divide-y">
          <div className="px-4 py-2 bg-gray-50 text-sm font-medium text-gray-600">
            Movimentos do turno
          </div>
          {sessao.movimentos.map((m) => (
            <div key={m.id} className="flex items-center justify-between px-4 py-3 text-sm">
              <div>
                <span
                  className={`inline-block w-20 font-medium ${
                    m.tipo === "sangria" ? "text-red-600" : "text-green-600"
                  }`}
                >
                  {m.tipo === "sangria" ? "Sangria" : "Suprimento"}
                </span>
                <span className="text-gray-600">{m.motivo}</span>
              </div>
              <div className="flex flex-col items-end gap-0.5">
                <span
                  className={`font-medium ${
                    m.tipo === "sangria" ? "text-red-600" : "text-green-600"
                  }`}
                >
                  {m.tipo === "sangria" ? "-" : "+"}
                  {formatCurrency(m.valor)}
                </span>
                <span className="text-xs text-gray-400">{formatDate(m.created_at)}</span>
              </div>
            </div>
          ))}
          <div className="flex justify-between px-4 py-2 text-sm bg-gray-50">
            <span className="text-gray-600">
              Suprimentos: {formatCurrency(suprimentos.reduce((s, m) => s + Number(m.valor), 0))} ·
              Sangrias: {formatCurrency(sangrias.reduce((s, m) => s + Number(m.valor), 0))}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function FechamentoCaixa({
  sessao,
  onCancel,
  onFechado,
}: {
  sessao: CaixaSessao;
  onCancel: () => void;
  onFechado: (fechada: CaixaSessao) => void;
}) {
  const { mutate: fechar, isPending } = useFecharCaixa();
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FecharValues>({
    resolver: zodResolver(fecharSchema),
    defaultValues: { valor_informado: 0, observacao: "" },
  });

  function onSubmit(data: FecharValues) {
    fechar(data, { onSuccess: (fechada) => onFechado(fechada) });
  }

  return (
    <div className="max-w-sm mx-auto mt-6 border rounded-lg p-6 space-y-4">
      <h2 className="text-lg font-semibold">Fechar Caixa</h2>
      <div className="text-sm text-gray-600 space-y-1">
        <div className="flex justify-between">
          <span>Fundo de abertura:</span>
          <span>{formatCurrency(sessao.valor_abertura)}</span>
        </div>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1">
          <Label htmlFor="valor_informado">Valor contado na gaveta (R$)</Label>
          <MoneyInput
            id="valor_informado"
            onValueChange={(raw) => setValue("valor_informado", raw ? parseFloat(raw) : 0)}
          />
          {errors.valor_informado && (
            <p className="text-xs text-destructive">{errors.valor_informado.message}</p>
          )}
        </div>
        <div className="space-y-1">
          <Label htmlFor="observacao">Observação (opcional)</Label>
          <Input id="observacao" {...register("observacao")} placeholder="Observações do fechamento" />
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" className="flex-1" onClick={onCancel}>
            Cancelar
          </Button>
          <Button type="submit" className="flex-1" disabled={isPending}>
            {isPending ? "Fechando..." : "Confirmar"}
          </Button>
        </div>
      </form>
    </div>
  );
}

function ResultadoFechamento({
  sessao,
  onNovaTurno,
}: {
  sessao: CaixaSessao;
  onNovaTurno: () => void;
}) {
  const diferenca = Number(sessao.diferenca ?? 0);
  const isPositivo = diferenca > 0;
  const isNegativo = diferenca < 0;

  return (
    <div className="max-w-sm mx-auto mt-6 border rounded-lg p-6 space-y-4">
      <h2 className="text-lg font-semibold">Fechamento Concluído</h2>
      <p className="text-sm text-gray-500">
        Fechado em {sessao.closed_at ? formatDate(sessao.closed_at) : "—"}
      </p>

      <div className="border rounded-lg divide-y text-sm">
        <div className="flex justify-between px-3 py-2">
          <span className="text-gray-600">Fundo de abertura</span>
          <span>{formatCurrency(sessao.valor_abertura)}</span>
        </div>
        <div className="flex justify-between px-3 py-2">
          <span className="text-gray-600">Valor esperado</span>
          <span className="font-medium">{formatCurrency(sessao.valor_esperado ?? 0)}</span>
        </div>
        <div className="flex justify-between px-3 py-2">
          <span className="text-gray-600">Valor contado</span>
          <span className="font-medium">{formatCurrency(sessao.valor_informado ?? 0)}</span>
        </div>
        <div
          className={`flex justify-between px-3 py-2 font-semibold ${
            isPositivo
              ? "text-green-600 bg-green-50"
              : isNegativo
              ? "text-red-600 bg-red-50"
              : "text-gray-700"
          }`}
        >
          <span>{isPositivo ? "Sobra" : isNegativo ? "Quebra" : "Diferença"}</span>
          <span>
            {isPositivo ? "+" : ""}
            {formatCurrency(Math.abs(diferenca))}
          </span>
        </div>
      </div>

      {sessao.observacao && (
        <p className="text-sm text-gray-600">
          <span className="font-medium">Observação:</span> {sessao.observacao}
        </p>
      )}

      <Button className="w-full" onClick={onNovaTurno}>
        Iniciar Novo Turno
      </Button>
    </div>
  );
}

export function CaixaPage() {
  const { data: sessao, isLoading } = useSessaoAberta();
  const [view, setView] = useState<ViewState>("turno");
  const [sessaoFechada, setSessaoFechada] = useState<CaixaSessao | null>(null);

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-48 bg-gray-200 animate-pulse rounded" />
        <div className="h-32 w-full max-w-sm bg-gray-200 animate-pulse rounded" />
      </div>
    );
  }

  if (sessaoFechada) {
    return (
      <ResultadoFechamento
        sessao={sessaoFechada}
        onNovaTurno={() => setSessaoFechada(null)}
      />
    );
  }

  if (!sessao) {
    return <AberturaCaixa />;
  }

  if (view === "fechando") {
    return (
      <FechamentoCaixa
        sessao={sessao}
        onCancel={() => setView("turno")}
        onFechado={(fechada) => {
          setSessaoFechada(fechada);
          setView("turno");
        }}
      />
    );
  }

  return (
    <TurnoAtivo
      sessao={sessao}
      onFechar={() => setView("fechando")}
    />
  );
}
