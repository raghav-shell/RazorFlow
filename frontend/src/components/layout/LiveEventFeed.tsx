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
        return "Payment Failure Ingested (HMAC Auth)";
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
    <div className="rounded-xl border border-slate-800 bg-[#0d1322] shadow-xl overflow-hidden">
      {/* Header */}
      <div className="p-3.5 bg-slate-950/70 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="relative flex items-center justify-center">
            <Radio className={`w-4 h-4 ${isLive ? "text-emerald-400" : "text-slate-500"}`} />
            {isLive && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            )}
          </div>
          <span className="text-xs font-bold text-white tracking-tight">
            Live Telemetry Feed
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950/80 border border-blue-500/30 text-blue-300 font-semibold">
            Audit Stream
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsLive(!isLive)}
            className={`text-[10px] px-2 py-0.5 rounded border transition cursor-pointer font-semibold ${
              isLive
                ? "bg-emerald-950/60 border-emerald-500/40 text-emerald-300"
                : "bg-slate-900 border-slate-700 text-slate-400"
            }`}
          >
            {isLive ? "Live (4s)" : "Paused"}
          </button>
          <Link
            href="/audit"
            className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1 transition"
          >
            <Eye className="w-3 h-3" /> Full Ledger
          </Link>
        </div>
      </div>

      {/* Events List */}
      <div className="divide-y divide-slate-800/50 max-h-[360px] overflow-y-auto">
        {loading ? (
          <div className="py-8 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            Connecting to audit stream...
          </div>
        ) : events.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No live events recorded yet. Run a demo scenario to see live stream.
          </div>
        ) : (
          events.map((ev) => (
            <div
              key={ev.event_hash || `seq-${ev.sequence_number}`}
              className="p-3 hover:bg-slate-800/20 transition flex items-start gap-2.5 text-xs"
            >
              <div className="mt-0.5 p-1 rounded-md bg-slate-900 border border-slate-800 shrink-0">
                {getEventIcon(ev.action)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-slate-200 truncate">
                    {formatActionLabel(ev.action)}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 shrink-0">
                    #{ev.sequence_number}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
                  <span className="font-mono text-slate-400">
                    Actor: {ev.actor_type.toLowerCase()} • {ev.actor_id}
                  </span>
                  <span>{formatDate(ev.created_at)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer Info */}
      <div className="p-2 bg-slate-950/90 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between px-3">
        <span>Sequential Cryptographic Hash Chain</span>
        <span className="font-mono text-emerald-400 font-semibold">SHA-256 Chained</span>
      </div>
    </div>
  );
}
