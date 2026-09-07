import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Pagination } from "./pagination";

describe("Pagination items-per-page selector", () => {
  it("renders a native select with options 10/25/50 showing the current porPagina", () => {
    render(
      <Pagination
        pagina={1}
        totalPaginas={3}
        total={25}
        porPagina={10}
        onPorPaginaChange={vi.fn()}
        onPageChange={vi.fn()}
      />,
    );

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("10");
    expect(screen.getByRole("option", { name: "10" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "25" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "50" })).toBeInTheDocument();
  });

  it("calls onPorPaginaChange with the numeric value when the selector changes", () => {
    const onPorPaginaChange = vi.fn();
    render(
      <Pagination
        pagina={1}
        totalPaginas={3}
        total={25}
        porPagina={10}
        onPorPaginaChange={onPorPaginaChange}
        onPageChange={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "25" } });
    expect(onPorPaginaChange).toHaveBeenCalledWith(25);
  });

  it("does not render the selector when porPagina/onPorPaginaChange are not provided", () => {
    render(
      <Pagination
        pagina={1}
        totalPaginas={3}
        total={25}
        onPageChange={vi.fn()}
      />,
    );

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });
});
