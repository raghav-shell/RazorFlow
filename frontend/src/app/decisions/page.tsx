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
    <div className="space-y-6 pb-16">
      {/* Title */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Zap className="w-6 h-6 text-purple-400" />
            Decisions Explorer
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-950 border border-purple-500/30 text-purple-300 font-semibold">
              AI vs Policy History
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete historical registry of AI strategy recommendations evaluated against deterministic merchant guardrails.
          </p>
        </div>

        <button
          onClick={loadDecisions}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Decisions Table */}
      <div className="rounded-xl border border-slate-800 bg-[#0d1322] shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Case & Order</th>
                <th className="py-3 px-4">AI Recommended Action</th>
                <th className="py-3 px-4">Policy Verdict</th>
                <th className="py-3 px-4">Authorized Action</th>
                <th className="py-3 px-4">Decided At</th>
                <th className="py-3 px-4 text-right">View Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-purple-500" />
                    Loading decision logs...
                  </td>
                </tr>
              ) : decisions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No decision records recorded yet. Launch a demo scenario to generate decisions.
                  </td>
                </tr>
              ) : (
                decisions.map((d) => (
                  <tr key={d.decision_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3.5 px-4">
                      <div className="font-mono font-bold text-white">
                        {d.external_order_id}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        {d.amount_formatted} • Attempt #{d.attempt_number}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] font-semibold text-purple-300 bg-purple-950/60 border border-purple-500/30 px-2 py-0.5 rounded">
                          {d.ai_recommended_action}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          ({(d.ai_confidence * 100).toFixed(0)}%)
                        </span>
                      </div>
                      {d.ai_reasoning && (
                        <p className="text-[10px] text-slate-400 max-w-xs truncate mt-0.5">
                          {d.ai_reasoning}
                        </p>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold border ${
                          d.policy_verdict === "APPROVED"
                            ? "bg-emerald-950/80 border-emerald-500/40 text-emerald-300"
                            : d.policy_verdict === "ESCALATED"
                            ? "bg-purple-950/80 border-purple-500/40 text-purple-300"
                            : "bg-blue-950/80 border-blue-500/40 text-blue-300"
                        }`}
                      >
                        {d.policy_verdict}
                      </span>
                      {d.policy_rule_triggered && (
                        <div className="text-[10px] text-amber-300 font-mono mt-0.5">
                          {d.policy_rule_triggered}
                        </div>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="font-bold text-white text-xs">
                        {d.authorized_action}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                      {formatDate(d.decided_at)}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/cases/${d.case_id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-purple-600 text-slate-200 hover:text-white font-semibold transition text-xs"
                      >
                        Inspect
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
