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
      const data = await apiClient.listAuditEvents("demo-store", undefined, 10, 0);
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
        return <Zap className="w-3.5 h-3.5 text-[#ffd60a]" />;
      case "DIAGNOSIS_PERFORMED":
      case "PROBABILITY_SCORED":
        return <Activity className="w-3.5 h-3.5 text-[#64d2ff]" />;
      case "STRATEGY_GENERATED":
      case "AI_RECOMMENDATION":
        return <Bot className="w-3.5 h-3.5 text-[#bf5af2]" />;
      case "POLICY_EVALUATED":
      case "POLICY_OVERRIDE":
        return <ShieldCheck className="w-3.5 h-3.5 text-[#0071e3]" />;
      case "COMMAND_EXECUTED":
      case "PAYMENT_LINK_CREATED":
        return <CreditCard className="w-3.5 h-3.5 text-[#64d2ff]" />;
      case "REMINDER_DISPATCHED":
        return <Bell className="w-3.5 h-3.5 text-[#ffd60a]" />;
      case "FINANCIAL_VERIFICATION":
      case "PAYMENT_CAPTURED":
      case "CASE_RECOVERED":
        return <CheckCircle2 className="w-3.5 h-3.5 text-[#30d158]" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-[#86868b]" />;
    }
  }

  function formatActionLabel(action: string): string {
    switch (action) {
      case "WEBHOOK_INGESTED":
        return "Webhook Ingested (HMAC Verified)";
      case "DIAGNOSIS_PERFORMED":
        return "ML P_ML & ERV Scored";
      case "STRATEGY_GENERATED":
        return "Gemini Advisory Strategy";
      case "POLICY_EVALUATED":
        return "Policy Engine Authorized";
      case "COMMAND_EXECUTED":
        return "Razorpay Test Link Generated";
      case "FINANCIAL_VERIFICATION":
        return "Financial Recovery Verified";
      default:
        return action.replace(/_/g, " ");
    }
  }

  return (
    <div className="apple-card overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#30d158] animate-pulse" />
          <span className="text-xs font-semibold text-white">Live Telemetry Feed</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsLive(!isLive)}
            className={`text-[10px] px-2.5 py-0.5 rounded-full border transition cursor-pointer font-mono font-medium ${
              isLive
                ? "bg-white/10 border-white/20 text-white"
                : "bg-white/[0.02] border-white/[0.06] text-[#86868b]"
            }`}
          >
            {isLive ? "LIVE 4s" : "PAUSED"}
          </button>
          <Link
            href="/audit"
            className="text-[10px] text-[#86868b] hover:text-white flex items-center gap-1 transition px-2 py-0.5 rounded-full hover:bg-white/[0.04]"
          >
            <Eye className="w-3 h-3" /> Ledger
          </Link>
        </div>
      </div>

      {/* Events Stream */}
      <div className="divide-y divide-white/[0.04] max-h-[340px] overflow-y-auto p-1">
        {loading ? (
          <div className="py-12 text-center text-xs text-[#86868b] flex flex-col items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-[#0071e3]" />
            <span className="text-[11px]">Connecting to telemetry stream...</span>
          </div>
        ) : events.length === 0 ? (
          <div className="py-12 text-center text-xs text-[#86868b]">
            {error || "No telemetry events captured yet."}
          </div>
        ) : (
          events.map((ev, idx) => (
            <div
              key={ev.event_hash || `seq-${ev.sequence_number || idx}`}
              className="p-3 hover:bg-white/[0.02] transition-colors flex items-start gap-3 rounded-2xl"
            >
              {/* Event Icon Node */}
              <div className="w-7 h-7 rounded-full bg-white/[0.04] border border-white/[0.08] flex items-center justify-center shrink-0 mt-0.5">
                {getEventIcon(ev.action)}
              </div>

              {/* Event Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-white truncate">
                    {formatActionLabel(ev.action)}
                  </span>
                  <span className="text-[10px] text-[#86868b] font-mono shrink-0">
                    {formatDate(ev.created_at)}
                  </span>
                </div>

                <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[10px]">
                  <span className="font-mono px-1.5 py-0.2 rounded-md bg-white/[0.05] text-[#86868b]">
                    #{ev.sequence_number}
                  </span>

                  <span className="px-1.5 py-0.2 rounded-md bg-white/[0.05] text-[#a1a1a6] font-mono">
                    {ev.actor_type || "SYSTEM"}
                  </span>

                  <span className="font-mono text-[#6e6e73] truncate max-w-[100px]" title={ev.event_hash}>
                    {ev.event_hash ? `${ev.event_hash.substring(0, 8)}...` : ""}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer Status */}
      <div className="p-2.5 bg-black/40 border-t border-white/[0.04] text-[10px] text-[#86868b] flex items-center justify-between px-4">
        <span className="font-mono">SHA-256 Merkle Chained</span>
        <span className="text-[#30d158] font-medium flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[#30d158]" /> Tamper-Proof
        </span>
      </div>
    </div>
  );
}
