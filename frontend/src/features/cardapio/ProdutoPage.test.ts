import { describe, expect, it } from "vitest";
import { buildFichaRemovalPayload } from "./ProdutoPage";
import type { ProdutoResponse } from "@/features/cadastros/produtos/useProdutos";

const produto: ProdutoResponse = {
  id: 1,
  nome: "X-Burger",
  categoria_id: 3,
  preco_venda: 25.5,
  ativo: true,
  producao_possivel: null,
  preco_promocional: null,
  nome_promocao: null,
  ficha_tecnica: [
    { insumo_id: 10, insumo_nome: "Pão", quantidade: 1, unidade_base: "un", custo_medio_insumo: 0.5 },
    { insumo_id: 20, insumo_nome: "Carne", quantidade: 0.15, unidade_base: "kg", custo_medio_insumo: 30 },
  ],
};

describe("buildFichaRemovalPayload", () => {
  it("drops the removed insumo but keeps the others and the product's own fields", () => {
    const payload = buildFichaRemovalPayload(produto, 10);
    expect(payload).toEqual({
      nome: "X-Burger",
      categoria_id: 3,
      preco_venda: "25.5",
      ficha_tecnica: [{ insumo_id: 20, quantidade: "0.15" }],
    });
  });

  it("results in an empty ficha_tecnica when removing the last item", () => {
    const payload = buildFichaRemovalPayload(
      { ...produto, ficha_tecnica: [produto.ficha_tecnica![0]] },
      10,
    );
    expect(payload.ficha_tecnica).toEqual([]);
  });
});
