import { cn } from "@/lib/utils";

export function getInitials(nome: string): string {
  return nome
    .trim()
    .split(/\s+/)
    .map((parte) => parte[0]?.toUpperCase() ?? "")
    .join("");
}

export function UserAvatarInitials({ nome, className }: { nome: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-200 text-xs font-medium text-gray-700",
        className,
      )}
      aria-hidden="true"
    >
      {getInitials(nome)}
    </span>
  );
}
