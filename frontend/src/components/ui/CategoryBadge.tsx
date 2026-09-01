import React from "react";
import { cn } from "@/lib/utils";
import { FailureCategory } from "@/lib/api/types";

interface CategoryBadgeProps {
  category: FailureCategory | string;
  isTransient?: boolean;
  className?: string;
}

export function CategoryBadge({ category, isTransient, className }: CategoryBadgeProps) {
  const cleanName = (category || "UNKNOWN").replace(/_/g, " ");

  let style = "bg-white/[0.04] text-[#86868b] border-white/[0.08]";

  if (category === "USER_AUTHENTICATION_DROPOFF") {
    style = "bg-[#0071e3]/10 text-[#64d2ff] border-[#0071e3]/30";
  } else if (category === "BANK_SYSTEM_OUTAGE") {
    style = "bg-[#ffd60a]/10 text-[#ffd60a] border-[#ffd60a]/30";
  } else if (category === "INSUFFICIENT_FUNDS") {
    style = "bg-[#ff9f0a]/10 text-[#ff9f0a] border-[#ff9f0a]/30";
  } else if (category === "TECHNICAL_GATEWAY_TIMEOUT") {
    style = "bg-[#bf5af2]/10 text-[#bf5af2] border-[#bf5af2]/30";
  } else if (category === "FRAUD_RISK_BLOCK") {
    style = "bg-[#ff453a]/10 text-[#ff453a] border-[#ff453a]/30";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border backdrop-blur-md",
        style,
        className
      )}
    >
      <span>{cleanName}</span>
      {isTransient && (
        <span className="text-[9px] bg-[#ffd60a]/20 text-[#ffd60a] border border-[#ffd60a]/40 px-1.5 py-0.2 rounded-full uppercase tracking-wider font-mono font-semibold">
          Transient
        </span>
      )}
    </span>
  );
}
