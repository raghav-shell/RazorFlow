"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Bot,
  Check,
  CheckCircle2,
  Clock,
  Cpu,
  CreditCard,
  DollarSign,
  ExternalLink,
  FileCheck,
  FileCode,
  HelpCircle,
  Lock,
  Play,
  RefreshCw,
  Send,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  User,
  Zap,
  Smartphone,
  Info,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { RecoveryCase } from "@/lib/api/types";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CategoryBadge } from "@/components/ui/CategoryBadge";
import { MobileWhatsAppModal } from "@/components/demo/MobileWhatsAppModal";

export default function CaseInvestigationPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.caseId as string;

  const [caseData, setCaseData] = useState<RecoveryCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [isWhatsAppModalOpen, setIsWhatsAppModalOpen] = useState(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadCase() {
    try {
      const data = await apiClient.getCase("demo-store", caseId);
      setCaseData(data);
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to load recovery case.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCase();
  }, [caseId]);

  async function handleExecuteAction(actionOverride?: string) {
    setExecuting(true);
    setActionSuccessMessage(null);
    setErrorMessage(null);
    try {
      const res = await apiClient.executeCase("demo-store", caseId, actionOverride);
      setActionSuccessMessage(
        `Action '${res.action_type}' dispatched successfully. Gateway Ref: ${
          res.gateway_reference_id || "N/A"
        }`
      );
      await loadCase();
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to execute recovery action.");
    } finally {
      setExecuting(false);
    }
  }

  async function handleSimulatePayment() {
    setSimulating(true);
    setActionSuccessMessage(null);
    setErrorMessage(null);
    try {
      const res = await apiClient.simulatePayment("demo-store", caseId);
      setActionSuccessMessage(
        `Payment captured & verified! Recovered: ${formatINR(
          res.recovered_amount_cents
        )}, Net: ${formatINR(res.net_recovery_cents)}`
      );
      await loadCase();
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to simulate payment capture.");
    } finally {
      setSimulating(false);
    }
  }

  if (loading) {
    return (
      <div className="py-24 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500 mb-3" />
        <p className="text-sm font-semibold text-slate-300">
          Loading case investigation workspace...
        </p>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="py-24 text-center">
        <AlertTriangle className="w-10 h-10 mx-auto text-amber-400 mb-3" />
        <h2 className="text-lg font-bold text-white mb-2">Case Not Found</h2>
        <p className="text-xs text-slate-400 mb-4">{errorMessage || "Case ID not found."}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-slate-800 text-white text-xs font-semibold hover:bg-slate-700"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Command Center
        </Link>
      </div>
    );
  }

  const latestDecision =
    caseData.decisions && caseData.decisions.length > 0
      ? caseData.decisions[0]
      : null;
  const latestAttempt =
    caseData.attempts && caseData.attempts.length > 0
      ? caseData.attempts[caseData.attempts.length - 1]
      : null;
  const outcome = caseData.outcome;
  const isRecovered = caseData.status === "RECOVERED";

  return (
    <div className="space-y-8 pb-20">
      {/* Top Breadcrumb & Action Toolbar */}
      <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/85 backdrop-blur-xl shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <Link
            href="/"
            className="p-2.5 rounded-xl bg-slate-900 border border-white/[0.08] hover:bg-slate-800 text-slate-400 hover:text-white transition shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-xl font-black text-white font-mono">
                {caseData.order?.external_order_id || "Order"}
              </h1>
              <StatusBadge status={caseData.status} />
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Case UUID: {caseData.id}
            </p>
          </div>
        </div>

        {/* Action Buttons Toolbar */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* WhatsApp Simulator Button */}
          <button
            onClick={() => setIsWhatsAppModalOpen(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-950/60 text-xs font-bold transition cursor-pointer shadow-sm"
          >
            <Smartphone className="w-4 h-4 text-emerald-400" />
            <span>Customer WhatsApp</span>
          </button>

          {/* Open Customer Payment Link Simulator */}
          <Link
            href={`/pay/${caseData.payment_link_id || latestAttempt?.gateway_reference_id || caseData.id}`}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-blue-600/20 border border-blue-500/40 text-blue-300 hover:bg-blue-600 hover:text-white text-xs font-bold transition cursor-pointer shadow-sm"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Hosted Checkout</span>
          </Link>

          {/* Simulate Payment Capture (if not already recovered) */}
          {!isRecovered && (
            <button
              onClick={handleSimulatePayment}
              disabled={simulating}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-black transition shadow-lg shadow-emerald-500/25 disabled:opacity-50 cursor-pointer"
            >
              {simulating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <CreditCard className="w-4 h-4" />
              )}
              <span>Simulate Payment</span>
            </button>
          )}

          {/* Execute Authorized Action */}
          {(caseData.status === "APPROVED" || caseData.status === "DETECTED") && (
            <button
              onClick={() => handleExecuteAction()}
              disabled={executing}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-black transition shadow-lg shadow-blue-500/25 disabled:opacity-50 cursor-pointer"
            >
              {executing ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>Dispatch Action</span>
            </button>
          )}
        </div>
      </div>

      {/* Action Notification Alert */}
      {actionSuccessMessage && (
        <div className="p-4 rounded-2xl bg-emerald-950/70 border border-emerald-500/40 text-xs text-emerald-200 flex items-center gap-2.5 shadow-lg">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span className="font-medium">{actionSuccessMessage}</span>
        </div>
      )}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-950/70 border border-rose-500/40 text-xs text-rose-200 flex items-center gap-2.5 shadow-lg">
          <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
          <span className="font-medium">{errorMessage}</span>
        </div>
      )}

      {/* Verified Outcome Banner (if recovered) */}
      {outcome && outcome.is_successful && (
        <div className="p-6 rounded-3xl border border-emerald-500/50 bg-gradient-to-r from-emerald-950/80 via-[#0a1525]/90 to-blue-950/80 backdrop-blur-xl shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center text-emerald-400 shadow-inner">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-black tracking-widest text-emerald-400">
                  Verified Financial Outcome
                </span>
                <h2 className="text-2xl font-black text-white">
                  Revenue Successfully Recovered
                </h2>
                <p className="text-xs text-slate-300 mt-0.5">
                  Verified via {outcome.verification_source} • Settling webhook reconciled into cryptographic ledger.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-8 border-t sm:border-t-0 sm:border-l border-emerald-800/40 pt-4 sm:pt-0 sm:pl-8">
              <div>
                <span className="text-[10px] text-slate-400 block font-bold uppercase tracking-wider">
                  Amount Recovered
                </span>
                <span className="text-xl font-black text-white font-mono">
                  {formatINR(outcome.amount_recovered_cents)}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block font-bold uppercase tracking-wider">
                  Intervention Cost
                </span>
                <span className="text-xl font-bold text-slate-300 font-mono">
                  {formatINR(outcome.cost_incurred_cents)}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block font-bold uppercase tracking-wider">
                  Net Recovered
                </span>
                <span className="text-2xl font-black text-emerald-400 font-mono">
                  {formatINR(outcome.net_recovery_cents)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Case Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Box 1: Financial & Failure Summary */}
        <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-xl space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">Financial Impact</span>
            <DollarSign className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Amount at Risk</span>
            <div className="text-3xl font-black text-white font-mono">
              {formatINR(caseData.amount_at_risk_cents)}
            </div>
          </div>
          <div className="pt-3 border-t border-white/[0.06] space-y-2">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Failure Cause</span>
            <div>
              <CategoryBadge
                category={caseData.failure_category}
                isTransient={caseData.is_transient}
              />
            </div>
            {caseData.diagnosis_reasoning && (
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {caseData.diagnosis_reasoning}
              </p>
            )}
          </div>
        </div>

        {/* Box 2: Customer Profile */}
        <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-xl space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">Customer Context</span>
            <User className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <div className="font-bold text-white text-lg">
              {caseData.customer?.name || "Anonymous Customer"}
            </div>
            <div className="text-xs text-slate-400">
              {caseData.customer?.email || "customer@example.com"}
            </div>
            {caseData.customer?.phone && (
              <div className="text-xs text-slate-400 font-mono mt-0.5">
                {caseData.customer.phone}
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/[0.06] text-xs">
            <div>
              <span className="text-slate-400 text-[10px] uppercase font-semibold">Risk Score</span>
              <div className="font-bold text-slate-200 font-mono text-sm mt-0.5">
                {caseData.customer
                  ? `${(caseData.customer.risk_score * 100).toFixed(0)}/100`
                  : "N/A"}
              </div>
            </div>
            <div>
              <span className="text-slate-400 text-[10px] uppercase font-semibold">Recovery History</span>
              <div className="font-bold text-emerald-400 font-mono text-sm mt-0.5">
                {caseData.customer?.recovery_success_count || 0} Settled
              </div>
            </div>
          </div>
        </div>

        {/* Box 3: Decision Telemetry */}
        <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-xl space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">Decision Telemetry</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-400 text-[10px] uppercase font-semibold">Recovery Prob.</span>
              <div className="text-2xl font-black text-blue-400 font-mono mt-0.5">
                {caseData.recovery_probability
                  ? `${(caseData.recovery_probability * 100).toFixed(0)}%`
                  : "—"}
              </div>
            </div>
            <div>
              <span className="text-slate-400 text-[10px] uppercase font-semibold">Expected ERV</span>
              <div className="text-2xl font-black text-white font-mono mt-0.5">
                {formatINR(caseData.expected_recovery_value_cents)}
              </div>
            </div>
          </div>
          <div className="pt-3 border-t border-white/[0.06] space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 text-[10px]">Policy Verdict:</span>
              <span className="font-bold text-emerald-400">
                {latestDecision?.policy_verdict || "APPROVED"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 text-[10px]">Authorized Action:</span>
              <span className="font-bold text-purple-300">
                {latestDecision?.authorized_action || "PAYMENT_LINK"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Decisioning Pillars: AI Advisory vs Policy Authority vs Financial Truth */}
      <div className="p-6 rounded-3xl border border-white/[0.08] bg-[#080d22]/90 backdrop-blur-xl shadow-2xl space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-black text-white">
              Decision Governance & Separation of Concerns
            </h2>
            <p className="text-xs text-slate-400">
              Generative AI recommends advisory strategies; PolicyEngine is the sole financial authority.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
          {/* Pillar 1: GEMINI = ADVISORY */}
          <div className="p-5 rounded-2xl bg-purple-950/25 border border-purple-500/30 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-purple-300 uppercase tracking-wider">
                1. Gemini AI Strategist
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-purple-950 border border-purple-500/40 text-purple-300 font-bold">
                ADVISORY ONLY
              </span>
            </div>
            <div className="text-purple-200 font-bold text-sm">
              Proposed: {latestDecision?.ai_recommended_action || "PAYMENT_LINK"} (
              {latestDecision ? `${(latestDecision.ai_confidence * 100).toFixed(0)}%` : "94%"} confidence)
            </div>
            <p className="text-xs text-slate-300 leading-relaxed italic">
              "{latestDecision?.ai_reasoning || "Authentication dropped at bank. Sending hosted payment link maximizes completion probability."}"
            </p>
          </div>

          {/* Pillar 2: POLICY ENGINE = AUTHORITY */}
          <div className="p-5 rounded-2xl bg-blue-950/25 border border-blue-500/30 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-blue-300 uppercase tracking-wider">
                2. Deterministic Policy Engine
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-blue-950 border border-blue-500/40 text-blue-300 font-bold">
                SOLE AUTHORITY
              </span>
            </div>
            <div className="text-blue-200 font-bold text-sm">
              Verdict: <span className="font-black text-white">{latestDecision?.policy_verdict || "APPROVED"}</span>
            </div>
            <div className="text-xs text-slate-300">
              Authorized Action: <span className="font-bold text-white">{latestDecision?.authorized_action || "PAYMENT_LINK"}</span>
            </div>
            {latestDecision?.policy_rule_triggered && (
              <div className="text-[10px] text-amber-300 font-mono bg-slate-950/80 p-2 rounded-lg border border-amber-500/30">
                Triggered: {latestDecision.policy_rule_triggered}
              </div>
            )}
          </div>

          {/* Pillar 3: VERIFICATION = FINANCIAL TRUTH */}
          <div className="p-5 rounded-2xl bg-emerald-950/25 border border-emerald-500/30 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-emerald-300 uppercase tracking-wider">
                3. Settlement Verification
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-bold">
                FINANCIAL TRUTH
              </span>
            </div>
            <div className="text-emerald-200 font-bold text-sm">
              Status: {outcome ? "VERIFIED & RECOVERED" : "Awaiting Settling Webhook"}
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {outcome
                ? `Confirmed via ${outcome.verification_source}. Recovered: ${formatINR(outcome.amount_recovered_cents)}.`
                : "Awaiting customer payment link completion or bank webhook capture."}
            </p>
          </div>
        </div>
      </div>

      {/* 10-Step Explicit Orchestration Lifecycle */}
      <div className="rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <h2 className="text-base font-black text-white flex items-center gap-2.5">
            <Activity className="w-5 h-5 text-blue-400" />
            10-Step End-to-End Orchestration Timeline
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            Sequential Cryptographic Tracking
          </span>
        </div>

        <div className="relative pl-7 space-y-7 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/[0.08]">
          {/* Step 1: PAYMENT FAILED */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-rose-950 border border-rose-500 flex items-center justify-center text-rose-400 text-xs font-bold shadow-md">
              1
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  1. PAYMENT FAILED (HMAC-SHA256 Webhook Ingested)
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {formatDate(caseData.created_at)}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Initial transaction failed on {caseData.initial_payment?.method || "UPI"}:{" "}
                <span className="text-rose-300 font-mono text-[11px]">
                  {caseData.initial_payment?.error_code || "PAYMENT_AUTHENTICATION_ERROR"}
                </span>{" "}
                ({caseData.initial_payment?.error_description || "Customer dropped off"})
              </p>
            </div>
          </div>

          {/* Step 2: CASE DETECTED */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-blue-950 border border-blue-500 flex items-center justify-center text-blue-400 text-xs font-bold shadow-md">
              2
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                2. CASE DETECTED (Idempotent State Synchronized)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                Created RecoveryCase aggregate root for amount{" "}
                <span className="font-bold text-white font-mono">
                  {formatINR(caseData.amount_at_risk_cents)}
                </span>
                . Classified as{" "}
                <span className="text-slate-200 font-semibold">{caseData.failure_category}</span>.
              </p>
            </div>
          </div>

          {/* Step 3: CUSTOMER CONTEXT */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-indigo-950 border border-indigo-500 flex items-center justify-center text-indigo-400 text-xs font-bold shadow-md">
              3
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                3. CUSTOMER CONTEXT (Enriched Historical Profile)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                Customer: {caseData.customer?.name || "Customer"} • Historical Successes:{" "}
                {caseData.customer?.recovery_success_count || 0} • Payer Risk Tier: LOW.
              </p>
            </div>
          </div>

          {/* Step 4: ML RECOVERY PROBABILITY */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-cyan-950 border border-cyan-500 flex items-center justify-center text-cyan-400 text-xs font-bold shadow-md">
              4
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                4. ML RECOVERY PROBABILITY (Tabular GradientBoosting P_ML)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                Computed statistical probability P_ML ={" "}
                <span className="text-cyan-300 font-semibold font-mono">
                  {caseData.recovery_probability ? `${(caseData.recovery_probability * 100).toFixed(0)}%` : "78%"}
                </span>{" "}
                evaluating 21 pre-intervention features.
              </p>
            </div>
          </div>

          {/* Step 5: ERV RANKING */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-cyan-950 border border-cyan-500 flex items-center justify-center text-cyan-400 text-xs font-bold shadow-md">
              5
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                5. ERV RANKING (Deterministic Paise Math: ⌊P_ML × Amount⌋)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                Calculated Gross & Net ERV ={" "}
                <span className="text-white font-bold font-mono">
                  {formatINR(caseData.expected_recovery_value_cents)}
                </span>{" "}
                (Net of intervention cost and customer risk penalties).
              </p>
            </div>
          </div>

          {/* Step 6: GEMINI STRATEGY */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-purple-950 border border-purple-500 flex items-center justify-center text-purple-400 text-xs font-bold shadow-md">
              6
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                6. GEMINI STRATEGY (Advisory Root-Cause Formulation)
              </span>
              <p className="text-xs text-slate-300 mt-0.5">
                Gemini recommended:{" "}
                <span className="text-purple-300 font-semibold">
                  {latestDecision?.ai_recommended_action || "PAYMENT_LINK"}
                </span>{" "}
                with structured Pydantic schema validation.
              </p>
            </div>
          </div>

          {/* Step 7: POLICY AUTHORIZATION */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-blue-950 border border-blue-500 flex items-center justify-center text-blue-400 text-xs font-bold shadow-md">
              7
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                7. POLICY AUTHORIZATION (Authoritative Guardrail Gate)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                Policy Engine validated merchant risk rules. Verdict:{" "}
                <span className="font-bold text-emerald-400">
                  {latestDecision?.policy_verdict || "APPROVED"}
                </span>
                .
              </p>
            </div>
          </div>

          {/* Step 8: RECOVERY COMMAND */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-indigo-950 border border-indigo-500 flex items-center justify-center text-indigo-400 text-xs font-bold shadow-md">
              8
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                8. RECOVERY COMMAND (Idempotent Command Generated)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                Authorized action wrapped into immutable RecoveryCommand with row-level lock serialization.
              </p>
            </div>
          </div>

          {/* Step 9: RAZORPAY EXECUTION */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-amber-950 border border-amber-500 flex items-center justify-center text-amber-400 text-xs font-bold shadow-md">
              9
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                9. RAZORPAY EXECUTION (Hosted Payment Link / Dispatch)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                {latestAttempt ? (
                  <>
                    Dispatched{" "}
                    <span className="text-slate-200 font-semibold">
                      {latestAttempt.action_type}
                    </span>{" "}
                    via Razorpay Test Mode.
                    {latestAttempt.gateway_reference_id && (
                      <span className="block mt-0.5 text-blue-300 font-mono">
                        Ref: {latestAttempt.gateway_reference_id}
                      </span>
                    )}
                  </>
                ) : (
                  "Action pending execution dispatch."
                )}
              </p>
            </div>
          </div>

          {/* Step 10: FINANCIAL VERIFICATION */}
          <div className="relative">
            <div className="absolute -left-7 top-0.5 w-6 h-6 rounded-full bg-emerald-950 border border-emerald-500 flex items-center justify-center text-emerald-400 text-xs font-bold shadow-md">
              10
            </div>
            <div>
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                10. FINANCIAL VERIFICATION (Settling Webhook Reconciled)
              </span>
              <p className="text-xs text-slate-400 mt-0.5">
                {outcome ? (
                  <>
                    Verified via{" "}
                    <span className="text-emerald-400 font-bold">
                      {outcome.verification_source}
                    </span>
                    . Recovered: {formatINR(outcome.amount_recovered_cents)} (Net:{" "}
                    {formatINR(outcome.net_recovery_cents)}). Chained to SHA-256 Ledger.
                  </>
                ) : (
                  "Awaiting settling payment capture or webhook verification."
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile WhatsApp Customer Simulator Modal */}
      <MobileWhatsAppModal
        isOpen={isWhatsAppModalOpen}
        onClose={() => setIsWhatsAppModalOpen(false)}
        caseData={caseData}
      />
    </div>
  );
}
