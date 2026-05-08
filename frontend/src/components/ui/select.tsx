import * as React from "react";
import { cn } from "@/lib/utils";

interface SelectContextValue {
  value?: string;
  onValueChange?: (value: string) => void;
}

const SelectContext = React.createContext<SelectContextValue>({});

interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

function Select({ value, defaultValue, onValueChange, children }: SelectProps) {
  return (
    <SelectContext.Provider value={{ value: value ?? defaultValue, onValueChange }}>
      {children}
    </SelectContext.Provider>
  );
}

interface SelectTriggerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const SelectTrigger = React.forwardRef<HTMLDivElement, SelectTriggerProps>(
  ({ className, children, ...props }, ref) => {
    const ctx = React.useContext(SelectContext);
    const selectRef = React.useRef<HTMLSelectElement>(null);

    return (
      <div
        ref={ref}
        className={cn("relative", className)}
        {...props}
        onClick={() => selectRef.current?.showPicker?.()}
      >
        {children}
        <select
          ref={selectRef}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          value={ctx.value ?? ""}
          onChange={(e) => ctx.onValueChange?.(e.target.value)}
        >
          <option value="" disabled />
          {/* options rendered by SelectContent via context */}
        </select>
      </div>
    );
  }
);
SelectTrigger.displayName = "SelectTrigger";

function SelectValue({ placeholder }: { placeholder?: string }) {
  const ctx = React.useContext(SelectContext);
  return (
    <span className={cn("block truncate text-sm", !ctx.value && "text-gray-400")}>
      {ctx.value || placeholder || ""}
    </span>
  );
}

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

function SelectContent({ children }: SelectContentProps) {
  const ctx = React.useContext(SelectContext);
  return (
    <SelectContext.Provider value={ctx}>
      <NativeSelectOptions>{children}</NativeSelectOptions>
    </SelectContext.Provider>
  );
}

function NativeSelectOptions({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  children: React.ReactNode;
}

function SelectItem({ value, children, className, ...props }: SelectItemProps) {
  return <div data-value={value} className={cn("hidden", className)} {...props}>{children}</div>;
}

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
