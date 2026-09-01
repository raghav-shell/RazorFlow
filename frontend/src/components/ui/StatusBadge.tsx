import React from "react";
import { cn } from "@/lib/utils";
import { RecoveryCaseStatus } from "@/lib/api/types";

interface StatusBadgeProps {
  status: RecoveryCaseStatus | string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  let badgeStyles = "bg-slate-900/80 text-slate-300 border-slate-700/60";
  let dotColor = "bg-slate-400";
  let halo = "";

  switch (status) {
    case "RECOVERED":
      badgeStyles = "bg-emerald-950/60 text-emerald-300 border-emerald-500/40 shadow-sm shadow-emerald-500/20";
      dotColor = "bg-emerald-400";
      halo = "shadow-[0_0_8px_rgba(52,211,153,0.5)]";
      break;
    case "APPROVED":
    case "EXECUTING":
      badgeStyles = "bg-blue-950/60 text-blue-300 border-blue-500/40 shadow-sm shadow-blue-500/20";
      dotColor = "bg-blue-400";
      halo = "shadow-[0_0_8px_rgba(96,165,250,0.5)]";
      break;
    case "WAITING_EXTERNAL":
    case "VERIFYING":
      badgeStyles = "bg-amber-950/60 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-500/20";
      dotColor = "bg-amber-400 animate-pulse";
      halo = "shadow-[0_0_8px_rgba(251,191,36,0.5)]";
      break;
    case "ESCALATED":
      badgeStyles = "bg-purple-950/60 text-purple-300 border-purple-500/40 shadow-sm shadow-purple-500/20";
      dotColor = "bg-purple-400";
      halo = "shadow-[0_0_8px_rgba(192,132,252,0.5)]";
      break;
    case "UNRECOVERABLE":
    case "EXPIRED":
    case "STOPPED":
    case "REJECTED":
      badgeStyles = "bg-rose-950/60 text-rose-300 border-rose-500/40 shadow-sm shadow-rose-500/20";
      dotColor = "bg-rose-400";
      halo = "shadow-[0_0_8px_rgba(251,113,133,0.5)]";
      break;
    case "DETECTED":
    case "ENRICHING":
    case "DIAGNOSING":
      badgeStyles = "bg-cyan-950/60 text-cyan-300 border-cyan-500/40 shadow-sm shadow-cyan-500/20";
      dotColor = "bg-cyan-400 animate-pulse";
      halo = "shadow-[0_0_8px_rgba(34,211,238,0.5)]";
      break;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase border backdrop-blur-md",
        badgeStyles,
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", dotColor, halo)} />
      {status.replace(/_/g, " ")}
    </span>
  );
}
