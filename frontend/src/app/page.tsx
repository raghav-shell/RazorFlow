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
  Building,
  User,
  ArrowRight,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { MetricSummary, RecoveryCase } from "@/lib/api/types";
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
    <div className="space-y-8 pb-20">
      {/* Hero Financial Cockpit Header */}
      <div className="relative p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-gradient-to-br from-[#090e24]/90 via-[#070b1a]/90 to-[#040711]/90 backdrop-blur-2xl shadow-2xl overflow-hidden">
        {/* Ambient Top Light */}
        <div className="absolute top-0 right-1/4 w-96 h-32 bg-gradient-to-b from-blue-500/15 via-indigo-500/5 to-transparent blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                Live Revenue Cockpit
              </span>
              <span className="px-3 py-1 rounded-full bg-slate-900/80 border border-white/[0.08] text-slate-300 text-xs font-mono">
                Store: demo-store
              </span>
            </div>
            
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight">
              Autonomous Revenue Recovery <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">Orchestrator</span>
            </h1>
            
            <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
              Real-time payment failure ingestion, ML recovery probability, Gemini AI advisory strategy, deterministic policy authorization, and cryptographic settlement reconciliation.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Auto Refresh Toggle */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold border transition duration-200 cursor-pointer ${
                autoRefresh
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300 shadow-sm shadow-emerald-500/20"
                  : "bg-slate-900 border-slate-700 text-slate-400"
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${autoRefresh ? "animate-spin text-emerald-400" : ""}`} />
              <span>{autoRefresh ? "Live 5s" : "Paused"}</span>
            </button>

            {/* Run Demo CTA */}
            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="relative group flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:via-indigo-500 hover:to-purple-500 text-white text-xs font-black shadow-lg shadow-blue-500/30 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] cursor-pointer border border-white/20"
            >
              <Sparkles className="w-4 h-4 text-cyan-200" />
              <span>Run Recovery Demo</span>
            </button>
          </div>
        </div>
      </div>

      {/* 6-Stage Narrative Lifecycle Stepper */}
      <div className="p-4 rounded-2xl bg-[#070b1c]/80 border border-white/[0.06] backdrop-blur-xl shadow-lg overflow-x-auto">
        <div className="flex items-center justify-between min-w-[850px] text-xs font-mono">
          {/* Step 1 */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300">
            <DollarSign className="w-3.5 h-3.5 text-rose-400" />
            <span className="font-bold">1. FAILED PAYMENT</span>
          </div>
          <span className="text-slate-600">➔</span>

          {/* Step 2 */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-cyan-300">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-bold">2. CASE DETECTED</span>
          </div>
          <span className="text-slate-600">➔</span>

          {/* Step 3 */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-950/30 border border-purple-500/30 text-purple-300">
            <Bot className="w-3.5 h-3.5 text-purple-400" />
            <span className="font-bold">3. ML + GEMINI ADVISORY</span>
          </div>
          <span className="text-slate-600">➔</span>

          {/* Step 4 */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-300">
            <Sliders className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-bold">4. POLICY AUTHORITY</span>
          </div>
          <span className="text-slate-600">➔</span>

          {/* Step 5 */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-950/30 border border-blue-500/30 text-blue-300">
            <Zap className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-bold">5. RAZORPAY EXECUTION</span>
          </div>
          <span className="text-slate-600">➔</span>

          {/* Step 6 */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 shadow-sm shadow-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-bold">6. VERIFIED RECOVERY</span>
          </div>
        </div>
      </div>

      {/* Hero Financial KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Verified Recovered Revenue (Hero) */}
        <div className="relative p-5 rounded-2xl border border-emerald-500/40 bg-gradient-to-br from-emerald-950/40 via-[#0a1226]/90 to-[#070b1c]/90 backdrop-blur-xl shadow-xl overflow-hidden group hover:border-emerald-400 transition-all duration-300">
          <div className="flex items-center justify-between text-emerald-300 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Verified Recovered</span>
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-emerald-400 tracking-tight font-mono">
            {formatINR(metrics?.verified_revenue_recovered_cents || 0)}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs pt-3 border-t border-white/[0.06]">
            <span className="text-slate-300 font-semibold">
              {metrics?.recovered_cases_count || 0} Settled Cases
            </span>
            <span className="font-mono text-[10px] text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded-full border border-emerald-500/40 font-bold">
              100% Reconciled
            </span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400" />
        </div>

        {/* Card 2: Revenue at Risk */}
        <div className="relative p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-br from-rose-950/20 via-[#0a1226]/80 to-[#070b1c]/80 backdrop-blur-xl shadow-xl overflow-hidden hover:border-rose-500/40 transition-all duration-300">
          <div className="flex items-center justify-between text-rose-300 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Revenue at Risk</span>
            <div className="w-7 h-7 rounded-lg bg-rose-500/15 border border-rose-500/30 flex items-center justify-center">
              <DollarSign className="w-4 h-4 text-rose-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-white tracking-tight font-mono">
            {formatINR(metrics?.revenue_at_risk_cents || 0)}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs pt-3 border-t border-white/[0.06]">
            <span className="text-slate-400 font-medium">
              {metrics?.active_cases_count || 0} Active Failures
            </span>
            <span className="font-mono text-[10px] text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded-full border border-rose-500/30">
              In Pipeline
            </span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 to-amber-500 opacity-80" />
        </div>

        {/* Card 3: Net Recovery Rate */}
        <div className="relative p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-br from-blue-950/20 via-[#0a1226]/80 to-[#070b1c]/80 backdrop-blur-xl shadow-xl overflow-hidden hover:border-blue-500/40 transition-all duration-300">
          <div className="flex items-center justify-between text-blue-300 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Recovery Yield</span>
            <div className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-blue-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-blue-400 tracking-tight font-mono">
            {formatPercent(metrics?.recovery_rate_percentage || 0)}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs pt-3 border-t border-white/[0.06]">
            <span className="text-slate-400">Net Profit Uplift:</span>
            <span className="font-mono font-bold text-slate-200">
              {formatINR(metrics?.net_recovered_revenue_cents || 0)}
            </span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500" />
        </div>

        {/* Card 4: Autonomous Velocity */}
        <div className="relative p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-br from-purple-950/20 via-[#0a1226]/80 to-[#070b1c]/80 backdrop-blur-xl shadow-xl overflow-hidden hover:border-purple-500/40 transition-all duration-300">
          <div className="flex items-center justify-between text-purple-300 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Intervention Velocity</span>
            <div className="w-7 h-7 rounded-lg bg-purple-500/15 border border-purple-500/30 flex items-center justify-center">
              <Clock className="w-4 h-4 text-purple-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-white tracking-tight font-mono">
            {metrics?.average_recovery_latency_minutes || 0}{" "}
            <span className="text-sm font-normal text-slate-400">min avg</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs pt-3 border-t border-white/[0.06]">
            <span className="px-2 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-500/30 text-[10px] font-bold">
              {metrics?.escalated_cases_count || 0} Escalated
            </span>
            <span className="text-slate-400 text-[10px]">
              {metrics?.awaiting_action_count || 0} In Cooldown
            </span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-indigo-500 to-pink-500" />
        </div>
      </div>

      {/* Main Grid: Pipeline Table + Live Event Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column (8 cols): Pipeline Table */}
        <div className="lg:col-span-8 space-y-4">
          {/* Search & Filter Controls */}
          <div className="p-4 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-xl flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by Order ID, Case UUID, or Customer..."
                className="w-full pl-10 pr-4 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition shadow-inner"
              />
            </div>

            {/* Status Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              {[
                { id: "ALL", label: "All Cases" },
                { id: "DETECTED", label: "Detected" },
                { id: "APPROVED", label: "Approved" },
                { id: "WAITING_EXTERNAL", label: "Waiting" },
                { id: "RECOVERED", label: "Recovered" },
                { id: "ESCALATED", label: "Escalated" },
              ].map((st) => (
                <button
                  key={st.id}
                  onClick={() => setSelectedStatus(st.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all duration-200 cursor-pointer ${
                    selectedStatus === st.id
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/20"
                      : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800"
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>
          </div>

          {/* Table Card */}
          <div className="rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white tracking-tight">
                    Active Revenue Recovery Queue
                  </h2>
                  <p className="text-[11px] text-slate-400">
                    Displaying {filteredCases.length} prioritized cases
                  </p>
                </div>
              </div>

              <Link
                href="/calculator"
                className="text-xs text-emerald-400 hover:text-emerald-300 font-bold flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 transition hover:bg-emerald-950/70"
              >
                <Calculator className="w-3.5 h-3.5" /> ROI Calculator
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-white/[0.06] text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3.5 px-4">Case & Order</th>
                    <th className="py-3.5 px-4">Failure Cause</th>
                    <th className="py-3.5 px-4">Amount at Risk</th>
                    <th className="py-3.5 px-4">Recovery (P)</th>
                    <th className="py-3.5 px-4">AI vs Policy</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04] text-slate-300">
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="py-16 text-center text-slate-500">
                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
                        <span className="font-mono">Loading live recovery pipeline...</span>
                      </td>
                    </tr>
                  ) : filteredCases.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-16 text-center text-slate-400">
                        <AlertOctagon className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                        <p className="text-sm font-bold text-slate-300">
                          No recovery cases found.
                        </p>
                        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                          Launch an evaluator demo scenario to observe real-time orchestration.
                        </p>
                        <button
                          onClick={() => setIsDemoModalOpen(true)}
                          className="mt-4 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold transition cursor-pointer shadow-lg shadow-blue-500/20"
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
                          className="hover:bg-white/[0.03] transition-colors group"
                        >
                          {/* Case & Order */}
                          <td className="py-3.5 px-4">
                            <div className="font-mono font-bold text-white group-hover:text-blue-400 transition-colors">
                              {orderId}
                            </div>
                            <div className="text-[10px] text-slate-500 font-mono">
                              {c.id.substring(0, 14)}...
                            </div>
                            {c.customer?.name && (
                              <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1">
                                <User className="w-3 h-3 text-slate-500" />
                                <span>{c.customer.name}</span>
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
                            <div className="font-black text-white text-sm font-mono">
                              {formatINR(c.amount_at_risk_cents)}
                            </div>
                            {c.amount_recovered_cents > 0 && (
                              <div className="text-[10px] text-emerald-400 font-bold font-mono">
                                +{formatINR(c.amount_recovered_cents)} recovered
                              </div>
                            )}
                          </td>

                          {/* Recovery Score */}
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-2">
                              <div className="w-12 bg-slate-900 h-2 rounded-full overflow-hidden border border-white/[0.06]">
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
                              <span className="font-bold text-slate-200 font-mono text-xs">
                                {prob}
                              </span>
                            </div>
                            {c.expected_recovery_value_cents && (
                              <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                                ERV: {formatINR(c.expected_recovery_value_cents)}
                              </div>
                            )}
                          </td>

                          {/* AI vs Policy */}
                          <td className="py-3.5 px-4">
                            {latestDecision ? (
                              <div className="space-y-1">
                                <div>
                                  <span className="text-[9px] font-bold text-purple-300 bg-purple-950/60 border border-purple-500/30 px-2 py-0.5 rounded-md uppercase tracking-wider">
                                    AI: {latestDecision.ai_recommended_action}
                                  </span>
                                </div>
                                <div className="text-[10px] text-slate-400 flex items-center gap-1">
                                  <span>Policy:</span>
                                  <span className="font-bold text-emerald-400">
                                    {latestDecision.policy_verdict}
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <span className="text-slate-500 font-mono">—</span>
                            )}
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-4">
                            <StatusBadge status={c.status} />
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right">
                            <Link
                              href={`/cases/${c.id}`}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-white/[0.08] hover:bg-blue-600 hover:border-blue-500 text-slate-200 hover:text-white font-bold transition text-xs cursor-pointer shadow-sm group-hover:border-blue-500/40"
                            >
                              <span>Inspect</span>
                              <ArrowUpRight className="w-3.5 h-3.5" />
                            </Link>
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
        <div className="lg:col-span-4 space-y-6">
          <LiveEventFeed />

          {/* Quick Governance Hub Card */}
          <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              Governance & Analytics Hub
            </h3>

            <div className="space-y-2.5 text-xs">
              <Link
                href="/decisions"
                className="p-3 rounded-xl bg-slate-950/60 border border-white/[0.06] hover:border-purple-500/40 flex items-center justify-between text-slate-300 hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-purple-950/80 border border-purple-500/30 flex items-center justify-center text-purple-400">
                    <Zap className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="font-bold block">Decisions Explorer</span>
                    <span className="text-[10px] text-slate-400">AI vs Policy matrix</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-purple-400 group-hover:translate-x-0.5 transition-transform" />
              </Link>

              <Link
                href="/policies"
                className="p-3 rounded-xl bg-slate-950/60 border border-white/[0.06] hover:border-amber-500/40 flex items-center justify-between text-slate-300 hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-amber-950/80 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <Sliders className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="font-bold block">Policy Studio & Sandbox</span>
                    <span className="text-[10px] text-slate-400">Deterministic guardrails</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-amber-400 group-hover:translate-x-0.5 transition-transform" />
              </Link>

              <Link
                href="/radar"
                className="p-3 rounded-xl bg-slate-950/60 border border-white/[0.06] hover:border-amber-500/40 flex items-center justify-between text-slate-300 hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                    <Radio className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="font-bold block">Failure Concentration Radar</span>
                    <span className="text-[10px] text-slate-400">Root-cause yield telemetry</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-transform" />
              </Link>

              <Link
                href="/audit"
                className="p-3 rounded-xl bg-slate-950/60 border border-white/[0.06] hover:border-emerald-500/40 flex items-center justify-between text-slate-300 hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="font-bold block">Immutable Audit Ledger</span>
                    <span className="text-[10px] text-slate-400">SHA-256 cryptographic chain</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-transform" />
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
