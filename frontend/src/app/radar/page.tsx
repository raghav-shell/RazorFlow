"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Radio,
  RefreshCw,
  Info,
  ShieldCheck,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { MetricSummary } from "@/lib/api/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { CategoryBadge } from "@/components/ui/CategoryBadge";

export default function FailureRadarPage() {
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      const data = await apiClient.getMetrics("demo-store");
      setMetrics(data);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load failure concentration metrics.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-8 pb-28 max-w-7xl mx-auto px-2 sm:px-4">
      {/* Header Cockpit */}
      <section className="pt-4 pb-2 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
            <Radio className="w-3.5 h-3.5 text-[#ffd60a]" />
            <span className="text-xs font-medium text-[#86868b]">Root-Cause Diagnostics</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-white">
            Observed Failure Radar
          </h1>
          <p className="text-sm text-[#86868b] leading-relaxed">
            Real-time aggregate diagnostics and statistical recovery efficiency across all failure categories.
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition cursor-pointer shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#64d2ff]" : ""}`} />
          <span>Refresh Radar</span>
        </button>
      </section>

      {/* Telemetry Notice */}
      <div className="apple-card p-4 text-xs text-[#86868b] flex items-start gap-3">
        <Info className="w-4 h-4 text-[#0071e3] shrink-0 mt-0.5" />
        <span className="leading-relaxed">
          <strong className="text-white">Telemetry Transparency:</strong> All metrics represent observed failure concentrations from processed merchant webhook events in RazorFlow.
        </span>
      </div>

      {/* Category Breakdown Cards */}
      {loading ? (
        <div className="py-20 text-center text-[#86868b]">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-[#0071e3]" />
          <p className="text-xs">Ingesting telemetry data points...</p>
        </div>
      ) : !metrics?.category_breakdown ? (
        <div className="py-16 text-center text-[#86868b]">
          No failure concentration data recorded yet.
        </div>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {Object.entries(metrics.category_breakdown).map(([categoryKey, catData]) => {
              const recoveryRate = catData.recovery_rate_pct || 0;
              const isTransient =
                categoryKey === "BANK_SYSTEM_OUTAGE" ||
                categoryKey === "TECHNICAL_GATEWAY_TIMEOUT";

              return (
                <div
                  key={categoryKey}
                  className="apple-card p-6 space-y-5 apple-card-hover"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CategoryBadge category={categoryKey as any} />
                      <span className="block text-[10px] text-[#86868b] mt-2 font-mono">
                        {isTransient ? "⚡ Transient (Auto-Retryable)" : "🛡️ Non-Transient"}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-white px-2.5 py-0.5 rounded-full bg-white/[0.06] border border-white/[0.04]">
                      {catData.total_cases} cases
                    </span>
                  </div>

                  {/* Recovery Rate Bar */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-[#86868b]">Recovery Yield</span>
                      <span className="font-semibold text-[#30d158] font-mono">
                        {formatPercent(recoveryRate)}
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#30d158] rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(0, recoveryRate))}%` }}
                      />
                    </div>
                  </div>

                  {/* Financial Stats */}
                  <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/[0.06] text-xs">
                    <div>
                      <span className="text-[10px] text-[#86868b] uppercase">At Risk</span>
                      <div className="font-mono font-semibold text-[#ff453a] text-sm mt-0.5">
                        {formatINR(catData.amount_at_risk_cents)}
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#86868b] uppercase">Recovered</span>
                      <div className="font-mono font-semibold text-[#30d158] text-sm mt-0.5">
                        {formatINR(catData.amount_recovered_cents)}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Effectiveness Summary */}
          {metrics.action_breakdown && (
            <div className="apple-card p-6 sm:p-7 space-y-5">
              <h2 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                <ShieldCheck className="w-4 h-4 text-[#0071e3]" />
                <span>Intervention Strategy Effectiveness</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                {Object.entries(metrics.action_breakdown).map(([actionKey, actData]) => (
                  <div
                    key={actionKey}
                    className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-2.5"
                  >
                    <div className="font-semibold text-white font-mono text-xs">
                      {actionKey.replace(/_/g, " ")}
                    </div>
                    <div className="flex justify-between text-[#86868b]">
                      <span>Attempts</span>
                      <span className="font-mono text-white font-medium">{actData.total_attempts}</span>
                    </div>
                    <div className="flex justify-between text-[#86868b]">
                      <span>Success Rate</span>
                      <span className="font-mono text-[#30d158] font-semibold">
                        {formatPercent(actData.success_rate_pct)}
                      </span>
                    </div>
                    <div className="flex justify-between text-[#86868b] pt-2 border-t border-white/[0.04] text-[10px]">
                      <span>Intervention Cost</span>
                      <span className="font-mono text-white">{formatINR(actData.total_cost_cents)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
