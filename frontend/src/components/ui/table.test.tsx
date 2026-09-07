import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from "./table";

describe("Table primitives", () => {
  it("renders a full table structure with header, body, footer and caption", () => {
    render(
      <Table>
        <TableCaption>Produtos</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead className="text-right">Preço</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Pizza</TableCell>
            <TableCell className="text-right">R$ 10,00</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell>Total</TableCell>
            <TableCell className="text-right">R$ 10,00</TableCell>
          </TableRow>
        </TableFooter>
      </Table>,
    );

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("Produtos")).toBeInTheDocument();
    expect(screen.getByText("Nome")).toBeInTheDocument();
    expect(screen.getByText("Pizza")).toBeInTheDocument();
    expect(screen.getByText("Total")).toBeInTheDocument();
  });

  it("applies hover:bg-gray-50 to TableRow by default", () => {
    render(
      <table>
        <tbody>
          <TableRow data-testid="row">
            <TableCell>x</TableCell>
          </TableRow>
        </tbody>
      </table>,
    );
    expect(screen.getByTestId("row").className).toContain("hover:bg-gray-50");
  });

  it("forwards refs for Table and TableRow", () => {
    let tableRef: HTMLTableElement | null = null;
    let rowRef: HTMLTableRowElement | null = null;
    render(
      <Table ref={(el) => { tableRef = el; }}>
        <TableBody>
          <TableRow ref={(el) => { rowRef = el; }}>
            <TableCell>x</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );
    expect(tableRef).toBeInstanceOf(HTMLTableElement);
    expect(rowRef).toBeInstanceOf(HTMLTableRowElement);
  });
});
