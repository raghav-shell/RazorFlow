"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Zap,
  Bot,
  ShieldCheck,
  CreditCard,
  Bell,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Eye,
  Radio,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { AuditEventItem } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

export function LiveEventFeed() {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchRecentEvents() {
    try {
      const data = await apiClient.listAuditEvents("demo-store", undefined, 12, 0);
      setEvents(data.items || []);
      setError(null);
    } catch (err: any) {
      setError("Telemetry stream polling paused.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchRecentEvents();
    if (!isLive) return;
    const interval = setInterval(fetchRecentEvents, 4000);
    return () => clearInterval(interval);
  }, [isLive]);

  function getEventIcon(action: string) {
    switch (action) {
      case "WEBHOOK_INGESTED":
      case "PAYMENT_FAILED":
        return <Zap className="w-3.5 h-3.5 text-amber-400" />;
      case "DIAGNOSIS_PERFORMED":
      case "PROBABILITY_SCORED":
        return <Activity className="w-3.5 h-3.5 text-cyan-400" />;
      case "STRATEGY_GENERATED":
      case "AI_RECOMMENDATION":
        return <Bot className="w-3.5 h-3.5 text-purple-400" />;
      case "POLICY_EVALUATED":
      case "POLICY_OVERRIDE":
        return <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />;
      case "COMMAND_EXECUTED":
      case "PAYMENT_LINK_CREATED":
        return <CreditCard className="w-3.5 h-3.5 text-indigo-400" />;
      case "REMINDER_DISPATCHED":
        return <Bell className="w-3.5 h-3.5 text-yellow-400" />;
      case "FINANCIAL_VERIFICATION":
      case "PAYMENT_CAPTURED":
      case "CASE_RECOVERED":
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  }

  function formatActionLabel(action: string): string {
    switch (action) {
      case "WEBHOOK_INGESTED":
        return "Payment Failure Ingested (HMAC Verified)";
      case "DIAGNOSIS_PERFORMED":
        return "ML P_ML & ERV Scored";
      case "STRATEGY_GENERATED":
        return "Gemini Strategy Formulated";
      case "POLICY_EVALUATED":
        return "Policy Engine Authorization";
      case "COMMAND_EXECUTED":
        return "Razorpay Test Link Generated";
      case "FINANCIAL_VERIFICATION":
        return "Financial Recovery Verified";
      default:
        return action.replace(/_/g, " ");
    }
  }

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#070b1e]/80 backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-4 bg-slate-950/60 border-b border-white/[0.06] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center w-6 h-6 rounded-full bg-emerald-950/80 border border-emerald-500/40">
            <Radio className={`w-3.5 h-3.5 ${isLive ? "text-emerald-400" : "text-slate-500"}`} />
            {isLive && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-tight">
                Live Telemetry Stream
              </span>
              <span className="text-[9px] px-2 py-0.2 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-300 font-bold uppercase tracking-wider">
                Audit Chain
              </span>
            </div>
            <p className="text-[10px] text-slate-400">Cryptographic non-repudiation ledger</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsLive(!isLive)}
            className={`text-[10px] px-2.5 py-1 rounded-lg border transition cursor-pointer font-bold tracking-wide ${
              isLive
                ? "bg-emerald-950/50 border-emerald-500/40 text-emerald-300 shadow-sm shadow-emerald-500/20"
                : "bg-slate-900 border-slate-700 text-slate-400"
            }`}
          >
            {isLive ? "POLLING 4s" : "PAUSED"}
          </button>
          <Link
            href="/audit"
            className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1 transition px-2 py-1 rounded-lg hover:bg-white/[0.04]"
          >
            <Eye className="w-3 h-3" /> Full Ledger
          </Link>
        </div>
      </div>

      {/* Events Stream */}
      <div className="divide-y divide-white/[0.04] max-h-[360px] overflow-y-auto p-1">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
            <span className="font-mono text-[11px]">Connecting to cryptographic audit stream...</span>
          </div>
        ) : events.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500">
            {error || "No telemetry events captured yet."}
          </div>
        ) : (
          events.map((ev, idx) => (
            <div
              key={ev.event_hash || `seq-${ev.sequence_number || idx}`}
              className="p-3 hover:bg-white/[0.03] transition-colors flex items-start gap-3 rounded-xl my-0.5"
            >
              {/* Event Icon Node */}
              <div className="w-7 h-7 rounded-lg bg-[#0c1228] border border-white/[0.08] flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                {getEventIcon(ev.action)}
              </div>

              {/* Event Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-slate-200 truncate">
                    {formatActionLabel(ev.action)}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono shrink-0">
                    {formatDate(ev.created_at)}
                  </span>
                </div>

                <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px]">
                  {/* Sequence Number */}
                  <span className="font-mono px-1.5 py-0.2 rounded bg-slate-900/80 border border-slate-800 text-slate-400 font-bold">
                    #{ev.sequence_number}
                  </span>

                  {/* Actor Badge */}
                  <span className="px-1.5 py-0.2 rounded bg-indigo-950/40 border border-indigo-500/30 text-indigo-300 font-mono">
                    {ev.actor_type || "SYSTEM"}
                  </span>

                  {/* Hash Snippet */}
                  <span className="font-mono text-slate-500 truncate max-w-[120px]" title={ev.event_hash}>
                    {ev.event_hash ? `${ev.event_hash.substring(0, 10)}...` : ""}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer Status */}
      <div className="p-2.5 bg-slate-950/40 border-t border-white/[0.04] text-[10px] text-slate-500 flex items-center justify-between px-4">
        <span className="font-mono">SHA-256 Non-Repudiation</span>
        <span className="text-emerald-400 font-semibold flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Tamper Proof
        </span>
      </div>
    </div>
  );
}
