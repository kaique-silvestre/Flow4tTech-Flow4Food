import { describe, expect, it, vi } from "vitest";
import { IMPERSONATION_SESSION_KEY, openImpersonationSession } from "./impersonation";

describe("openImpersonationSession", () => {
  it("stores the token before navigating and never includes it in a URL", () => {
    const setItem = vi.fn();
    const replace = vi.fn();
    const popup = {
      sessionStorage: { setItem },
      location: { replace },
      opener: window,
    } as unknown as Window;
    const open = vi.spyOn(window, "open").mockReturnValue(popup);

    expect(openImpersonationSession("header.payload.signature")).toBe(true);

    expect(open).toHaveBeenCalledWith("about:blank", "_blank");
    expect(setItem).toHaveBeenCalledWith(IMPERSONATION_SESSION_KEY, "header.payload.signature");
    expect(replace).toHaveBeenCalledWith("/");
    expect(popup.opener).toBeNull();
    expect(JSON.stringify(open.mock.calls)).not.toContain("header.payload.signature");
  });

  it("does not attempt navigation when the browser blocks the popup", () => {
    vi.spyOn(window, "open").mockReturnValue(null);
    expect(openImpersonationSession("token")).toBe(false);
  });
});
