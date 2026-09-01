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
      tagColor: "bg-emerald-950 text-emerald-300 border-emerald-500/30",
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
      tagColor: "bg-amber-950 text-amber-300 border-amber-500/30",
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
      tagColor: "bg-purple-950 text-purple-300 border-purple-500/30",
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
      tagColor: "bg-cyan-950 text-cyan-300 border-cyan-500/30",
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl my-8 rounded-2xl border border-slate-800 bg-[#0d1322] shadow-2xl p-6 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-5 pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/20 shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                Evaluator Demo Scenarios
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950 border border-blue-500/30 text-blue-300 font-semibold">
                  3-Minute Judge Showcase
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Trigger real backend orchestration pipelines to inspect AI reasoning, deterministic guardrails, and cryptographic reconciliation in action.
              </p>
            </div>
          </div>

          <button
            onClick={handleResetDemoCohort}
            disabled={resetting}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition shrink-0 flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${resetting ? "animate-spin text-blue-400" : ""}`} />
            <span>Reset Demo Cohort (22 Cases)</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/60 border border-rose-500/40 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Reset Success Alert */}
        {resetMessage && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{resetMessage}</span>
          </div>
        )}

        {/* Scenario Result Card */}
        {result && (
          <div className="mb-6 p-4 rounded-xl bg-blue-950/40 border border-blue-500/30 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-300 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Scenario Executed Successfully
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-semibold font-mono">
                Status: {result.final_status}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <div>
                <span className="text-slate-400 block text-[10px]">Order ID</span>
                <span className="font-mono font-semibold text-white">{result.order_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Amount</span>
                <span className="font-semibold text-white">{result.amount_formatted}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">AI Suggested</span>
                <span className="font-semibold text-purple-300">{result.ai_action}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Policy Verdict</span>
                <span className="font-semibold text-emerald-300">{result.policy_verdict}</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pt-1">
              <button
                type="button"
                onClick={() => {
                  onClose();
                  router.push(`/cases/${result.case_id}`);
                }}
                className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-md shadow-blue-500/20"
              >
                <span>Inspect Full Case Dossier</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <Link
                href={`/pay/${result.case_id}`}
                onClick={onClose}
                className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
              >
                <span>Open Payment Checkout Simulator</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* Scenarios Grid */}
        <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            const isLoading = loadingScenario === sc.id;

            return (
              <div
                key={sc.id}
                className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/40 hover:bg-slate-900/50 hover:border-slate-700 transition space-y-2.5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                      <Icon className={`w-4 h-4 ${sc.iconColor}`} />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-white">{sc.title}</h3>
                      <span
                        className={`inline-block text-[10px] px-2 py-0.2 rounded border font-semibold mt-0.5 ${sc.tagColor}`}
                      >
                        {sc.tag}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleLaunchScenario(sc.id)}
                    disabled={isLoading}
                    className="px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-300 hover:bg-blue-600 hover:text-white text-xs font-bold transition flex items-center gap-1.5 shrink-0 disabled:opacity-50 cursor-pointer"
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
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-1.5 text-[10px] pt-1 font-mono">
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80">
                    <span className="text-slate-400 block font-semibold text-[9px] uppercase">
                      1. Input
                    </span>
                    <span className="text-slate-300 line-clamp-2">{sc.input}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80">
                    <span className="text-purple-400 block font-semibold text-[9px] uppercase">
                      2. AI & ML
                    </span>
                    <span className="text-purple-200 line-clamp-2">{sc.decision}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80">
                    <span className="text-amber-400 block font-semibold text-[9px] uppercase">
                      3. Policy
                    </span>
                    <span className="text-amber-200 line-clamp-2">{sc.policy}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80">
                    <span className="text-blue-400 block font-semibold text-[9px] uppercase">
                      4. Execution
                    </span>
                    <span className="text-blue-200 line-clamp-2">{sc.execution}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80">
                    <span className="text-emerald-400 block font-semibold text-[9px] uppercase">
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
