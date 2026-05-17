import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Copy, Check } from "lucide-react";

interface Props {
  toastId: string | number;
  password: string;
}

export function SenhaProvisoriaToast({ toastId, password }: Props) {
  const [secondsLeft, setSecondsLeft] = useState(10);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsLeft((s) => (s <= 1 ? 0 : s - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [toastId]);

  useEffect(() => {
    if (secondsLeft === 0) {
      toast.dismiss(toastId);
    }
  }, [secondsLeft, toastId]);

  function handleCopy() {
    navigator.clipboard.writeText(password).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg border bg-white px-4 py-3 shadow-lg w-72">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-gray-800">Senha provisória</span>
        <span className="text-xs text-gray-400">Fecha em {secondsLeft}s</span>
      </div>
      <div className="flex items-center gap-2 rounded bg-gray-100 px-3 py-2">
        <span className="flex-1 font-mono text-sm font-semibold tracking-wide text-gray-900 select-all">
          {password}
        </span>
        <button
          onClick={handleCopy}
          className="shrink-0 text-gray-500 hover:text-gray-800 transition-colors"
          title="Copiar senha"
        >
          {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} />}
        </button>
      </div>
      <div className="h-1 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full bg-green-500 transition-all duration-1000 ease-linear"
          style={{ width: `${(secondsLeft / 10) * 100}%` }}
        />
      </div>
    </div>
  );
}
