"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Radio,
  AlertTriangle,
  Activity,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Zap,
  Info,
  RefreshCw,
  TrendingDown,
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
    <div className="space-y-8 pb-20 max-w-7xl mx-auto">
      {/* Header Cockpit */}
      <div className="p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-gradient-to-br from-[#120e06]/90 via-[#070b1a]/90 to-[#040711]/90 backdrop-blur-2xl shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Radio className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              Live Telemetry Stream
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Observed Failure <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">Concentration Radar</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Real-time aggregate diagnostics and recovery efficiency across failure categories derived from ingested merchant webhooks.
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 border border-white/[0.08] hover:border-amber-500/40 hover:bg-slate-800 text-slate-200 text-xs font-bold transition cursor-pointer shadow-lg shadow-black/40 shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
          Refresh Radar
        </button>
      </div>

      {/* Telemetry Notice */}
      <div className="p-4 rounded-2xl bg-slate-950/60 border border-white/[0.06] text-xs text-slate-400 flex items-start gap-3">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <span className="leading-relaxed">
          <strong>Telemetry Transparency Notice:</strong> All metrics represent <em>observed failure concentrations</em> from processed merchant webhook events in RazorFlow. RazorFlow does not claim unverified external banking telemetry.
        </span>
      </div>

      {/* Category Breakdown Cards */}
      {loading ? (
        <div className="py-20 text-center text-slate-500">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-amber-500" />
          <p className="text-xs font-bold">Ingesting telemetry data points...</p>
        </div>
      ) : !metrics?.category_breakdown ? (
        <div className="py-16 text-center text-slate-400">
          No failure concentration data recorded yet.
        </div>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(metrics.category_breakdown).map(([categoryKey, catData]) => {
              const recoveryRate = catData.recovery_rate_pct || 0;
              const isTransient =
                categoryKey === "BANK_SYSTEM_OUTAGE" ||
                categoryKey === "TECHNICAL_GATEWAY_TIMEOUT";

              return (
                <div
                  key={categoryKey}
                  className="p-6 rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl space-y-5 hover:border-amber-500/30 transition-all duration-300"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CategoryBadge category={categoryKey as any} />
                      <span className="block text-[10px] text-slate-400 mt-2 font-mono font-medium">
                        {isTransient ? "⚡ Transient (Auto-Retryable)" : "🛡️ Non-Transient"}
                      </span>
                    </div>
                    <span className="text-xs font-mono font-black text-white px-2.5 py-1 rounded-lg bg-slate-900 border border-white/[0.06]">
                      {catData.total_cases} cases
                    </span>
                  </div>

                  {/* Recovery Rate Bar */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400 font-bold">Observed Recovery Yield</span>
                      <span className="font-black text-emerald-400 font-mono">
                        {formatPercent(recoveryRate)}
                      </span>
                    </div>
                    <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-white/[0.06]">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(0, recoveryRate))}%` }}
                      />
                    </div>
                  </div>

                  {/* Financial Stats */}
                  <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/[0.06] text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                        At Risk
                      </span>
                      <div className="font-mono font-black text-rose-400 text-sm mt-1">
                        {formatINR(catData.amount_at_risk_cents)}
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                        Recovered
                      </span>
                      <div className="font-mono font-black text-emerald-400 text-sm mt-1">
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
            <div className="p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl space-y-5">
              <h2 className="text-sm font-black text-white uppercase tracking-wider flex items-center gap-2.5 pb-2 border-b border-white/[0.06]">
                <div className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4 text-blue-400" />
                </div>
                <span>Intervention Strategy Effectiveness</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                {Object.entries(metrics.action_breakdown).map(([actionKey, actData]) => (
                  <div
                    key={actionKey}
                    className="p-5 rounded-2xl border border-white/[0.06] bg-slate-950/60 space-y-3"
                  >
                    <div className="font-bold text-white font-mono text-xs">
                      {actionKey.replace(/_/g, " ")}
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Total Executed</span>
                      <span className="font-mono text-white font-bold">{actData.total_attempts}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Success Rate</span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {formatPercent(actData.success_rate_pct)}
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-400 pt-2 border-t border-white/[0.06] text-[10px]">
                      <span>Intervention Cost</span>
                      <span className="font-mono text-slate-300 font-semibold">{formatINR(actData.total_cost_cents)}</span>
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
