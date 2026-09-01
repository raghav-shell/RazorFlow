"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Cpu,
  ArrowRight,
  X,
  Loader2,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { DemoScenarioResult } from "@/lib/api/types";

interface DemoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DemoModal({ isOpen, onClose }: DemoModalProps) {
  const router = useRouter();
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [result, setResult] = useState<DemoScenarioResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const scenarios = [
    {
      id: "scenario_1",
      title: "Scenario 1: Autonomous Payment Link Recovery",
      tag: "Happy Path",
      tagColor: "bg-emerald-950/60 text-emerald-300 border-emerald-500/40",
      icon: CheckCircle2,
      iconColor: "text-emerald-400",
      input: "UPI Auth dropoff on ₹4,500 order (High-confidence customer)",
      decision: "ML P_ML = 0.78 • Gemini recommends PAYMENT_LINK",
      policy: "Policy authorizes link generation (Within risk & attempt ceiling)",
      execution: "Authentic Razorpay Test payment link created & dispatched",
      outcome: "Payment verified via webhook • ₹4,500 recovered • Chained to Audit",
    },
    {
      id: "scenario_2",
      title: "Scenario 2: Transient Bank Outage Cooldown",
      tag: "Outage Protection",
      tagColor: "bg-amber-950/60 text-amber-300 border-amber-500/40",
      icon: AlertTriangle,
      iconColor: "text-amber-400",
      input: "HDFC Bank UPI 503 Service Unavailable timeout on ₹2,800 order",
      decision: "ML detects transient outage pattern • Favors WAIT_AND_REASSESS",
      policy: "Policy enforces 30-min cooldown window to prevent customer spam",
      execution: "Case placed in WAITING_EXTERNAL • Scheduled Celery reassessment",
      outcome: "Zero spam messages sent during active bank outage",
    },
    {
      id: "scenario_3",
      title: "Scenario 3: High-Value Policy Override",
      tag: "Policy Authority",
      tagColor: "bg-purple-950/60 text-purple-300 border-purple-500/40",
      icon: ShieldAlert,
      iconColor: "text-purple-400",
      input: "₹85,000 corporate payment fails (Exceeds ₹50,000 threshold)",
      decision: "Gemini recommends automated PAYMENT_LINK (Advisory only)",
      policy: "Policy Engine OVERRIDES: RULE_HIGH_VALUE_ESCALATION triggered",
      execution: "Dispatches HUMAN_ESCALATION for account manager review",
      outcome: "AI strictly bounded by deterministic merchant financial governance",
    },
    {
      id: "scenario_4",
      title: "Scenario 4: AI Failure Fallback to Deterministic ERV",
      tag: "Fault Tolerance",
      tagColor: "bg-cyan-950/60 text-cyan-300 border-cyan-500/40",
      icon: Cpu,
      iconColor: "text-cyan-400",
      input: "Simulated Gemini AI timeout / API partition (8.0s limit)",
      decision: "Pipeline transparently falls back to Deterministic ERV Ranker",
      policy: "Policy authorizes top candidate without business stall",
      execution: "Execution proceeds seamlessly • is_fallback=true logged",
      outcome: "100% financial pipeline uptime even during AI provider outages",
    },
  ];

