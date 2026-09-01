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

  let style = "bg-slate-900/60 text-slate-300 border-slate-700/60";

  if (category === "USER_AUTHENTICATION_DROPOFF") {
    style = "bg-sky-950/40 text-sky-300 border-sky-500/30 shadow-sm shadow-sky-500/10";
  } else if (category === "BANK_SYSTEM_OUTAGE") {
    style = "bg-amber-950/40 text-amber-300 border-amber-500/30 shadow-sm shadow-amber-500/10";
  } else if (category === "INSUFFICIENT_FUNDS") {
    style = "bg-orange-950/40 text-orange-300 border-orange-500/30 shadow-sm shadow-orange-500/10";
  } else if (category === "TECHNICAL_GATEWAY_TIMEOUT") {
    style = "bg-indigo-950/40 text-indigo-300 border-indigo-500/30 shadow-sm shadow-indigo-500/10";
  } else if (category === "FRAUD_RISK_BLOCK") {
    style = "bg-rose-950/40 text-rose-300 border-rose-500/30 shadow-sm shadow-rose-500/10";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold border backdrop-blur-md",
        style,
        className
      )}
    >
      <span>{cleanName}</span>
      {isTransient && (
        <span className="text-[9px] bg-amber-400/20 text-amber-300 border border-amber-400/30 px-1.5 py-0.2 rounded-full uppercase tracking-wider font-extrabold">
          Transient
        </span>
      )}
    </span>
  );
}
