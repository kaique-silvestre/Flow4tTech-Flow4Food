import { Bell } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";

export interface NotificationItem {
  id: string;
  title: string;
  description: string;
  time: string;
}

interface NotificationsProps {
  items?: NotificationItem[];
}

const defaultNotifications: NotificationItem[] = [
  {
    id: "1",
    title: "Conta vencendo",
    description: "Sem fornecedor — R$ 350,00 vence hoje.",
    time: "agora",
  },
  {
    id: "2",
    title: "Promoção ativa",
    description: "Promoção Teste está ativa hoje.",
    time: "hoje",
  },
  {
    id: "3",
    title: "Evento próximo",
    description: "Evento Teste 2 em 14 dias.",
    time: "25 jun",
  },
];

export function Notifications({ items = defaultNotifications }: NotificationsProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          className="relative inline-flex items-center justify-center rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
          aria-label="Notificações"
        >
          <Bell className="h-5 w-5" />
          {items.length > 0 && (
            <Badge
              variant="default"
              className="absolute -top-0.5 -right-0.5 h-4 min-w-4 px-1 text-[10px] leading-none flex items-center justify-center"
            >
              {items.length > 9 ? "9+" : items.length}
            </Badge>
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0 bg-white border-gray-200" align="end" side="bottom" sideOffset={8}>
        <div className="rounded-lg border bg-white shadow-lg overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
            <span className="text-sm font-semibold text-gray-800">Notificações</span>
            {items.length > 0 && (
              <span className="text-xs text-gray-400">{items.length} nova(s)</span>
            )}
          </div>
          {items.length === 0 ? (
            <div className="p-6 text-sm text-gray-400 text-center">
              Nenhuma notificação
            </div>
          ) : (
            <ul className="divide-y divide-gray-100 max-h-72 overflow-y-auto">
              {items.map((item) => (
                <li key={item.id} className="px-4 py-3 hover:bg-gray-50 transition-colors cursor-pointer">
                  <div className="flex justify-between items-start gap-2 mb-0.5">
                    <span className="font-medium text-sm text-gray-900 leading-tight">{item.title}</span>
                    <span className="text-[10px] text-gray-400 shrink-0 mt-0.5">{item.time}</span>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">{item.description}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
