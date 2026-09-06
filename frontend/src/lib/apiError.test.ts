import { describe, expect, it } from "vitest";
import { getApiErrorCode, getApiErrorMessage, getApiErrorStatus } from "./apiError";

function makeAxiosError(status: number, body?: unknown) {
  return { response: { status, data: body } };
}

describe("getApiErrorMessage", () => {
  it("extracts the structured error message from the API envelope", () => {
    const err = makeAxiosError(409, { error: { code: "CONFLICT", message: "Comanda alterada", field: null } });
    expect(getApiErrorMessage(err, "fallback")).toBe("Comanda alterada");
  });

  it("falls back when the error has no structured envelope", () => {
    expect(getApiErrorMessage(new Error("network down"), "fallback")).toBe("fallback");
    expect(getApiErrorMessage(undefined, "fallback")).toBe("fallback");
  });
});

describe("getApiErrorCode", () => {
  it("extracts the structured error code", () => {
    const err = makeAxiosError(409, { error: { code: "SESSAO_JA_ABERTA", message: "x", field: null } });
    expect(getApiErrorCode(err)).toBe("SESSAO_JA_ABERTA");
  });

  it("returns undefined when there is no envelope", () => {
    expect(getApiErrorCode(new Error("boom"))).toBeUndefined();
  });
});

describe("getApiErrorStatus", () => {
  it("extracts the HTTP status", () => {
    expect(getApiErrorStatus(makeAxiosError(404))).toBe(404);
  });

  it("returns undefined when there is no response", () => {
    expect(getApiErrorStatus(new Error("boom"))).toBeUndefined();
  });
});
