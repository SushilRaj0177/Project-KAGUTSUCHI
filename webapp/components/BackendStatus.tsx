"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "./LanguageContext";

type Status = "checking" | "online" | "offline";

export function BackendStatus() {
  const { t, lang } = useLanguage();
  const jp = lang === "ja" ? "font-jp" : "";
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let cancelled = false;
    fetch("/api/backend/health")
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setStatus(data.online ? "online" : "offline");
      })
      .catch(() => {
        if (!cancelled) setStatus("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "checking") return null;

  const label = status === "online" ? t.backendOnline : t.backendOffline;
  const detail = status === "online" ? t.backendOnline : t.backendOfflineDetail;
  const dotColor = status === "online" ? "bg-neon-cyan shadow-[0_0_6px_var(--neon-cyan)]" : "bg-neon-pink shadow-[0_0_6px_var(--neon-pink)]";

  return (
    <div
      className={`flex shrink-0 items-center gap-1.5 font-mono text-[10px] whitespace-nowrap text-steel-400 uppercase tracking-wide ${jp}`}
      title={detail}
    >
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotColor}`} />
      {label}
    </div>
  );
}
