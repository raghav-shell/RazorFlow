import React from "react";
import { cn } from "@/lib/utils";
import { RecoveryCaseStatus } from "@/lib/api/types";

interface StatusBadgeProps {
  status: RecoveryCaseStatus | string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  let badgeStyles = "bg-slate-800/80 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";

  switch (status) {
    case "RECOVERED":
      badgeStyles = "bg-emerald-950/80 text-emerald-300 border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.2)]";
      dotColor = "bg-emerald-400";
      break;
    case "APPROVED":
    case "EXECUTING":
      badgeStyles = "bg-blue-950/80 text-blue-300 border-blue-500/40 shadow-[0_0_12px_rgba(59,130,246,0.2)]";
      dotColor = "bg-blue-400";
      break;
    case "WAITING_EXTERNAL":
    case "VERIFYING":
      badgeStyles = "bg-amber-950/80 text-amber-300 border-amber-500/40";
      dotColor = "bg-amber-400 animate-pulse";
      break;
    case "ESCALATED":
      badgeStyles = "bg-purple-950/80 text-purple-300 border-purple-500/40";
      dotColor = "bg-purple-400";
      break;
    case "UNRECOVERABLE":
    case "EXPIRED":
    case "STOPPED":
    case "REJECTED":
      badgeStyles = "bg-rose-950/80 text-rose-300 border-rose-500/40";
      dotColor = "bg-rose-400";
      break;
    case "DETECTED":
    case "ENRICHING":
    case "DIAGNOSING":
      badgeStyles = "bg-cyan-950/80 text-cyan-300 border-cyan-500/40";
      dotColor = "bg-cyan-400 animate-pulse";
      break;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border",
        badgeStyles,
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", dotColor)} />
      {status.replace(/_/g, " ")}
    </span>
  );
}
