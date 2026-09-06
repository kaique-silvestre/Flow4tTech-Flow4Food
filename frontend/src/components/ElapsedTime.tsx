import { memo, useEffect, useState } from "react";

function parseUtc(iso: string): number {
  const s = iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z";
  return new Date(s).getTime();
}

export function formatElapsed(sinceIso: string, now: number): string {
  const ms = now - parseUtc(sinceIso);
  const totalMin = Math.floor(ms / 60_000);
  if (totalMin < 60) return `${totalMin} min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return `${h}h ${m}min`;
}

interface ElapsedTimeProps {
  /** ISO datetime (backend UTC naive) to measure elapsed time from. */
  since: string;
  /** Stop ticking (e.g. comanda já fechada) without unmounting. */
  active?: boolean;
}

/**
 * Ticks its own "Xmin"/"Xh Ymin" label every second, isolated in its own
 * component so a 1s clock doesn't force a full re-render of whatever list
 * or page renders it (comandas abertas can be a long list).
 */
export const ElapsedTime = memo(function ElapsedTime({ since, active = true }: ElapsedTimeProps) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => setNow(Date.now()), 1_000);
    return () => clearInterval(id);
  }, [active]);

  return <>{formatElapsed(since, now)}</>;
});
