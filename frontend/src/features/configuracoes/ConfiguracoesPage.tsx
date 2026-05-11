import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "@/lib/toast";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useEstabelecimento, useUpdateEstabelecimento } from "./useEstabelecimento";

type Tab = "estabelecimento" | "senha" | "impressora" | "backup";

const TABS: { id: Tab; label: string }[] = [
  { id: "estabelecimento", label: "Estabelecimento" },
  { id: "senha", label: "Senha" },
  { id: "impressora", label: "Impressora" },
  { id: "backup", label: "Backup" },
];

function maskCnpj(v: string): string {
  const d = v.replace(/\D/g, "").slice(0, 14);
  return d
    .replace(/^(\d{2})(\d)/, "$1.$2")
    .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1/$2")
    .replace(/(\d{4})(\d)/, "$1-$2");
}

function maskTelefone(v: string): string {
  const d = v.replace(/\D/g, "").slice(0, 11);
  if (d.length <= 10) {
    return d
      .replace(/^(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }
  return d
    .replace(/^(\d{2})(\d)/, "($1) $2")
    .replace(/(\d{5})(\d)/, "$1-$2");
}

const estSchema = z.object({
  nome: z.string().min(1, "Nome obrigatório"),
  cnpj: z.string().optional().refine(
    (v) => !v || /^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/.test(v),
    { message: "CNPJ inválido" }
  ),
  endereco: z.string().optional(),
  telefone: z.string().optional().refine(
    (v) => !v || /^\(\d{2}\) \d{4,5}-\d{4}$/.test(v),
    { message: "Telefone inválido" }
  ),
});

const senhaSchema = z
  .object({
    senha_atual: z.string().min(1, "Obrigatório"),
    nova_senha: z.string().min(4, "Mínimo 4 caracteres"),
    confirmar: z.string().min(1, "Obrigatório"),
  })
  .refine((d) => d.nova_senha === d.confirmar, {
    message: "Senhas não conferem",
    path: ["confirmar"],
  });

type EstForm = z.infer<typeof estSchema>;
type SenhaForm = z.infer<typeof senhaSchema>;

function TabEstabelecimento() {
  const { data, isLoading } = useEstabelecimento();
  const update = useUpdateEstabelecimento();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<EstForm>({
    resolver: zodResolver(estSchema),
    values: {
      nome: data?.nome ?? "Estabelecimento",
      cnpj: data?.cnpj ?? "",
      endereco: data?.endereco ?? "",
      telefone: data?.telefone ?? "",
    },
  });

  function onSubmit(d: EstForm) {
    update.mutate(
      { nome: d.nome, cnpj: d.cnpj || undefined, endereco: d.endereco || undefined, telefone: d.telefone || undefined },
      {
        onSuccess: () => toast.success("Dados salvos"),
        onError: () => toast.error("Erro ao salvar"),
      }
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
        ))}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-md space-y-4">
      <div className="space-y-1">
        <Label htmlFor="nome">Nome Fantasia</Label>
        <Input id="nome" {...register("nome")} />
        {errors.nome && <p className="text-sm text-red-500">{errors.nome.message}</p>}
      </div>
      <div className="space-y-1">
        <Label htmlFor="cnpj">CNPJ</Label>
        <Controller
          name="cnpj"
          control={control}
          render={({ field }) => (
            <Input
              id="cnpj"
              placeholder="00.000.000/0000-00"
              value={field.value ?? ""}
              onChange={(e) => field.onChange(maskCnpj(e.target.value))}
            />
          )}
        />
        {errors.cnpj && <p className="text-sm text-red-500">{errors.cnpj.message}</p>}
      </div>
      <div className="space-y-1">
        <Label htmlFor="endereco">Endereço</Label>
        <Input id="endereco" {...register("endereco")} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="telefone">Telefone</Label>
        <Controller
          name="telefone"
          control={control}
          render={({ field }) => (
            <Input
              id="telefone"
              placeholder="(11) 99999-9999"
              value={field.value ?? ""}
              onChange={(e) => field.onChange(maskTelefone(e.target.value))}
            />
          )}
        />
        {errors.telefone && <p className="text-sm text-red-500">{errors.telefone.message}</p>}
      </div>
      <Button type="submit" disabled={update.isPending}>
        {update.isPending ? "Salvando..." : "Salvar"}
      </Button>
    </form>
  );
}

