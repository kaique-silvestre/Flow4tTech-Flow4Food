import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { getInitials, UserAvatarInitials } from "./UserAvatarInitials";

describe("getInitials", () => {
  it("junta a primeira letra de cada parte do nome, em maiúsculo", () => {
    expect(getInitials("José da Silva")).toBe("JDS");
  });

  it("retorna apenas uma letra para nome sem espaço", () => {
    expect(getInitials("Maria")).toBe("M");
  });
});

describe("UserAvatarInitials", () => {
  it("renderiza um círculo com as iniciais do nome", () => {
    render(<UserAvatarInitials nome="Ana Paula" />);

    expect(screen.getByText("AP")).toBeInTheDocument();
  });
});
