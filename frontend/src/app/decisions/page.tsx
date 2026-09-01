"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Zap, Bot, Shield, ArrowUpRight, RefreshCw, Filter } from "lucide-react";
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
    <div className="space-y-8 pb-20 max-w-7xl mx-auto">
      {/* Title Header */}
      <div className="p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-gradient-to-br from-[#120722]/90 via-[#070b1a]/90 to-[#040711]/90 backdrop-blur-2xl shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Zap className="w-3.5 h-3.5 text-purple-400" />
              AI vs Policy Audit Trail
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Decisions <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">Intelligence Explorer</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Complete historical registry of AI strategy recommendations evaluated against deterministic merchant guardrails.
          </p>
        </div>

        <button
          onClick={loadDecisions}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 border border-white/[0.08] hover:border-purple-500/40 hover:bg-slate-800 text-slate-200 text-xs font-bold transition cursor-pointer shadow-lg shadow-black/40 shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-purple-400" : ""}`} />
          Refresh Decisions
        </button>
      </div>

      {/* Decisions Table */}
      <div className="rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-white/[0.06] text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-4 px-5">Case & Order</th>
                <th className="py-4 px-5">AI Strategy Candidate</th>
                <th className="py-4 px-5">Policy Verdict</th>
                <th className="py-4 px-5">Authorized Action</th>
                <th className="py-4 px-5">Decided At</th>
                <th className="py-4 px-5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-500">
                    <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-purple-500" />
                    <p className="text-xs font-bold">Loading decision logs...</p>
                  </td>
                </tr>
              ) : decisions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-400">
                    No decision records recorded yet. Launch a demo scenario to generate decisions.
                  </td>
                </tr>
              ) : (
                decisions.map((d) => (
                  <tr key={d.decision_id} className="hover:bg-purple-500/[0.03] transition-colors">
                    <td className="py-4 px-5">
                      <div className="font-mono font-bold text-white text-xs">
                        {d.external_order_id}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        {d.amount_formatted} • Attempt #{d.attempt_number}
                      </div>
                    </td>

                    <td className="py-4 px-5">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold text-purple-300 bg-purple-950/70 border border-purple-500/30 px-2.5 py-0.5 rounded-lg font-mono">
                          {d.ai_recommended_action}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono font-bold">
                          {(d.ai_confidence * 100).toFixed(0)}% conf
                        </span>
                      </div>
                      {d.ai_reasoning && (
                        <p className="text-[10px] text-slate-400 max-w-xs truncate mt-1">
                          {d.ai_reasoning}
                        </p>
                      )}
                    </td>

                    <td className="py-4 px-5">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold border font-mono ${
                          d.policy_verdict === "APPROVED"
                            ? "bg-emerald-950/80 border-emerald-500/40 text-emerald-300 shadow-[0_0_8px_rgba(16,185,129,0.2)]"
                            : d.policy_verdict === "ESCALATED"
                            ? "bg-purple-950/80 border-purple-500/40 text-purple-300 shadow-[0_0_8px_rgba(168,85,247,0.2)]"
                            : "bg-blue-950/80 border-blue-500/40 text-blue-300"
                        }`}
                      >
                        {d.policy_verdict}
                      </span>
                      {d.policy_rule_triggered && (
                        <div className="text-[10px] text-amber-300 font-mono mt-1 font-semibold">
                          {d.policy_rule_triggered}
                        </div>
                      )}
                    </td>

                    <td className="py-4 px-5">
                      <span className="font-bold text-white text-xs font-mono">
                        {d.authorized_action}
                      </span>
                    </td>

                    <td className="py-4 px-5 text-slate-400 font-mono text-[11px]">
                      {formatDate(d.decided_at)}
                    </td>

                    <td className="py-4 px-5 text-right">
                      <Link
                        href={`/cases/${d.case_id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-white/[0.08] hover:bg-purple-600 hover:border-purple-500 text-slate-200 hover:text-white font-bold transition text-xs shadow-sm cursor-pointer"
                      >
                        <span>Dossier</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
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