function TabSenha() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SenhaForm>({ resolver: zodResolver(senhaSchema) });

  async function onSubmit(d: SenhaForm) {
    try {
      await api.patch("/api/config/senha", {
        senha_atual: d.senha_atual,
        nova_senha: d.nova_senha,
      });
      toast.success("Senha alterada com sucesso");
      reset();
    } catch {
      toast.error("Senha atual incorreta");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-md space-y-4">
      <div className="space-y-1">
        <Label htmlFor="senha_atual">Senha Atual</Label>
        <Input id="senha_atual" type="password" {...register("senha_atual")} />
        {errors.senha_atual && <p className="text-sm text-red-500">{errors.senha_atual.message}</p>}
      </div>
      <div className="space-y-1">
        <Label htmlFor="nova_senha">Nova Senha</Label>
        <Input id="nova_senha" type="password" {...register("nova_senha")} />
        {errors.nova_senha && <p className="text-sm text-red-500">{errors.nova_senha.message}</p>}
      </div>
      <div className="space-y-1">
        <Label htmlFor="confirmar">Confirmar Nova Senha</Label>
        <Input id="confirmar" type="password" {...register("confirmar")} />
        {errors.confirmar && <p className="text-sm text-red-500">{errors.confirmar.message}</p>}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Alterando..." : "Alterar Senha"}
      </Button>
    </form>
  );
}

function TabImpressora() {
  return (
    <div className="max-w-md space-y-4">
      <p className="text-sm text-gray-600">
        Configure a impressora térmica Obitech WD-80R7 no sistema operacional:
      </p>
      <ol className="space-y-2 text-sm text-gray-700">
        <li className="flex gap-2">
          <span className="font-semibold text-gray-900">1.</span>
          Conecte a impressora via USB ao computador.
        </li>
        <li className="flex gap-2">
          <span className="font-semibold text-gray-900">2.</span>
          Acesse Configurações do SO → Dispositivos → Impressoras e scanners → Adicionar impressora.
        </li>
        <li className="flex gap-2">
          <span className="font-semibold text-gray-900">3.</span>
          Selecione o driver Obitech WD-80R7 ou use o driver genérico para impressora de 80mm.
        </li>
        <li className="flex gap-2">
          <span className="font-semibold text-gray-900">4.</span>
          Imprima uma página de teste: no navegador pressione Ctrl+P e selecione a impressora configurada.
        </li>
        <li className="flex gap-2">
          <span className="font-semibold text-gray-900">5.</span>
          Sem integração técnica nesta versão — impressão via diálogo do navegador.
        </li>
      </ol>
    </div>
  );
}

function TabBackup() {
  const [loadingJson, setLoadingJson] = useState(false);
  const [loadingXlsx, setLoadingXlsx] = useState(false);

  async function download(formato: "json" | "xlsx") {
    const setLoading = formato === "json" ? setLoadingJson : setLoadingXlsx;
    setLoading(true);
    try {
      const r = await api.get(`/api/backup?formato=${formato}`, { responseType: "blob" });
      const ext = formato === "json" ? "json" : "xlsx";
      const url = URL.createObjectURL(new Blob([r.data as BlobPart]));
      const a = document.createElement("a");
      a.href = url;
      const today = new Date().toISOString().slice(0, 10);
      a.download = `backup_${today}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Erro ao gerar backup");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md space-y-4">
      <p className="text-sm text-gray-600">
        Exporte todos os dados do sistema para um arquivo. Operação manual sob demanda.
      </p>
      <div className="flex gap-3">
        <Button variant="outline" onClick={() => download("json")} disabled={loadingJson}>
          {loadingJson ? "Gerando..." : "Exportar JSON"}
        </Button>
        <Button variant="outline" onClick={() => download("xlsx")} disabled={loadingXlsx}>
          {loadingXlsx ? "Gerando..." : "Exportar Excel"}
        </Button>
      </div>
    </div>
  );
}

export function ConfiguracoesPage() {
  const [activeTab, setActiveTab] = useState<Tab>("estabelecimento");

  return (
    <div className="p-6">
      <h1 className="mb-6 text-xl font-semibold">Configurações</h1>

      <div className="mb-6 flex border-b">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? "border-b-2 border-gray-900 text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "estabelecimento" && <TabEstabelecimento />}
      {activeTab === "senha" && <TabSenha />}
      {activeTab === "impressora" && <TabImpressora />}
      {activeTab === "backup" && <TabBackup />}
    </div>
  );
}
