import { NumericFormat } from "react-number-format";
import { Input } from "@/components/ui/input";

interface MoneyInputProps {
  value?: number | string | null;
  onValueChange?: (rawValue: string) => void;
  id?: string;
  className?: string;
  placeholder?: string;
}

export function MoneyInput({ value, onValueChange, id, className, placeholder }: MoneyInputProps) {
  return (
    <NumericFormat
      customInput={Input}
      prefix="R$ "
      decimalSeparator=","
      thousandSeparator="."
      decimalScale={2}
      fixedDecimalScale
      value={value ?? ""}
      onValueChange={(values) => {
        onValueChange?.(values.value);
      }}
      id={id}
      className={className}
      placeholder={placeholder ?? "R$ 0,00"}
    />
  );
}
