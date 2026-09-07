import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CategoriaFilterPopover, buildCategoryPaths } from "./CategoriaFilterPopover";
import type { Categoria } from "@/features/cadastros/categorias/useCategorias";

const categorias: Categoria[] = [
  {
    id: 1,
    nome: "Bebidas",
    ativo: true,
    children: [
      { id: 2, nome: "Refrigerantes", ativo: true, children: [] },
      { id: 3, nome: "Sucos", ativo: true, children: [] },
    ],
  },
  {
    id: 4,
    nome: "Comidas",
    ativo: true,
    children: [],
  },
];

const catPathMap = buildCategoryPaths(categorias);

describe("CategoriaFilterPopover", () => {
  it("opens the popover when the trigger button is clicked", () => {
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={null}
        onChange={vi.fn()}
        expandidos={new Set()}
        onToggleExpand={vi.fn()}
      />,
    );

    expect(screen.queryByText("Bebidas")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /todas as categorias/i }));
    expect(screen.getByText("Bebidas")).toBeInTheDocument();
  });

  it("hides subcategories until the parent is expanded", () => {
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={null}
        onChange={vi.fn()}
        expandidos={new Set()}
        onToggleExpand={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /todas as categorias/i }));
    expect(screen.queryByText("Refrigerantes")).not.toBeInTheDocument();
  });

  it("shows subcategories once the parent id is in the expandidos set", () => {
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={null}
        onChange={vi.fn()}
        expandidos={new Set([1])}
        onToggleExpand={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /todas as categorias/i }));
    expect(screen.getByText("Refrigerantes")).toBeInTheDocument();
    expect(screen.getByText("Sucos")).toBeInTheDocument();
  });

  it("calls onToggleExpand with the parent id when the expand chevron is clicked", () => {
    const onToggleExpand = vi.fn();
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={null}
        onChange={vi.fn()}
        expandidos={new Set()}
        onToggleExpand={onToggleExpand}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /todas as categorias/i }));
    fireEvent.click(screen.getByRole("button", { name: /expandir bebidas/i }));
    expect(onToggleExpand).toHaveBeenCalledWith(1);
  });

  it("calls onChange with the parent id and closes when a parent category is selected", () => {
    const onChange = vi.fn();
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={null}
        onChange={onChange}
        expandidos={new Set()}
        onToggleExpand={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /todas as categorias/i }));
    fireEvent.click(screen.getByRole("button", { name: "Bebidas" }));
    expect(onChange).toHaveBeenCalledWith(1);
    expect(screen.queryByText("Comidas")).not.toBeInTheDocument();
  });

  it("calls onChange with the subcategory id when a subcategory is selected", () => {
    const onChange = vi.fn();
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={null}
        onChange={onChange}
        expandidos={new Set([1])}
        onToggleExpand={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /todas as categorias/i }));
    fireEvent.click(screen.getByRole("button", { name: "Refrigerantes" }));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("calls onChange with null when 'Todas as categorias' is selected", () => {
    const onChange = vi.fn();
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={1}
        onChange={onChange}
        expandidos={new Set()}
        onToggleExpand={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /bebidas/i }));
    fireEvent.click(screen.getByRole("button", { name: /todas as categorias/i }));
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("shows the selected category's name on the trigger button", () => {
    render(
      <CategoriaFilterPopover
        categorias={categorias}
        catPathMap={catPathMap}
        value={2}
        onChange={vi.fn()}
        expandidos={new Set()}
        onToggleExpand={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /bebidas > refrigerantes/i })).toBeInTheDocument();
  });
});
