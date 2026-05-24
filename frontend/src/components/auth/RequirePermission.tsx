import { Outlet } from "react-router-dom";
import { usePermission } from "@/hooks/usePermission";

interface Props {
  screen: string;
}

export function RequirePermission({ screen }: Props) {
  const allowed = usePermission(screen);

  if (!allowed) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-gray-400">
        <p className="text-base font-medium text-gray-600">Acesso não autorizado</p>
        <p className="text-sm">Seu perfil não tem permissão para esta tela.</p>
      </div>
    );
  }

  return <Outlet />;
}
