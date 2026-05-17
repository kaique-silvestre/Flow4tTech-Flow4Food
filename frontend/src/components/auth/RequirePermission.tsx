import { Navigate } from "react-router-dom";
import { usePermission } from "@/hooks/usePermission";

interface Props {
  screen: string;
  children: React.ReactNode;
}

export function RequirePermission({ screen, children }: Props) {
  const allowed = usePermission(screen);
  if (!allowed) return <Navigate to="/" replace />;
  return <>{children}</>;
}
