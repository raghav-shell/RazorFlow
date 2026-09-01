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
    style = "bg-sky-950/60 text-sky-300 border-sky-600/30";
  } else if (category === "BANK_SYSTEM_OUTAGE") {
    style = "bg-amber-950/60 text-amber-300 border-amber-600/30";
  } else if (category === "INSUFFICIENT_FUNDS") {
    style = "bg-orange-950/60 text-orange-300 border-orange-600/30";
  } else if (category === "TECHNICAL_GATEWAY_TIMEOUT") {
    style = "bg-indigo-950/60 text-indigo-300 border-indigo-600/30";
  } else if (category === "FRAUD_RISK_BLOCK") {
    style = "bg-rose-950/60 text-rose-300 border-rose-600/30";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border",
        style,
        className
      )}
    >
      <span>{cleanName}</span>
      {isTransient && (
        <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1 rounded uppercase tracking-wider font-bold">
          Transient
        </span>
      )}
    </span>
  );
}
