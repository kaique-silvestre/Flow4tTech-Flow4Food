import { describe, expect, it } from "vitest";
import { decodeJwtPayload } from "./jwt";

function makeToken(payload: unknown): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.signature`;
}

describe("decodeJwtPayload", () => {
  it("decodes a well-formed JWT payload", () => {
    const token = makeToken({ user_id: 1, permissions: ["comandas"] });
    expect(decodeJwtPayload<{ user_id: number; permissions: string[] }>(token)).toEqual({
      user_id: 1,
      permissions: ["comandas"],
    });
  });

  it("decodes base64url-encoded payloads (- and _ instead of + and /)", () => {
    // "?>" encodes to a payload segment containing + and / in standard base64
    const token = makeToken({ note: "?>>>???" });
    expect(decodeJwtPayload<{ note: string }>(token)).toEqual({ note: "?>>>???" });
  });

  it("returns null for a malformed token", () => {
    expect(decodeJwtPayload("not-a-jwt")).toBeNull();
  });

  it("returns null for invalid base64/JSON in the payload segment", () => {
    expect(decodeJwtPayload("header.not-base64-json.sig")).toBeNull();
  });

  it("returns null for an empty string", () => {
    expect(decodeJwtPayload("")).toBeNull();
  });
});
