"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  DollarSign,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  AlertOctagon,
  Clock,
  Zap,
  Bot,
  Sliders,
  ExternalLink,
  Radio,
  Calculator,
  FileText,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { MetricSummary, RecoveryCase, RecoveryCaseStatus } from "@/lib/api/types";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CategoryBadge } from "@/components/ui/CategoryBadge";
import { DemoModal } from "@/components/demo/DemoModal";
import { LiveEventFeed } from "@/components/layout/LiveEventFeed";

export default function CommandCenterPage() {
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

  async function loadData() {
    try {
      const [metricData, casesData] = await Promise.all([
        apiClient.getMetrics("demo-store"),
        apiClient.listCases("demo-store", {
          status: selectedStatus === "ALL" ? undefined : selectedStatus,
          limit: 50,
        }),
      ]);
      setMetrics(metricData);
      setCases(casesData.cases || []);
    } catch (err) {
      console.error("Failed to load command center data:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    if (!autoRefresh) return;
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [selectedStatus, autoRefresh]);

  const filteredCases = cases.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const orderId = c.order?.external_order_id?.toLowerCase() || "";
    const caseId = c.id.toLowerCase();
    const custName = c.customer?.name?.toLowerCase() || "";
    return orderId.includes(q) || caseId.includes(q) || custName.includes(q);
  });

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header / Welcome */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              Recovery Command Center
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-950 border border-blue-500/30 text-blue-400 font-semibold">
              Live Dashboard
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time financial telemetry, AI root-cause reasoning, deterministic policy authorization, and cryptographic settlement verification.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition cursor-pointer ${
              autoRefresh
                ? "bg-emerald-950/60 border-emerald-500/40 text-emerald-300"
                : "bg-slate-900 border-slate-700 text-slate-400"
            }`}
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${autoRefresh ? "animate-spin" : ""}`}
            />
            {autoRefresh ? "Auto-refreshing (5s)" : "Auto-refresh off"}
          </button>

          {/* Primary Action Button */}
          <button
            onClick={() => setIsDemoModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-xs font-bold shadow-xl shadow-purple-500/25 transition cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>Run Recovery Demo</span>
          </button>
        </div>
      </div>

      {/* Narrative Lifecycle Banner */}
      <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800/80 shadow-sm overflow-x-auto">
        <div className="flex items-center justify-between min-w-[760px] text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-1.5 text-rose-400 font-bold">
            <DollarSign className="w-3.5 h-3.5" />
            <span>1. REVENUE AT RISK</span>
          </div>
          <span className="text-slate-600">➔</span>
          <div className="flex items-center gap-1.5 text-cyan-400 font-bold">
            <Activity className="w-3.5 h-3.5" />
            <span>2. CASES ANALYZED</span>
          </div>
          <span className="text-slate-600">➔</span>
          <div className="flex items-center gap-1.5 text-purple-400 font-bold">
            <Bot className="w-3.5 h-3.5" />
            <span>3. AI + ML DECISIONING</span>
          </div>
          <span className="text-slate-600">➔</span>
          <div className="flex items-center gap-1.5 text-amber-400 font-bold">
            <Sliders className="w-3.5 h-3.5" />
            <span>4. POLICY AUTHORIZATION</span>
          </div>
          <span className="text-slate-600">➔</span>
          <div className="flex items-center gap-1.5 text-blue-400 font-bold">
            <Zap className="w-3.5 h-3.5" />
            <span>5. EXECUTION</span>
          </div>
          <span className="text-slate-600">➔</span>
          <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>6. VERIFIED RECOVERY</span>
          </div>
        </div>
      </div>

      {/* KPI Financial Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Verified Recovered (Hero) */}
        <div className="p-4 rounded-xl border border-emerald-500/40 bg-gradient-to-br from-emerald-950/40 via-[#0d1322] to-[#0d1322] shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-emerald-300 text-xs font-semibold mb-2">
            <span>Verified Recovered Revenue</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 tracking-tight">
            {formatINR(metrics?.verified_revenue_recovered_cents || 0)}
          </div>
          <div className="mt-2 flex items-center justify-between text-xs">
            <span className="text-emerald-300/80 font-medium">
              {metrics?.recovered_cases_count || 0} successful recoveries
            </span>
            <span className="font-mono text-[10px] text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-500/30">
              100% Reconciled
            </span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-cyan-500" />
        </div>

        {/* Card 2: Revenue at Risk */}
        <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322]/80 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Revenue at Risk</span>
            <DollarSign className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {formatINR(metrics?.revenue_at_risk_cents || 0)}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">
              {metrics?.active_cases_count || 0}
            </span>{" "}
            active failure cases
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 to-amber-500 opacity-75" />
        </div>

        {/* Card 3: Net Recovery Rate & Profit */}
        <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322]/80 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Net Recovery Rate</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-400 tracking-tight">
            {formatPercent(metrics?.recovery_rate_percentage || 0)}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
            <span>Net Profit Uplift:</span>
            <span className="font-semibold text-slate-200">
              {formatINR(metrics?.net_recovered_revenue_cents || 0)}
            </span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500" />
        </div>

        {/* Card 4: Action Pipeline & Latency */}
        <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322]/80 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Intervention Velocity</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {metrics?.average_recovery_latency_minutes || 0}{" "}
            <span className="text-sm font-normal text-slate-400">min avg</span>
          </div>
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span className="px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-500/30 text-[10px] font-semibold">
              {metrics?.escalated_cases_count || 0} Escalated
            </span>
            <span className="text-slate-400 text-[10px]">
              {metrics?.awaiting_action_count || 0} in cooldown
            </span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-pink-500" />
        </div>
      </div>

      {/* Main Grid: Pipeline Table + Live Event Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Pipeline Table */}
        <div className="lg:col-span-8 space-y-4">
          {/* Interactive Filters & Search */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 rounded-xl border border-slate-800 bg-slate-900/50">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by Order ID, Case UUID, or Customer name..."
                className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
            </div>

            {/* Status Filter Buttons */}
            <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
              {[
                { id: "ALL", label: "All" },
                { id: "DETECTED", label: "Detected" },
                { id: "APPROVED", label: "Approved" },
                { id: "WAITING_EXTERNAL", label: "Waiting" },
                { id: "RECOVERED", label: "Recovered" },
                { id: "ESCALATED", label: "Escalated" },
              ].map((st) => (
                <button
                  key={st.id}
                  onClick={() => setSelectedStatus(st.id)}
                  className={`px-2.5 py-1 rounded-md text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                    selectedStatus === st.id
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-slate-950 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>
          </div>

          {/* Table Container */}
          <div className="rounded-xl border border-slate-800 bg-[#0d1322] shadow-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-400" />
                Active Revenue Recovery Pipeline
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                  {filteredCases.length} records
                </span>
              </h2>

              <Link
                href="/calculator"
                className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1"
              >
                <Calculator className="w-3.5 h-3.5" /> ROI Calculator
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Case & Order</th>
                    <th className="py-3 px-4">Failure Category</th>
                    <th className="py-3 px-4">Amount at Risk</th>
                    <th className="py-3 px-4">Score (p)</th>
                    <th className="py-3 px-4">AI vs Policy</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-slate-500">
                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                        Loading live recovery pipeline...
                      </td>
                    </tr>
                  ) : filteredCases.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-slate-400">
                        <AlertOctagon className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                        <p className="text-sm font-semibold text-slate-300">
                          No recovery cases found.
                        </p>
                        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                          Launch an evaluator demo scenario to observe real-time orchestration.
                        </p>
                        <button
                          onClick={() => setIsDemoModalOpen(true)}
                          className="mt-4 px-3.5 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition cursor-pointer"
                        >
                          Run Recovery Demo
                        </button>
                      </td>
                    </tr>
                  ) : (
                    filteredCases.map((c) => {
                      const orderId = c.order?.external_order_id || "ord_unknown";
                      const latestDecision =
                        c.decisions && c.decisions.length > 0
                          ? c.decisions[0]
                          : null;
                      const prob = c.recovery_probability
                        ? `${(c.recovery_probability * 100).toFixed(0)}%`
                        : "—";

                      return (
                        <tr
                          key={c.id}
                          className="hover:bg-slate-800/30 transition group"
                        >
                          {/* Case & Order */}
                          <td className="py-3.5 px-4">
                            <div className="font-mono font-bold text-white group-hover:text-blue-400 transition">
                              {orderId}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono">
                              {c.id.substring(0, 13)}...
                            </div>
                            {c.customer?.name && (
                              <div className="text-[10px] text-slate-400 mt-0.5">
                                {c.customer.name}
                              </div>
                            )}
                          </td>

                          {/* Failure Category */}
                          <td className="py-3.5 px-4">
                            <CategoryBadge
                              category={c.failure_category}
                              isTransient={c.is_transient}
                            />
                            {c.diagnosis_reasoning && (
                              <div className="text-[10px] text-slate-400 line-clamp-1 max-w-xs mt-1">
                                {c.diagnosis_reasoning}
                              </div>
                            )}
                          </td>

                          {/* Amount at Risk */}
                          <td className="py-3.5 px-4">
                            <div className="font-bold text-white text-sm">
                              {formatINR(c.amount_at_risk_cents)}
                            </div>
                            {c.amount_recovered_cents > 0 && (
                              <div className="text-[10px] text-emerald-400 font-semibold">
                                +{formatINR(c.amount_recovered_cents)} recovered
                              </div>
                            )}
                          </td>

                          {/* Recovery Score */}
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-2">
                              <div className="w-10 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-blue-500 to-emerald-400"
                                  style={{
                                    width: `${Math.min(
                                      100,
                                      (c.recovery_probability || 0) * 100
                                    )}%`,
                                  }}
                                />
                              </div>
                              <span className="font-semibold text-slate-200">
                                {prob}
                              </span>
                            </div>
                            {c.expected_recovery_value_cents && (
                              <div className="text-[10px] text-slate-400 mt-0.5">
                                ERV: {formatINR(c.expected_recovery_value_cents)}
                              </div>
                            )}
                          </td>

                          {/* AI vs Policy */}
                          <td className="py-3.5 px-4">
                            {latestDecision ? (
                              <div className="space-y-0.5">
                                <div className="flex items-center gap-1.5">
                                  <span className="text-[10px] font-semibold text-purple-300 bg-purple-950/60 border border-purple-500/30 px-1.5 py-0.2 rounded">
                                    AI: {latestDecision.ai_recommended_action}
                                  </span>
                                </div>
                                <div className="text-[10px] text-slate-400">
                                  Policy:{" "}
                                  <span className="font-semibold text-emerald-400">
                                    {latestDecision.policy_verdict}
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <span className="text-slate-500">—</span>
                            )}
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-4">
                            <StatusBadge status={c.status} />
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <Link
                                href={`/cases/${c.id}`}
                                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-blue-600 text-slate-200 hover:text-white font-semibold transition text-xs cursor-pointer"
                              >
                                <span>Inspect</span>
                                <ArrowUpRight className="w-3 h-3" />
                              </Link>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Live Event Feed */}
        <div className="lg:col-span-4 space-y-4">
          <LiveEventFeed />

          {/* Quick Navigation Cards */}
          <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322] shadow-xl space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Quick Governance Actions
            </h3>

            <div className="space-y-2 text-xs">
              <Link
                href="/decisions"
                className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 flex items-center justify-between text-slate-300 hover:text-white transition"
              >
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-400" />
                  <span>Decisions Explorer</span>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>

              <Link
                href="/policies"
                className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 flex items-center justify-between text-slate-300 hover:text-white transition"
              >
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-amber-400" />
                  <span>Policy Studio & Sandbox</span>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>

              <Link
                href="/radar"
                className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 flex items-center justify-between text-slate-300 hover:text-white transition"
              >
                <div className="flex items-center gap-2">
                  <Radio className="w-4 h-4 text-amber-400" />
                  <span>Observed Failure Radar</span>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>

              <Link
                href="/audit"
                className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 flex items-center justify-between text-slate-300 hover:text-white transition"
              >
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-400" />
                  <span>Immutable Audit Ledger</span>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Evaluator Demo Modal */}
      <DemoModal
        isOpen={isDemoModalOpen}
        onClose={() => {
          setIsDemoModalOpen(false);
          loadData();
        }}
      />
    </div>
  );
}
