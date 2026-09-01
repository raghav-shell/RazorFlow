"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Zap, ArrowUpRight, RefreshCw } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { formatDate } from "@/lib/utils";

export default function DecisionsExplorerPage() {
  const [decisions, setDecisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadDecisions() {
    try {
      const data = await apiClient.listDecisions("demo-store", 50, 0);
      setDecisions(data.items || []);
    } catch (err) {
      console.error("Failed to load decisions:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDecisions();
  }, []);

  return (
    <div className="space-y-8 pb-28 max-w-7xl mx-auto px-2 sm:px-4">
      {/* Title Header */}
      <section className="pt-4 pb-2 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
            <Zap className="w-3.5 h-3.5 text-[#bf5af2]" />
            <span className="text-xs font-medium text-[#86868b]">AI vs Policy Registry</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-white">
            Decisions Intelligence
          </h1>
          <p className="text-sm text-[#86868b] leading-relaxed">
            Historical register of AI strategy recommendations evaluated against deterministic merchant guardrails.
          </p>
        </div>

        <button
          onClick={loadDecisions}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition cursor-pointer shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#bf5af2]" : ""}`} />
          <span>Refresh Decisions</span>
        </button>
      </section>

      {/* Decisions Table */}
      <div className="apple-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-white/[0.06] text-[#86868b] font-medium text-[11px]">
              <tr>
                <th className="py-3.5 px-5">Order Reference</th>
                <th className="py-3.5 px-5">AI Strategy Candidate</th>
                <th className="py-3.5 px-5">Policy Verdict</th>
                <th className="py-3.5 px-5">Authorized Action</th>
                <th className="py-3.5 px-5">Decided At</th>
                <th className="py-3.5 px-5 text-right">Dossier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-white">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-[#86868b]">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#0071e3]" />
                    <span>Loading decisions...</span>
                  </td>
                </tr>
              ) : decisions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-[#86868b]">
                    No decision records recorded yet. Launch a demo scenario to generate decisions.
                  </td>
                </tr>
              ) : (
                decisions.map((d) => (
                  <tr key={d.decision_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-4 px-5">
                      <div className="font-mono font-semibold text-white text-xs">
                        {d.external_order_id}
                      </div>
                      <div className="text-[10px] text-[#86868b] font-mono mt-0.5">
                        {d.amount_formatted} • Attempt #{d.attempt_number}
                      </div>
                    </td>

                    <td className="py-4 px-5">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-medium text-white px-2 py-0.5 rounded-md bg-white/[0.06] font-mono">
                          {d.ai_recommended_action}
                        </span>
                        <span className="text-[10px] text-[#86868b] font-mono">
                          {(d.ai_confidence * 100).toFixed(0)}% conf
                        </span>
                      </div>
                      {d.ai_reasoning && (
                        <p className="text-[10px] text-[#86868b] max-w-xs truncate mt-1">
                          {d.ai_reasoning}
                        </p>
                      )}
                    </td>

                    <td className="py-4 px-5">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${
                          d.policy_verdict === "APPROVED"
                            ? "bg-[#30d158]/10 border-[#30d158]/30 text-[#30d158]"
                            : d.policy_verdict === "ESCALATED"
                            ? "bg-[#bf5af2]/10 border-[#bf5af2]/30 text-[#bf5af2]"
                            : "bg-white/10 border-white/20 text-white"
                        }`}
                      >
                        {d.policy_verdict}
                      </span>
                    </td>

                    <td className="py-4 px-5">
                      <span className="font-semibold text-white text-xs font-mono">
                        {d.authorized_action}
                      </span>
                    </td>

                    <td className="py-4 px-5 text-[#86868b] font-mono text-[11px]">
                      {formatDate(d.decided_at)}
                    </td>

                    <td className="py-4 px-5 text-right">
                      <Link
                        href={`/cases/${d.case_id}`}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-white/[0.05] hover:bg-white/15 border border-white/[0.08] text-white font-medium transition text-xs cursor-pointer"
                      >
                        <span>Inspect</span>
                        <ArrowUpRight className="w-3 h-3 text-[#86868b]" />
                      </Link>
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
