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
  ChevronRight,
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
      subtitle: "Transient dropoff recovered via authentic Razorpay test checkout link",
      tag: "Happy Path",
      tagColor: "bg-[#30d158]/10 text-[#30d158] border-[#30d158]/30",
      icon: CheckCircle2,
      iconColor: "text-[#30d158]",
      steps: [
        { label: "1. Trigger", text: "UPI Auth dropoff on ₹4,500 order" },
        { label: "2. AI & ML", text: "P_ML = 0.78 • Gemini recommends PAYMENT_LINK" },
        { label: "3. Policy", text: "Approved: Within attempt ceiling & risk limits" },
        { label: "4. Execution", text: "Authentic Razorpay test link created & sent" },
        { label: "5. Outcome", text: "₹4,500 recovered • SHA-256 chained to audit" },
      ],
    },
    {
      id: "scenario_2",
      title: "Scenario 2: Transient Bank Outage Cooldown",
      subtitle: "Bank 503 error handled with automated cooldown to prevent customer spam",
      tag: "Outage Protection",
      tagColor: "bg-[#ffd60a]/10 text-[#ffd60a] border-[#ffd60a]/30",
      icon: AlertTriangle,
      iconColor: "text-[#ffd60a]",
      steps: [
        { label: "1. Trigger", text: "HDFC Bank UPI 503 Service Unavailable (₹2,800)" },
        { label: "2. AI & ML", text: "ML classifies transient outage • Recommends WAIT" },
        { label: "3. Policy", text: "Enforces 30-min cooldown to avoid spamming user" },
        { label: "4. Execution", text: "Case scheduled in WAITING_EXTERNAL queue" },
        { label: "5. Outcome", text: "Zero spam messages during active bank outage" },
      ],
    },
    {
      id: "scenario_3",
      title: "Scenario 3: High-Value Policy Override",
      subtitle: "High-value enterprise order strictly overridden by deterministic merchant guardrails",
      tag: "Policy Authority",
      tagColor: "bg-[#bf5af2]/10 text-[#bf5af2] border-[#bf5af2]/30",
      icon: ShieldAlert,
      iconColor: "text-[#bf5af2]",
      steps: [
        { label: "1. Trigger", text: "₹85,000 corporate payment dropoff (> ₹50k limit)" },
        { label: "2. AI Advisory", text: "Gemini suggests automated link (Advisory)" },
        { label: "3. Policy Override", text: "Policy Engine OVERRIDES: High-Value Rule triggered" },
        { label: "4. Execution", text: "Dispatches HUMAN_ESCALATION to key account manager" },
        { label: "5. Outcome", text: "AI strictly bounded by financial governance" },
      ],
    },
    {
      id: "scenario_4",
      title: "Scenario 4: AI Failure Fallback to Deterministic ERV",
      subtitle: "Zero pipeline downtime fallback when external LLM API is unavailable",
      tag: "Fault Tolerance",
      tagColor: "bg-[#64d2ff]/10 text-[#64d2ff] border-[#64d2ff]/30",
      icon: Cpu,
      iconColor: "text-[#64d2ff]",
      steps: [
        { label: "1. Trigger", text: "Simulated Gemini API timeout / partition (8.0s)" },
        { label: "2. Fallback", text: "Fallback to Deterministic ERV Mathematical Ranker" },
        { label: "3. Policy", text: "Policy authorizes highest ERV candidate seamlessly" },
        { label: "4. Execution", text: "Execution proceeds without stall (is_fallback=true)" },
        { label: "5. Outcome", text: "100% financial pipeline uptime guaranteed" },
      ],
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-xl overflow-y-auto">
      <div className="relative w-full max-w-4xl my-auto rounded-[28px] border border-white/[0.12] bg-[#0c0c10]/95 backdrop-blur-3xl shadow-[0_40px_100px_rgba(0,0,0,0.9)] p-6 sm:p-8 overflow-hidden">
        
        {/* Subtle Ambient Top Center Light */}
        <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-96 h-40 bg-[#0071e3]/20 blur-[90px] pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-[#86868b] hover:text-white p-2 rounded-full bg-white/[0.04] hover:bg-white/[0.1] border border-white/[0.08] transition cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-white/[0.08]">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-[#0071e3]/15 border border-[#0071e3]/30 flex items-center justify-center text-[#64d2ff] shadow-[0_0_20px_rgba(0,113,227,0.25)] shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-xl font-semibold text-white tracking-tight">
                  Evaluator Demo Showcase
                </h2>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-white/[0.08] border border-white/[0.1] text-[#86868b] font-mono uppercase tracking-wider">
                  3-Min Judge Demo
                </span>
              </div>
              <p className="text-xs text-[#86868b] mt-0.5">
                Execute live backend recovery pipelines to inspect AI reasoning, deterministic guardrails, and cryptographic reconciliation.
              </p>
            </div>
          </div>

          <button
            onClick={handleResetDemoCohort}
            disabled={resetting}
            className="px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] text-[#86868b] hover:text-white text-xs font-medium transition shrink-0 flex items-center gap-2 disabled:opacity-50 cursor-pointer self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${resetting ? "animate-spin text-[#0071e3]" : ""}`} />
            <span>Reset Demo Cohort</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-5 p-4 rounded-2xl bg-[#ff453a]/10 border border-[#ff453a]/30 text-xs text-[#ff453a] font-medium">
            {error}
          </div>
        )}

        {/* Reset Success Alert */}
        {resetMessage && (
          <div className="mb-5 p-4 rounded-2xl bg-[#30d158]/10 border border-[#30d158]/30 text-xs text-[#30d158] flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{resetMessage}</span>
          </div>
        )}

        {/* Scenario Result Card */}
        {result && (
          <div className="mb-6 p-5 rounded-2xl bg-white/[0.03] border border-[#0071e3]/40 shadow-[0_10px_30px_rgba(0,113,227,0.15)] space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#30d158]" />
                Scenario Executed Successfully
              </span>
              <span className="text-xs px-3 py-0.5 rounded-full bg-[#30d158]/10 border border-[#30d158]/30 text-[#30d158] font-mono font-medium">
                {result.final_status}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-black/50 p-4 rounded-xl border border-white/[0.06]">
              <div>
                <span className="text-[#86868b] block text-[10px] uppercase">Order Reference</span>
                <span className="font-mono font-semibold text-white text-xs">{result.order_id}</span>
              </div>
              <div>
                <span className="text-[#86868b] block text-[10px] uppercase">Amount</span>
                <span className="font-mono font-semibold text-white text-xs">{result.amount_formatted}</span>
              </div>
              <div>
                <span className="text-[#86868b] block text-[10px] uppercase">AI Suggested</span>
                <span className="font-medium text-[#bf5af2] text-xs">{result.ai_action}</span>
              </div>
              <div>
                <span className="text-[#86868b] block text-[10px] uppercase">Policy Verdict</span>
                <span className="font-semibold text-[#30d158] text-xs">{result.policy_verdict}</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-1">
              <button
                type="button"
                onClick={() => {
                  onClose();
                  router.push(`/cases/${result.case_id}`);
                }}
                className="px-4 py-2 rounded-full bg-white text-black hover:bg-[#e5e5ea] text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer shadow-md"
              >
                <span>Inspect Case Dossier</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <Link
                href={`/pay/${result.case_id}`}
                onClick={onClose}
                className="px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer"
              >
                <span>Open Hosted Checkout</span>
                <ExternalLink className="w-3.5 h-3.5 text-[#64d2ff]" />
              </Link>
            </div>
          </div>
        )}

        {/* Scenarios Grid */}
        <div className="space-y-4 max-h-[58vh] overflow-y-auto pr-1">
          {scenarios.map((sc) => {
            const Icon = sc.icon;
            const isLoading = loadingScenario === sc.id;

            return (
              <div
                key={sc.id}
                className="p-5 rounded-2xl border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/[0.15] transition-all duration-200 space-y-3.5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3.5">
                    <div className="p-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] shrink-0 mt-0.5">
                      <Icon className={`w-4 h-4 ${sc.iconColor}`} />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-semibold text-white">{sc.title}</h3>
                        <span
                          className={`text-[10px] px-2.5 py-0.5 rounded-full border font-medium ${sc.tagColor}`}
                        >
                          {sc.tag}
                        </span>
                      </div>
                      <p className="text-xs text-[#86868b] mt-0.5">
                        {sc.subtitle}
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleLaunchScenario(sc.id)}
                    disabled={isLoading}
                    className="px-4 py-2 rounded-full bg-white text-black hover:bg-[#e5e5ea] text-xs font-semibold transition flex items-center gap-1.5 shrink-0 disabled:opacity-50 cursor-pointer shadow-[0_4px_14px_rgba(255,255,255,0.15)] hover:scale-[1.02] active:scale-[0.98]"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-[#0071e3]" />
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

                {/* 5-Step Pipeline Flow with Clean Horizontal Stepper */}
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 pt-1">
                  {sc.steps.map((step, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-black/40 border border-white/[0.05] flex flex-col justify-between space-y-1"
                    >
                      <span className="text-[10px] text-[#86868b] font-mono font-medium">
                        {step.label}
                      </span>
                      <span className="text-[11px] text-white/90 leading-tight">
                        {step.text}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
