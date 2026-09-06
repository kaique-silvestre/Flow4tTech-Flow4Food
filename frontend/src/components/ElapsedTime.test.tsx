import { render, screen } from "@testing-library/react";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ElapsedTime, formatElapsed } from "./ElapsedTime";

describe("formatElapsed", () => {
  it("formats minutes under an hour", () => {
    const since = new Date("2026-01-01T10:00:00Z").toISOString();
    const now = new Date("2026-01-01T10:35:00Z").getTime();
    expect(formatElapsed(since, now)).toBe("35 min");
  });

  it("formats hours and minutes past an hour", () => {
    const since = new Date("2026-01-01T10:00:00Z").toISOString();
    const now = new Date("2026-01-01T12:20:00Z").getTime();
    expect(formatElapsed(since, now)).toBe("2h 20min");
  });

  it("treats a naive (no timezone suffix) datetime as UTC, like the rest of the app", () => {
    const since = "2026-01-01T10:00:00";
    const now = new Date("2026-01-01T10:10:00Z").getTime();
    expect(formatElapsed(since, now)).toBe("10 min");
  });
});

describe("ElapsedTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T10:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("ticks its own label every second without requiring the parent to re-render", () => {
    const since = new Date("2026-01-01T09:59:00Z").toISOString();
    render(<ElapsedTime since={since} />);

    expect(screen.getByText("1 min")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(60_000);
    });

    expect(screen.getByText("2 min")).toBeInTheDocument();
  });

  it("stops ticking when active=false", () => {
    const since = new Date("2026-01-01T09:59:00Z").toISOString();
    const { rerender } = render(<ElapsedTime since={since} active={false} />);
    expect(screen.getByText("1 min")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(120_000);
    });
    // No interval was ever started, so the label is frozen.
    expect(screen.getByText("1 min")).toBeInTheDocument();

    rerender(<ElapsedTime since={since} active={false} />);
    expect(screen.getByText("1 min")).toBeInTheDocument();
  });
});
