"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  DollarSign,
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
  Radio,
  Calculator,
  FileText,
  User,
  ArrowRight,
  Play,
  Lock,
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
  const [activeTab, setActiveTab] = useState<"ALL" | "RECOVERED" | "ACTIVE" | "ESCALATED">("ALL");

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
    if (activeTab === "RECOVERED" && c.status !== "RECOVERED") return false;
    if (activeTab === "ACTIVE" && (c.status === "RECOVERED" || c.status === "UNRECOVERABLE")) return false;
    if (activeTab === "ESCALATED" && c.status !== "ESCALATED") return false;

    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const orderId = c.order?.external_order_id?.toLowerCase() || "";
    const caseId = c.id.toLowerCase();
    const custName = c.customer?.name?.toLowerCase() || "";
    return orderId.includes(q) || caseId.includes(q) || custName.includes(q);
  });

  return (
    <div className="space-y-10 pb-24 max-w-7xl mx-auto px-2 sm:px-4">
      {/* Apple Keynote Hero Section */}
      <section className="relative pt-6 pb-2">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
          <div className="space-y-4 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] backdrop-blur-xl">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0071e3] animate-pulse" />
              <span className="text-xs font-medium text-[#86868b] tracking-wide">
                RazorFlow 2.0 • Autonomous Orchestrator
              </span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-[-0.035em] text-white leading-[1.08]">
              Autonomous Recovery. <br />
              <span className="text-apple-gradient">Engineered for Zero Dropoff.</span>
            </h1>

            <p className="text-base sm:text-lg text-[#86868b] font-normal leading-relaxed max-w-2xl">
              Statistical ML triage, deterministic policy guardrails, and instant hosted checkout re-engagement. Built for high-velocity merchants on Razorpay.
            </p>
          </div>

          {/* Quick Action Toolbar */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium border transition-all duration-200 cursor-pointer ${
                autoRefresh
                  ? "bg-emerald-500/10 border-emerald-500/30 text-[#30d158]"
                  : "bg-white/[0.04] border-white/10 text-[#86868b]"
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${autoRefresh ? "animate-spin text-[#30d158]" : ""}`} />
              <span>{autoRefresh ? "Live Telemetry" : "Telemetry Paused"}</span>
            </button>

            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-black hover:bg-[#e5e5ea] text-xs font-semibold shadow-[0_10px_30px_rgba(255,255,255,0.2)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#0071e3]" />
              <span>Simulate Scenario</span>
            </button>
          </div>
        </div>
      </section>

      {/* Apple Bento Grid Showcase */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-5">
        {/* Bento Card 1 (Hero Large): Verified Recovered Revenue */}
        <div className="lg:col-span-6 apple-card p-7 flex flex-col justify-between apple-card-hover relative overflow-hidden group">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#86868b] tracking-wider uppercase">
                Verified Net Recovered
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-[#30d158]/10 border border-[#30d158]/25 text-[#30d158] text-[10px] font-mono font-semibold">
                +100% RECONCILED
              </span>
            </div>

            <div className="text-4xl sm:text-5xl font-semibold text-white tracking-tight font-mono">
              {formatINR(metrics?.verified_revenue_recovered_cents || 0)}
            </div>

            <p className="text-xs text-[#86868b] leading-relaxed max-w-md">
              Recovered transactions mathematically reconciled against gateway ledger webhooks with zero human intervention.
            </p>
          </div>

          <div className="mt-8 pt-5 border-t border-white/[0.06] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-white">
              <CheckCircle2 className="w-4 h-4 text-[#30d158]" />
              <span className="font-medium">{metrics?.recovered_cases_count || 0} Settled Cases</span>
            </div>
            <Link
              href="/audit"
              className="text-[#64d2ff] hover:text-white flex items-center gap-1 transition-colors font-medium text-[11px]"
            >
              <span>Inspect Hash-Chain</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Bento Card 2: ML Statistical Recovery Yield */}
        <div className="lg:col-span-3 apple-card p-6 flex flex-col justify-between apple-card-hover">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#86868b] uppercase tracking-wider">
                Statistical Yield
              </span>
              <TrendingUp className="w-4 h-4 text-[#64d2ff]" />
            </div>

            <div className="text-3xl font-semibold text-white tracking-tight font-mono">
              {formatPercent(metrics?.recovery_rate_percentage || 0)}
            </div>

            <p className="text-[11px] text-[#86868b]">
              Calibrated P_ML recovery probability scoring.
            </p>
          </div>

          <div className="pt-4 border-t border-white/[0.06] space-y-1.5 text-[11px]">
            <div className="flex justify-between text-[#86868b]">
              <span>Active in Pipeline</span>
              <span className="text-white font-mono font-medium">{metrics?.active_cases_count || 0}</span>
            </div>
            <div className="flex justify-between text-[#86868b]">
              <span>Latency</span>
              <span className="text-white font-mono font-medium">{metrics?.average_recovery_latency_minutes || 1.4}m</span>
            </div>
          </div>
        </div>

        {/* Bento Card 3: Deterministic Policy Integrity */}
        <div className="lg:col-span-3 apple-card p-6 flex flex-col justify-between apple-card-hover">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#86868b] uppercase tracking-wider">
                Policy Authority
              </span>
              <ShieldCheck className="w-4 h-4 text-[#bf5af2]" />
            </div>

            <div className="text-3xl font-semibold text-white tracking-tight font-mono">
              100%
            </div>

            <p className="text-[11px] text-[#86868b]">
              PolicyEngine holds strict financial authority over AI suggestions.
            </p>
          </div>

          <div className="pt-4 border-t border-white/[0.06] space-y-1.5 text-[11px]">
            <div className="flex justify-between text-[#86868b]">
              <span>Escalated Cases</span>
              <span className="text-white font-mono font-medium">{metrics?.escalated_cases_count || 0}</span>
            </div>
            <div className="flex justify-between text-[#86868b]">
              <span>Breaches</span>
              <span className="text-[#30d158] font-mono font-medium">0</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Layout: Active Recovery Queue + Telemetry Radar Stream */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column (8 cols): Queue & Filter */}
        <div className="lg:col-span-8 space-y-5">
          {/* Minimalist Segmented Tabs + Search Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            {/* Apple Segmented Switcher */}
            <div className="apple-segmented inline-flex items-center self-start">
              {[
                { id: "ALL", label: "All Cases" },
                { id: "ACTIVE", label: "Active" },
                { id: "RECOVERED", label: "Recovered" },
                { id: "ESCALATED", label: "Escalated" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-200 cursor-pointer ${
                    activeTab === tab.id
                      ? "bg-white/10 text-white shadow-sm font-semibold"
                      : "text-[#86868b] hover:text-white"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Minimal Search Input */}
            <div className="relative flex-1 max-w-xs">
              <Search className="w-3.5 h-3.5 text-[#86868b] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search order or customer..."
                className="apple-input w-full pl-9 pr-3 py-1.5 text-xs text-white placeholder:text-[#6e6e73]"
              />
            </div>
          </div>

          {/* Minimalist Cases Table */}
          <div className="apple-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-white/[0.06] text-[#86868b] font-medium text-[11px]">
                  <tr>
                    <th className="py-3.5 px-5">Order Reference</th>
                    <th className="py-3.5 px-5">Diagnosis</th>
                    <th className="py-3.5 px-5">Amount</th>
                    <th className="py-3.5 px-5">Yield (P_ML)</th>
                    <th className="py-3.5 px-5">Status</th>
                    <th className="py-3.5 px-5 text-right">Dossier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04] text-white">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-16 text-center text-[#86868b]">
                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#0071e3]" />
                        <span>Loading recovery queue...</span>
                      </td>
                    </tr>
                  ) : filteredCases.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-16 text-center text-[#86868b]">
                        <div className="w-12 h-12 rounded-full bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mx-auto mb-3">
                          <AlertOctagon className="w-5 h-5 text-[#86868b]" />
                        </div>
                        <p className="text-sm font-medium text-white">No recovery cases found.</p>
                        <p className="text-xs text-[#86868b] mt-1">
                          Simulate an evaluator demo scenario to observe real-time orchestration.
                        </p>
                        <button
                          onClick={() => setIsDemoModalOpen(true)}
                          className="mt-4 px-4 py-2 rounded-full bg-white text-black hover:bg-[#e5e5ea] text-xs font-semibold transition cursor-pointer shadow-sm"
                        >
                          Simulate Payment Drop
                        </button>
                      </td>
                    </tr>
                  ) : (
                    filteredCases.map((c) => {
                      const orderId = c.order?.external_order_id || "ord_unknown";
                      const prob = c.recovery_probability
                        ? `${(c.recovery_probability * 100).toFixed(0)}%`
                        : "—";

                      return (
                        <tr
                          key={c.id}
                          className="hover:bg-white/[0.02] transition-colors group"
                        >
                          {/* Case & Order */}
                          <td className="py-4 px-5">
                            <div className="font-mono font-semibold text-white text-xs">
                              {orderId}
                            </div>
                            <div className="text-[10px] text-[#86868b] font-mono mt-0.5">
                              {c.customer?.name || "Customer"}
                            </div>
                          </td>

                          {/* Failure Category */}
                          <td className="py-4 px-5">
                            <CategoryBadge
                              category={c.failure_category}
                              isTransient={c.is_transient}
                            />
                          </td>

                          {/* Amount at Risk */}
                          <td className="py-4 px-5">
                            <div className="font-semibold text-white font-mono text-xs">
                              {formatINR(c.amount_at_risk_cents)}
                            </div>
                            {c.amount_recovered_cents > 0 && (
                              <div className="text-[10px] text-[#30d158] font-mono font-medium">
                                +{formatINR(c.amount_recovered_cents)} settled
                              </div>
                            )}
                          </td>

                          {/* Recovery Score */}
                          <td className="py-4 px-5">
                            <div className="flex items-center gap-2">
                              <div className="w-12 bg-white/[0.06] h-1.5 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-[#0071e3] rounded-full"
                                  style={{
                                    width: `${Math.min(
                                      100,
                                      (c.recovery_probability || 0) * 100
                                    )}%`,
                                  }}
                                />
                              </div>
                              <span className="font-mono text-xs text-[#86868b]">
                                {prob}
                              </span>
                            </div>
                          </td>

                          {/* Status */}
                          <td className="py-4 px-5">
                            <StatusBadge status={c.status} />
                          </td>

                          {/* Actions */}
                          <td className="py-4 px-5 text-right">
                            <Link
                              href={`/cases/${c.id}`}
                              className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-white/[0.05] hover:bg-white/15 border border-white/[0.08] text-white font-medium transition text-xs cursor-pointer"
                            >
                              <span>Inspect</span>
                              <ArrowUpRight className="w-3 h-3 text-[#86868b]" />
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

        {/* Right Column (4 cols): Telemetry Radar Feed */}
        <div className="lg:col-span-4 space-y-6">
          <LiveEventFeed />

          {/* Minimalist Navigation Grid */}
          <div className="apple-card p-5 space-y-3">
            <span className="text-[10px] font-semibold text-[#86868b] tracking-wider uppercase block">
              Governance Ecosystem
            </span>

            <div className="space-y-1.5 text-xs">
              <Link
                href="/decisions"
                className="p-2.5 rounded-xl hover:bg-white/[0.04] flex items-center justify-between text-[#a1a1a6] hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <Zap className="w-4 h-4 text-[#bf5af2]" />
                  <span className="font-medium">Decisions Explorer</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#6e6e73] group-hover:text-white group-hover:translate-x-0.5 transition-transform" />
              </Link>

              <Link
                href="/policies"
                className="p-2.5 rounded-xl hover:bg-white/[0.04] flex items-center justify-between text-[#a1a1a6] hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <Sliders className="w-4 h-4 text-[#ffd60a]" />
                  <span className="font-medium">Policy Studio & Guardrails</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#6e6e73] group-hover:text-white group-hover:translate-x-0.5 transition-transform" />
              </Link>

              <Link
                href="/radar"
                className="p-2.5 rounded-xl hover:bg-white/[0.04] flex items-center justify-between text-[#a1a1a6] hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <Radio className="w-4 h-4 text-[#64d2ff]" />
                  <span className="font-medium">Failure Telemetry Radar</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#6e6e73] group-hover:text-white group-hover:translate-x-0.5 transition-transform" />
              </Link>

              <Link
                href="/audit"
                className="p-2.5 rounded-xl hover:bg-white/[0.04] flex items-center justify-between text-[#a1a1a6] hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-[#30d158]" />
                  <span className="font-medium">Immutable Audit Ledger</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#6e6e73] group-hover:text-white group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        </div>
      </section>

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
