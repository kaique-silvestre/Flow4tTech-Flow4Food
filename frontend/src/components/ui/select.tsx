import * as React from "react";
import { cn } from "@/lib/utils";

interface SelectContextValue {
  value: string;
  onValueChange: (value: string) => void;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const SelectContext = React.createContext<SelectContextValue | null>(null);

function useSelectCtx() {
  const ctx = React.useContext(SelectContext);
  if (!ctx) throw new Error("Select context missing");
  return ctx;
}

interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

function Select({ value, defaultValue, onValueChange, children }: SelectProps) {
  const [internalValue, setInternalValue] = React.useState(defaultValue ?? "");
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const controlled = value !== undefined;
  const currentValue = controlled ? (value ?? "") : internalValue;

  function handleChange(v: string) {
    if (!controlled) setInternalValue(v);
    onValueChange?.(v);
    setOpen(false);
  }

  React.useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <SelectContext.Provider value={{ value: currentValue, onValueChange: handleChange, open, setOpen }}>
      <div ref={containerRef} className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  );
}

interface SelectTriggerProps {
  className?: string;
  children: React.ReactNode;
}

function SelectTrigger({ className, children }: SelectTriggerProps) {
  const { open, setOpen } = useSelectCtx();
  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center justify-between rounded border px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500",
        className
      )}
      onClick={() => setOpen((v) => !v)}
    >
      {children}
      <svg
        className={cn("ml-2 h-4 w-4 shrink-0 text-gray-400 transition-transform", open && "rotate-180")}
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fillRule="evenodd"
          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
          clipRule="evenodd"
        />
      </svg>
    </button>
  );
}

function SelectValue({ placeholder, label }: { placeholder?: string; label?: string }) {
  const { value } = useSelectCtx();
  const display = label ?? (value || null);
  return (
    <span className={cn("block truncate text-left", !display && "text-gray-400")}>
      {display ?? placeholder ?? ""}
    </span>
  );
}

function SelectContent({ children, className }: { children: React.ReactNode; className?: string }) {
  const { open } = useSelectCtx();
  if (!open) return null;
  return (
    <div
      className={cn(
        "absolute left-0 right-0 z-50 mt-1 max-h-60 overflow-auto rounded-md border bg-white py-1 shadow-lg",
        className
      )}
    >
      {children}
    </div>
  );
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

function SelectItem({ value, children, className }: SelectItemProps) {
  const ctx = useSelectCtx();
  const isSelected = ctx.value === value;

  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center px-3 py-2.5 text-sm text-left hover:bg-gray-50 min-h-[44px]",
        isSelected && "bg-blue-50 text-blue-700 font-medium",
        className
      )}
      onClick={() => ctx.onValueChange(value)}
    >
      {children}
    </button>
  );
}

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