  async function handleLaunchScenario(scenarioId: string) {
    setLoadingScenario(scenarioId);
    setError(null);
    setResult(null);
    setResetMessage(null);

    try {
      const res = await apiClient.launchDemoScenario(scenarioId);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || "Failed to launch scenario");
    } finally {
      setLoadingScenario(null);
    }
  }

  async function handleResetDemoCohort() {
    setResetting(true);
    setError(null);
    setResetMessage(null);
    setResult(null);

    try {
      const res = await apiClient.resetAndSeedCohort();
      setResetMessage(
        `Cohort reset completed! Seeded ${res.total_seeded || 22} realistic demo cases across all failure categories.`
      );
      router.refresh();
    } catch (err: any) {
      setError(err?.message || "Failed to reset demo cohort.");
    } finally {
      setResetting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl my-8 rounded-3xl border border-white/[0.1] bg-[#070b1e] shadow-2xl p-6 sm:p-8 overflow-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 right-1/4 w-80 h-32 bg-blue-500/15 blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 transition cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-5 border-b border-white/[0.08]">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25 shrink-0 border border-white/20">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-black text-white flex items-center gap-2">
                Evaluator Demo Showcase
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-300 font-bold uppercase tracking-wider">
                  3-Min Judge Demo
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Trigger real backend orchestration pipelines to inspect AI reasoning, deterministic guardrails, and cryptographic reconciliation.
              </p>
            </div>
          </div>

          <button
            onClick={handleResetDemoCohort}
            disabled={resetting}
            className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-white/[0.08] hover:bg-slate-800 text-slate-300 text-xs font-bold transition shrink-0 flex items-center gap-2 disabled:opacity-50 cursor-pointer shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${resetting ? "animate-spin text-blue-400" : ""}`} />
            <span>Reset Demo Cohort (22 Cases)</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-5 p-4 rounded-xl bg-rose-950/60 border border-rose-500/40 text-xs text-rose-300 font-medium">
            {error}
          </div>
        )}

        {/* Reset Success Alert */}
        {resetMessage && (
          <div className="mb-5 p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-xs text-emerald-300 flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{resetMessage}</span>
          </div>
        )}

        {/* Scenario Result Card */}
        {result && (
          <div className="mb-6 p-5 rounded-2xl bg-gradient-to-br from-blue-950/50 via-[#0a1226]/90 to-[#070b1c]/90 border border-blue-500/40 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-300 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Scenario Executed Successfully
              </span>
              <span className="text-xs px-3 py-1 rounded-full bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-bold font-mono">
                Status: {result.final_status}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-950/80 p-4 rounded-xl border border-white/[0.06]">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Order ID</span>
                <span className="font-mono font-bold text-white text-xs">{result.order_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Amount</span>
                <span className="font-mono font-bold text-white text-xs">{result.amount_formatted}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">AI Suggested</span>
                <span className="font-bold text-purple-300 text-xs">{result.ai_action}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Policy Verdict</span>
                <span className="font-bold text-emerald-300 text-xs">{result.policy_verdict}</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-1">
              <button
                type="button"
                onClick={() => {
                  onClose();
                  router.push(`/cases/${result.case_id}`);
                }}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition flex items-center gap-2 cursor-pointer shadow-lg shadow-blue-500/25"
              >
                <span>Inspect Full Case Dossier</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <Link
                href={`/pay/${result.case_id}`}
                onClick={onClose}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition flex items-center gap-2 cursor-pointer shadow-lg shadow-emerald-500/25"
              >
                <span>Open Payment Checkout Simulator</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* Scenarios Grid */}
        <div className="space-y-4 max-h-[480px] overflow-y-auto pr-1">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            const isLoading = loadingScenario === sc.id;

            return (
              <div
                key={sc.id}
                className="p-5 rounded-2xl border border-white/[0.06] bg-slate-950/50 hover:bg-slate-900/60 hover:border-blue-500/30 transition-all duration-200 space-y-3"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-[#0c1228] border border-white/[0.08]">
                      <Icon className={`w-5 h-5 ${sc.iconColor}`} />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">{sc.title}</h3>
                      <span
                        className={`inline-block text-[10px] px-2.5 py-0.5 rounded-full border font-bold uppercase tracking-wider mt-1 ${sc.tagColor}`}
                      >
                        {sc.tag}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleLaunchScenario(sc.id)}
                    disabled={isLoading}
                    className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold transition flex items-center gap-2 shrink-0 disabled:opacity-50 cursor-pointer shadow-md shadow-blue-500/20"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Running...</span>
                      </>
                    ) : (
                      <>
                        <span>Execute Scenario</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>

                {/* 5-Step Pipeline Flow */}
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-[10px] pt-1 font-mono">
                  <div className="p-2.5 rounded-xl bg-[#080d20] border border-white/[0.05]">
                    <span className="text-slate-400 block font-bold text-[9px] uppercase tracking-wider mb-0.5">
                      1. Input
                    </span>
                    <span className="text-slate-300 line-clamp-2">{sc.input}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#080d20] border border-white/[0.05]">
                    <span className="text-purple-400 block font-bold text-[9px] uppercase tracking-wider mb-0.5">
                      2. AI & ML
                    </span>
                    <span className="text-purple-200 line-clamp-2">{sc.decision}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#080d20] border border-white/[0.05]">
                    <span className="text-amber-400 block font-bold text-[9px] uppercase tracking-wider mb-0.5">
                      3. Policy
                    </span>
                    <span className="text-amber-200 line-clamp-2">{sc.policy}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#080d20] border border-white/[0.05]">
                    <span className="text-blue-400 block font-bold text-[9px] uppercase tracking-wider mb-0.5">
                      4. Execution
                    </span>
                    <span className="text-blue-200 line-clamp-2">{sc.execution}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#080d20] border border-white/[0.05]">
                    <span className="text-emerald-400 block font-bold text-[9px] uppercase tracking-wider mb-0.5">
                      5. Outcome
                    </span>
                    <span className="text-emerald-200 line-clamp-2">{sc.outcome}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
