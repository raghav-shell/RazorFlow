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
    <div className="space-y-6 pb-16">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-emerald-400" />
            Immutable Audit Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident, cryptographically chained SHA-256 financial audit trail recording all recovery actions and state transitions.
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifying}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow-md shadow-emerald-500/20 disabled:opacity-50 cursor-pointer"
        >
          {verifying ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <ShieldCheck className="w-3.5 h-3.5" />
          )}
          Verify Cryptographic Hash-Chain
        </button>
      </div>

      {/* Cryptographic Verification Proof Banner */}
      {verifyResult && (
        <div
          className={`p-4 rounded-xl border ${
            verifyResult.is_valid
              ? "bg-emerald-950/40 border-emerald-500/40"
              : "bg-rose-950/40 border-rose-500/40"
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  verifyResult.is_valid
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "bg-rose-500/20 text-rose-400"
                }`}
              >
                {verifyResult.is_valid ? (
                  <ShieldCheck className="w-6 h-6" />
                ) : (
                  <ShieldAlert className="w-6 h-6" />
                )}
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                  Cryptographic Integrity Status
                </span>
                <h2 className="text-base font-bold text-white">
                  {verifyResult.status === "SECURE_UNBROKEN_CHAIN"
                    ? "Cryptographic Hash-Chain Unbroken & Valid"
                    : "Tamper Detected in Audit Sequence"}
                </h2>
              </div>
            </div>

            <span className="text-xs px-2.5 py-1 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-bold font-mono">
              {verifyResult.total_events} Blocked Events
            </span>
          </div>

          {verifyResult.latest_hash && (
            <div className="mt-3 pt-3 border-t border-emerald-900/40 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
              <div>
                <span className="text-slate-400 block text-[10px]">
                  Genesis Block Hash:
                </span>
                <span className="text-slate-300 text-[11px] break-all">
                  {verifyResult.genesis_hash?.substring(0, 32)}...
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">
                  Latest Verified Chain Head Hash:
                </span>
                <span className="text-emerald-300 text-[11px] break-all">
                  {verifyResult.latest_hash?.substring(0, 32)}...
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Audit Events Stream */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1322] shadow-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            Append-Only Audit Stream
          </h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {events.length} events
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Seq #</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">SHA-256 Hash</th>
                <th className="py-3 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-500" />
                    Loading audit trail...
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No audit records found yet. Trigger actions to populate ledger.
                  </td>
                </tr>
              ) : (
                events.map((e) => (
                  <tr key={e.sequence_number} className="hover:bg-slate-800/30 transition">
                    <td className="py-3.5 px-4 font-bold text-emerald-400">
                      #{e.sequence_number}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-200 font-bold text-[11px]">
                        {e.action}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-300">
                      <span className="text-[10px] text-slate-500 block">
                        {e.entity_type}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {e.entity_id.substring(0, 12)}...
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-300 text-[11px]">
                      {e.actor_type}
                      {e.actor_id && (
                        <span className="text-slate-500 block text-[10px]">
                          {e.actor_id}
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="text-[10px] text-slate-400 truncate max-w-xs">
                        curr: <span className="text-emerald-400">{e.event_hash.substring(0, 16)}...</span>
                      </div>
                      <div className="text-[10px] text-slate-600 truncate max-w-xs">
                        prev: {e.prev_event_hash.substring(0, 16)}...
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-right text-slate-400 text-[11px]">
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
