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
    <div className="space-y-6 pb-20 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Radio className="w-6 h-6 text-amber-400" />
            Observed Failure Concentration
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-950/80 border border-amber-500/30 text-amber-300 font-semibold">
              Telemetry Radar
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time aggregate diagnostics and recovery efficiency across failure categories derived from ingested merchant webhooks.
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Radar
        </button>
      </div>

      {/* Transparency Note */}
      <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-400 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <span>
          <strong>Telemetry Notice:</strong> All metrics represent <em>observed failure concentrations</em> from processed merchant webhook events in RazorFlow. RazorFlow does not claim unverified external banking telemetry.
        </span>
      </div>

      {/* Category Breakdown Cards */}
      {loading ? (
        <div className="py-20 text-center text-slate-500">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-amber-500" />
          Loading observed failure concentrations...
        </div>
      ) : !metrics?.category_breakdown ? (
        <div className="py-12 text-center text-slate-400">
          No failure concentration data recorded yet.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {Object.entries(metrics.category_breakdown).map(([categoryKey, catData]) => {
              const recoveryRate = catData.recovery_rate_pct || 0;
              const isTransient =
                categoryKey === "BANK_SYSTEM_OUTAGE" ||
                categoryKey === "TECHNICAL_GATEWAY_TIMEOUT";

              return (
                <div
                  key={categoryKey}
                  className="p-5 rounded-2xl border border-slate-800 bg-[#0d1322] shadow-xl space-y-4 hover:border-slate-700 transition"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <CategoryBadge category={categoryKey as any} />
                      <span className="block text-[10px] text-slate-400 mt-1.5 font-mono">
                        {isTransient ? "Transient (Auto-Retryable)" : "Non-Transient"}
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold text-slate-300">
                      {catData.total_cases} cases
                    </span>
                  </div>

                  {/* Recovery Rate Bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">Observed Recovery Yield</span>
                      <span className="font-bold text-emerald-400 font-mono">
                        {formatPercent(recoveryRate)}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(0, recoveryRate))}%` }}
                      />
                    </div>
                  </div>

                  {/* Financial Stats */}
                  <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">
                        At Risk
                      </span>
                      <div className="font-mono font-bold text-rose-400 mt-0.5">
                        {formatINR(catData.amount_at_risk_cents)}
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">
                        Recovered
                      </span>
                      <div className="font-mono font-bold text-emerald-400 mt-0.5">
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
            <div className="p-6 rounded-2xl border border-slate-800 bg-[#0d1322] shadow-xl space-y-4">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-blue-400" />
                Intervention Strategy Effectiveness
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                {Object.entries(metrics.action_breakdown).map(([actionKey, actData]) => (
                  <div
                    key={actionKey}
                    className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/60 space-y-2"
                  >
                    <div className="font-semibold text-slate-200 font-mono">
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
                    <div className="flex justify-between text-slate-400 pt-1 border-t border-slate-800/60 text-[10px]">
                      <span>Intervention Cost</span>
                      <span className="font-mono text-slate-300">{formatINR(actData.total_cost_cents)}</span>
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
