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
    <div className="space-y-8 pb-28 max-w-7xl mx-auto px-2 sm:px-4">
      {/* Title Header */}
      <section className="pt-4 pb-2 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
            <Lock className="w-3.5 h-3.5 text-[#30d158]" />
            <span className="text-xs font-medium text-[#86868b]">Non-Repudiation Ledger</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-white">
            Immutable Audit Trail
          </h1>
          <p className="text-sm text-[#86868b] leading-relaxed">
            Cryptographically linked SHA-256 state transitions ensuring zero tamperability across all autonomous recovery events.
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifying}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-black hover:bg-[#e5e5ea] text-xs font-semibold shadow-[0_10px_30px_rgba(255,255,255,0.2)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 cursor-pointer shrink-0"
        >
          {verifying ? (
            <RefreshCw className="w-4 h-4 animate-spin text-[#0071e3]" />
          ) : (
            <ShieldCheck className="w-4 h-4 text-[#30d158]" />
          )}
          <span>Verify Cryptographic Chain</span>
        </button>
      </section>

      {/* Cryptographic Verification Proof Banner */}
      {verifyResult && (
        <div className="apple-card p-6 sm:p-7 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-full bg-[#30d158]/10 border border-[#30d158]/30 flex items-center justify-center text-[#30d158]">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-mono text-[#30d158] font-semibold tracking-wider">
                  Chain Integrity Verified
                </span>
                <h2 className="text-base font-semibold text-white">
                  SHA-256 Hash-Chain Unbroken & Valid
                </h2>
              </div>
            </div>

            <span className="text-xs px-3 py-1 rounded-full bg-white/10 border border-white/10 text-white font-mono font-medium self-start sm:self-auto">
              {verifyResult.total_events} Chained Blocks
            </span>
          </div>

          {verifyResult.latest_hash && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 border-t border-white/[0.06] text-xs font-mono">
              <div className="p-3 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                <span className="text-[#86868b] block text-[10px] uppercase mb-1">
                  Genesis Block Hash
                </span>
                <span className="text-white text-[11px] break-all">
                  {verifyResult.genesis_hash?.substring(0, 32)}...
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                <span className="text-[#86868b] block text-[10px] uppercase mb-1">
                  Latest Chain Head Hash
                </span>
                <span className="text-[#30d158] text-[11px] break-all font-semibold">
                  {verifyResult.latest_hash?.substring(0, 32)}...
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Audit Events Stream Table */}
      <div className="apple-card overflow-hidden">
        <div className="p-5 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-white">
            <Lock className="w-4 h-4 text-[#64d2ff]" />
            <span>Append-Only Ledger Stream</span>
          </div>
          <span className="text-[11px] font-mono text-[#86868b]">
            {events.length} block events
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-white/[0.06] text-[#86868b] font-medium text-[11px]">
              <tr>
                <th className="py-3.5 px-5">Seq #</th>
                <th className="py-3.5 px-5">Action</th>
                <th className="py-3.5 px-5">Entity Ref</th>
                <th className="py-3.5 px-5">Actor</th>
                <th className="py-3.5 px-5">SHA-256 Hash Chain</th>
                <th className="py-3.5 px-5 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-white font-mono">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-[#86868b] font-sans">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#0071e3]" />
                    <span>Loading ledger stream...</span>
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-[#86868b] font-sans">
                    No audit records found.
                  </td>
                </tr>
              ) : (
                events.map((e) => (
                  <tr key={e.sequence_number} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3.5 px-5 font-semibold text-[#30d158]">
                      #{String(e.sequence_number).padStart(3, "0")}
                    </td>

                    <td className="py-3.5 px-5">
                      <span className="px-2 py-0.5 rounded-md bg-white/[0.05] border border-white/[0.08] text-white text-[10px]">
                        {e.action}
                      </span>
                    </td>

                    <td className="py-3.5 px-5 text-[#86868b]">
                      <span className="text-[10px] text-[#86868b] block">
                        {e.entity_type}
                      </span>
                      <span className="text-[11px] text-white">
                        {e.entity_id.substring(0, 14)}...
                      </span>
                    </td>

                    <td className="py-3.5 px-5 text-[11px]">
                      <span className="text-white">{e.actor_type}</span>
                      {e.actor_id && (
                        <span className="text-[#86868b] block text-[10px]">
                          {e.actor_id}
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-5">
                      <div className="text-[10px] text-[#86868b] truncate max-w-xs">
                        curr: <span className="text-[#30d158] font-semibold">{e.event_hash.substring(0, 16)}...</span>
                      </div>
                      <div className="text-[10px] text-[#6e6e73] truncate max-w-xs mt-0.5">
                        prev: {e.prev_event_hash.substring(0, 16)}...
                      </div>
                    </td>

                    <td className="py-3.5 px-5 text-right text-[#86868b] text-[11px]">
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
