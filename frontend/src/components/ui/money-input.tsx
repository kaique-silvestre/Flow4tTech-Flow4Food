import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";

interface MoneyInputProps {
  value?: number | string | null;
  onValueChange?: (rawValue: string) => void;
  id?: string;
  className?: string;
  placeholder?: string;
}

function toCents(v: number | string | null | undefined): number {
  if (v == null || v === "") return 0;
  const n = parseFloat(String(v));
  return isNaN(n) ? 0 : Math.round(n * 100);
}

function centsToDisplay(c: number): string {
  if (c === 0) return "";
  const r = Math.floor(c / 100);
  const d = c % 100;
  return `R$ ${r.toLocaleString("pt-BR")},${String(d).padStart(2, "0")}`;
}

export function MoneyInput({ value, onValueChange, id, className, placeholder }: MoneyInputProps) {
  const [cents, setCents] = useState(() => toCents(value));
  const focused = useRef(false);

  useEffect(() => {
    if (!focused.current) {
      setCents(toCents(value));
    }
  }, [value]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key >= "0" && e.key <= "9") {
      e.preventDefault();
      const next = Math.min(cents * 10 + parseInt(e.key), 99999999);
      setCents(next);
      onValueChange?.(String(next / 100));
    } else if (e.key === "Backspace") {
      e.preventDefault();
      const next = Math.floor(cents / 10);
      setCents(next);
      onValueChange?.(String(next / 100));
    }
  }

  return (
    <Input
      id={id}
      className={className}
      placeholder={placeholder ?? "R$ 0,00"}
      value={centsToDisplay(cents)}
      onChange={() => {}}
      onFocus={() => { focused.current = true; }}
      onBlur={() => { focused.current = false; }}
      onKeyDown={handleKeyDown}
    />
  );
}
