"use client";

import React, { useEffect, useState } from "react";
import {
  FileText,
  ShieldCheck,
  ShieldAlert,
  Lock,
  RefreshCw,
  Hash,
  CheckCircle2,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { AuditEventItem, AuditVerifyResult } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

export default function AuditLedgerPage() {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [verifyResult, setVerifyResult] = useState<AuditVerifyResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  async function loadAuditData() {
    try {
      const [eventsData, verifyData] = await Promise.all([
        apiClient.listAuditEvents("demo-store", undefined, 50, 0),
        apiClient.verifyAuditChain("demo-store"),
      ]);
      setEvents(eventsData.items || []);
      setVerifyResult(verifyData);
    } catch (err) {
      console.error("Failed to load audit ledger:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAuditData();
  }, []);

  async function handleVerifyChain() {
    setVerifying(true);
    try {
      const data = await apiClient.verifyAuditChain("demo-store");
      setVerifyResult(data);
    } catch (err) {
      console.error("Verification failed:", err);
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div className="space-y-8 pb-20 max-w-7xl mx-auto">
      {/* Title Header */}
      <div className="p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-gradient-to-br from-[#06140e]/90 via-[#070b1a]/90 to-[#040711]/90 backdrop-blur-2xl shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Lock className="w-3.5 h-3.5 text-emerald-400" />
              SHA-256 Merkle Chain Integrity
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Immutable <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">Audit Ledger</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Tamper-evident, cryptographically chained SHA-256 financial audit trail recording all recovery actions and state transitions.
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifying}
          className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-slate-950 font-black text-xs transition shadow-xl shadow-emerald-500/20 disabled:opacity-50 cursor-pointer shrink-0 border border-white/20"
        >
          {verifying ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <ShieldCheck className="w-4 h-4" />
          )}
          Verify Hash-Chain
        </button>
      </div>

      {/* Cryptographic Verification Proof Banner */}
      {verifyResult && (
        <div
          className={`p-6 sm:p-7 rounded-3xl border shadow-2xl backdrop-blur-xl ${
            verifyResult.is_valid
              ? "bg-emerald-950/40 border-emerald-500/40 shadow-emerald-950/20"
              : "bg-rose-950/40 border-rose-500/40 shadow-rose-950/20"
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${
                  verifyResult.is_valid
                    ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-400 shadow-lg shadow-emerald-500/20"
                    : "bg-rose-500/20 border-rose-500/40 text-rose-400"
                }`}
              >
                {verifyResult.is_valid ? (
                  <ShieldCheck className="w-7 h-7" />
                ) : (
                  <ShieldAlert className="w-7 h-7" />
                )}
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400 font-mono">
                  Cryptographic Integrity Verification
                </span>
                <h2 className="text-lg font-black text-white">
                  {verifyResult.status === "SECURE_UNBROKEN_CHAIN"
                    ? "Cryptographic Hash-Chain Unbroken & Valid"
                    : "Tamper Detected in Audit Sequence"}
                </h2>
              </div>
            </div>

            <span className="text-xs px-3.5 py-1.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 font-black font-mono self-start sm:self-auto shadow-sm">
              {verifyResult.total_events} Chained Blocks
            </span>
          </div>

          {verifyResult.latest_hash && (
            <div className="mt-5 pt-5 border-t border-emerald-500/20 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-white/[0.06]">
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider mb-1">
                  Genesis Block Hash:
                </span>
                <span className="text-slate-300 text-[11px] break-all font-bold">
                  {verifyResult.genesis_hash?.substring(0, 32)}...
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-white/[0.06]">
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider mb-1">
                  Latest Chain Head Hash:
                </span>
                <span className="text-emerald-300 text-[11px] break-all font-bold">
                  {verifyResult.latest_hash?.substring(0, 32)}...
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Audit Events Stream */}
      <div className="rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl overflow-hidden">
        <div className="p-5 sm:p-6 border-b border-white/[0.06] flex items-center justify-between">
          <h2 className="text-sm font-black text-white uppercase tracking-wider flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
              <Lock className="w-4 h-4 text-emerald-400" />
            </div>
            <span>Append-Only Ledger Stream</span>
          </h2>
          <span className="text-xs px-3 py-1 rounded-full bg-slate-900 border border-white/[0.06] text-slate-400 font-mono font-bold">
            {events.length} block events
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-white/[0.06] text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-4 px-5">Seq #</th>
                <th className="py-4 px-5">Action</th>
                <th className="py-4 px-5">Entity Ref</th>
                <th className="py-4 px-5">Actor</th>
                <th className="py-4 px-5">SHA-256 Hash Chain</th>
                <th className="py-4 px-5 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-slate-300 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-500">
                    <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-emerald-500" />
                    <p className="text-xs font-bold font-sans">Loading immutable audit trail...</p>
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-400 font-sans">
                    No audit records found yet. Trigger actions to populate ledger.
                  </td>
                </tr>
              ) : (
                events.map((e) => (
                  <tr key={e.sequence_number} className="hover:bg-emerald-500/[0.02] transition-colors">
                    <td className="py-4 px-5 font-black text-emerald-400">
                      #{String(e.sequence_number).padStart(3, "0")}
                    </td>

                    <td className="py-4 px-5">
                      <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-white/[0.08] text-white font-bold text-[11px]">
                        {e.action}
                      </span>
                    </td>

                    <td className="py-4 px-5 text-slate-300">
                      <span className="text-[10px] text-slate-400 block font-semibold">
                        {e.entity_type}
                      </span>
                      <span className="text-[11px] text-slate-200">
                        {e.entity_id.substring(0, 14)}...
                      </span>
                    </td>

                    <td className="py-4 px-5 text-slate-300 text-[11px]">
                      <span className="font-bold text-white">{e.actor_type}</span>
                      {e.actor_id && (
                        <span className="text-slate-500 block text-[10px]">
                          {e.actor_id}
                        </span>
                      )}
                    </td>

                    <td className="py-4 px-5">
                      <div className="text-[10px] text-slate-400 truncate max-w-xs">
                        curr: <span className="text-emerald-400 font-bold">{e.event_hash.substring(0, 18)}...</span>
                      </div>
                      <div className="text-[10px] text-slate-600 truncate max-w-xs mt-0.5">
                        prev: {e.prev_event_hash.substring(0, 18)}...
                      </div>
                    </td>

                    <td className="py-4 px-5 text-right text-slate-400 text-[11px]">
                      {formatDate(e.created_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
