import React from "react";
import { cn } from "@/lib/utils";
import { RecoveryCaseStatus } from "@/lib/api/types";

interface StatusBadgeProps {
  status: RecoveryCaseStatus | string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  let badgeStyles = "bg-white/[0.04] text-[#86868b] border-white/[0.08]";
  let dotColor = "bg-[#86868b]";
  let halo = "";

  switch (status) {
    case "RECOVERED":
      badgeStyles = "bg-[#30d158]/10 text-[#30d158] border-[#30d158]/25 shadow-[0_0_12px_rgba(48,209,88,0.15)]";
      dotColor = "bg-[#30d158]";
      halo = "shadow-[0_0_8px_rgba(48,209,88,0.6)]";
      break;
    case "APPROVED":
    case "EXECUTING":
      badgeStyles = "bg-[#0071e3]/10 text-[#64d2ff] border-[#0071e3]/30 shadow-[0_0_12px_rgba(0,113,227,0.15)]";
      dotColor = "bg-[#64d2ff]";
      halo = "shadow-[0_0_8px_rgba(100,210,255,0.6)]";
      break;
    case "WAITING_EXTERNAL":
    case "VERIFYING":
      badgeStyles = "bg-[#ffd60a]/10 text-[#ffd60a] border-[#ffd60a]/30 shadow-[0_0_12px_rgba(255,214,10,0.15)]";
      dotColor = "bg-[#ffd60a] animate-pulse";
      halo = "shadow-[0_0_8px_rgba(255,214,10,0.6)]";
      break;
    case "ESCALATED":
      badgeStyles = "bg-[#bf5af2]/10 text-[#bf5af2] border-[#bf5af2]/30 shadow-[0_0_12px_rgba(191,90,242,0.15)]";
      dotColor = "bg-[#bf5af2]";
      halo = "shadow-[0_0_8px_rgba(191,90,242,0.6)]";
      break;
    case "UNRECOVERABLE":
    case "EXPIRED":
    case "STOPPED":
    case "REJECTED":
      badgeStyles = "bg-[#ff453a]/10 text-[#ff453a] border-[#ff453a]/25 shadow-[0_0_12px_rgba(255,69,58,0.15)]";
      dotColor = "bg-[#ff453a]";
      halo = "shadow-[0_0_8px_rgba(255,69,58,0.6)]";
      break;
    case "DETECTED":
    case "ENRICHING":
    case "DIAGNOSING":
      badgeStyles = "bg-[#64d2ff]/10 text-[#64d2ff] border-[#64d2ff]/25 shadow-[0_0_12px_rgba(100,210,255,0.15)]";
      dotColor = "bg-[#64d2ff] animate-pulse";
      halo = "shadow-[0_0_8px_rgba(100,210,255,0.6)]";
      break;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-wide uppercase border backdrop-blur-md transition-all duration-200",
        badgeStyles,
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", dotColor, halo)} />
      {status.replace(/_/g, " ")}
    </span>
  );
}
