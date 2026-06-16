import { cn } from "@/lib/utils";

interface NavBadgeProps {
  count: number;
  color?: string;
  /** collapsed = dot mode (sidebar recolhida) */
  dot?: boolean;
  className?: string;
}

/**
 * Badge numérico para itens de navegação.
 * dot=false (padrão): pill com número  — ex: sidebar expandida
 * dot=true: bolinha sem número          — ex: sidebar recolhida
 */
export function NavBadge({ count, color = "bg-amber-500", dot = false, className }: NavBadgeProps) {
  if (count <= 0) return null;

  if (dot) {
    return (
      <span
        className={cn(
          "absolute top-0.5 right-0.5 h-2 w-2 rounded-full ring-2 ring-white",
          color,
          className,
        )}
        aria-label={`${count} notificações`}
      />
    );
  }

  return (
    <span
      className={cn(
        "rounded-full px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white",
        color,
        className,
      )}
      aria-label={`${count} notificações`}
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}
