"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Bot,
  CheckCircle2,
  CreditCard,
  DollarSign,
  ExternalLink,
  Lock,
  Play,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  User,
  Zap,
  Smartphone,
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
      <div className="py-24 text-center text-[#86868b]">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#0071e3] mb-3" />
        <p className="text-sm">Loading case dossier...</p>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="py-24 text-center">
        <AlertTriangle className="w-10 h-10 mx-auto text-[#ffd60a] mb-3" />
        <h2 className="text-lg font-semibold text-white mb-2">Case Not Found</h2>
        <p className="text-xs text-[#86868b] mb-4">{errorMessage || "Case ID not found."}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-white text-black text-xs font-semibold hover:bg-[#e5e5ea]"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Command Center</span>
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
    <div className="space-y-8 pb-28 max-w-7xl mx-auto px-2 sm:px-4">
      {/* Top Breadcrumb & Action Toolbar */}
      <section className="pt-4 pb-2 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <Link
            href="/"
            className="p-2.5 rounded-full bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.1] text-[#86868b] hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-[-0.03em] text-white font-mono">
                {caseData.order?.external_order_id || "Order"}
              </h1>
              <StatusBadge status={caseData.status} />
            </div>
            <p className="text-xs text-[#86868b] font-mono mt-0.5">
              UUID: {caseData.id || caseId}
            </p>
          </div>
        </div>

        {/* Action Buttons Toolbar */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* WhatsApp Simulator Button */}
          <button
            onClick={() => setIsWhatsAppModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] text-white text-xs font-medium transition cursor-pointer"
          >
            <Smartphone className="w-4 h-4 text-[#30d158]" />
            <span>Customer WhatsApp</span>
          </button>

          {/* Hosted Checkout Simulator */}
          <Link
            href={`/pay/${caseData.payment_link_id || latestAttempt?.gateway_reference_id || caseData.id}`}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#0071e3]/10 border border-[#0071e3]/30 text-[#64d2ff] hover:bg-[#0071e3]/20 text-xs font-medium transition cursor-pointer"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Hosted Checkout</span>
          </Link>

          {/* Simulate Payment Capture (if not already recovered) */}
          {!isRecovered && (
            <button
              onClick={handleSimulatePayment}
              disabled={simulating}
              className="flex items-center gap-2 px-5 py-2 rounded-full bg-white text-black hover:bg-[#e5e5ea] text-xs font-semibold transition cursor-pointer disabled:opacity-50"
            >
              {simulating ? (
                <RefreshCw className="w-4 h-4 animate-spin text-[#0071e3]" />
              ) : (
                <CreditCard className="w-4 h-4 text-[#30d158]" />
              )}
              <span>Simulate Payment</span>
            </button>
          )}

          {/* Execute Authorized Action */}
          {(caseData.status === "APPROVED" || caseData.status === "DETECTED") && (
            <button
              onClick={() => handleExecuteAction()}
              disabled={executing}
              className="flex items-center gap-2 px-5 py-2 rounded-full bg-white text-black hover:bg-[#e5e5ea] text-xs font-semibold transition cursor-pointer disabled:opacity-50"
            >
              {executing ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4 text-[#0071e3]" />
              )}
              <span>Dispatch Action</span>
            </button>
          )}
        </div>
      </section>

      {/* Action Notification Alert */}
      {actionSuccessMessage && (
        <div className="apple-card p-4 text-xs text-[#30d158] flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{actionSuccessMessage}</span>
        </div>
      )}
      {errorMessage && (
        <div className="apple-card p-4 text-xs text-[#ff453a] flex items-center gap-2.5">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Verified Outcome Banner (if recovered) */}
      {outcome && outcome.is_successful && (
        <div className="apple-card p-6 sm:p-7">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-[#30d158]/10 border border-[#30d158]/30 flex items-center justify-center text-[#30d158]">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-mono text-[#30d158] font-semibold tracking-wider">
                  Verified Settlement
                </span>
                <h2 className="text-xl font-semibold text-white">
                  Revenue Successfully Recovered
                </h2>
                <p className="text-xs text-[#86868b] mt-0.5">
                  Verified via {outcome.verification_source} • Settling webhook reconciled into cryptographic ledger.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6 border-t sm:border-t-0 sm:border-l border-white/[0.06] pt-4 sm:pt-0 sm:pl-6">
              <div>
                <span className="text-[10px] text-[#86868b] block uppercase">
                  Recovered
                </span>
                <span className="text-xl font-semibold text-white font-mono">
                  {formatINR(outcome.amount_recovered_cents)}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-[#86868b] block uppercase">
                  Net Recovered
                </span>
                <span className="text-xl font-semibold text-[#30d158] font-mono">
                  {formatINR(outcome.net_recovery_cents)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Case Overview Apple Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Box 1: Financial & Failure Summary */}
        <div className="apple-card p-6 space-y-4">
          <div className="flex items-center justify-between text-xs text-[#86868b]">
            <span className="font-semibold text-white">Financial Impact</span>
            <DollarSign className="w-4 h-4 text-[#64d2ff]" />
          </div>
          <div>
            <span className="text-[10px] text-[#86868b] uppercase">Amount at Risk</span>
            <div className="text-3xl font-semibold text-white font-mono tracking-tight mt-0.5">
              {formatINR(caseData.amount_at_risk_cents)}
            </div>
          </div>
          <div className="pt-3 border-t border-white/[0.06] space-y-2">
            <span className="text-[10px] text-[#86868b] uppercase">Failure Cause</span>
            <div>
              <CategoryBadge
                category={caseData.failure_category}
                isTransient={caseData.is_transient}
              />
            </div>
            {caseData.diagnosis_reasoning && (
              <p className="text-xs text-[#86868b] mt-1 leading-relaxed">
                {caseData.diagnosis_reasoning}
              </p>
            )}
          </div>
        </div>

        {/* Box 2: Customer Profile */}
        <div className="apple-card p-6 space-y-4">
          <div className="flex items-center justify-between text-xs text-[#86868b]">
            <span className="font-semibold text-white">Customer Profile</span>
            <User className="w-4 h-4 text-[#bf5af2]" />
          </div>
          <div>
            <div className="font-semibold text-white text-base">
              {caseData.customer?.name || "Anonymous Customer"}
            </div>
            <div className="text-xs text-[#86868b] mt-0.5">
              {caseData.customer?.email || "customer@example.com"}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/[0.06] text-xs">
            <div>
              <span className="text-[#86868b] text-[10px] uppercase">Risk Tier</span>
              <div className="font-semibold text-white font-mono text-sm mt-0.5">
                {caseData.customer
                  ? `${(caseData.customer.risk_score * 100).toFixed(0)}/100 (Low)`
                  : "N/A"}
              </div>
            </div>
            <div>
              <span className="text-[#86868b] text-[10px] uppercase">Recovery History</span>
              <div className="font-semibold text-[#30d158] font-mono text-sm mt-0.5">
                {caseData.customer?.recovery_success_count || 0} Settled
              </div>
            </div>
          </div>
        </div>

        {/* Box 3: Decision Telemetry */}
        <div className="apple-card p-6 space-y-4">
          <div className="flex items-center justify-between text-xs text-[#86868b]">
            <span className="font-semibold text-white">Decision Telemetry</span>
            <Zap className="w-4 h-4 text-[#ffd60a]" />
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-[#86868b] text-[10px] uppercase">Recovery Prob.</span>
              <div className="text-2xl font-semibold text-[#64d2ff] font-mono mt-0.5">
                {caseData.recovery_probability
                  ? `${(caseData.recovery_probability * 100).toFixed(0)}%`
                  : "—"}
              </div>
            </div>
            <div>
              <span className="text-[#86868b] text-[10px] uppercase">Expected ERV</span>
              <div className="text-2xl font-semibold text-white font-mono mt-0.5">
                {formatINR(caseData.expected_recovery_value_cents)}
              </div>
            </div>
          </div>
          <div className="pt-3 border-t border-white/[0.06] space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#86868b] text-[10px]">Policy Verdict:</span>
              <span className="font-semibold text-[#30d158] font-mono">
                {latestDecision?.policy_verdict || "APPROVED"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#86868b] text-[10px]">Authorized Action:</span>
              <span className="font-semibold text-white font-mono">
                {latestDecision?.authorized_action || "PAYMENT_LINK"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Decisioning Pillars: AI Advisory vs Policy Authority vs Financial Truth */}
      <div className="apple-card p-6 sm:p-7 space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#bf5af2]/10 border border-[#bf5af2]/30 flex items-center justify-center text-[#bf5af2]">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">
              Separation of Concerns & Governance Pillars
            </h2>
            <p className="text-xs text-[#86868b]">
              Generative AI recommends advisory strategies; PolicyEngine is the sole financial authority.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* Pillar 1: GEMINI = ADVISORY */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#bf5af2] font-mono uppercase font-semibold">
                1. Gemini AI Strategist
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-[#bf5af2]/10 text-[#bf5af2] font-mono">
                Advisory
              </span>
            </div>
            <div className="text-white font-semibold text-sm">
              Proposed: {latestDecision?.ai_recommended_action || "PAYMENT_LINK"} (
              {latestDecision ? `${(latestDecision.ai_confidence * 100).toFixed(0)}%` : "94%"} conf)
            </div>
            <p className="text-xs text-[#86868b] leading-relaxed">
              "{latestDecision?.ai_reasoning || "Authentication dropped at bank. Sending hosted payment link maximizes completion probability."}"
            </p>
          </div>

          {/* Pillar 2: POLICY ENGINE = AUTHORITY */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#0071e3] font-mono uppercase font-semibold">
                2. Deterministic Policy Engine
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-[#0071e3]/10 text-[#64d2ff] font-mono">
                Authority
              </span>
            </div>
            <div className="text-white font-semibold text-sm">
              Verdict: <span className="text-[#30d158]">{latestDecision?.policy_verdict || "APPROVED"}</span>
            </div>
            <div className="text-xs text-[#86868b]">
              Authorized: <span className="font-semibold text-white">{latestDecision?.authorized_action || "PAYMENT_LINK"}</span>
            </div>
          </div>

          {/* Pillar 3: VERIFICATION = FINANCIAL TRUTH */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#30d158] font-mono uppercase font-semibold">
                3. Settlement Verification
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-[#30d158]/10 text-[#30d158] font-mono">
                Truth
              </span>
            </div>
            <div className="text-white font-semibold text-sm">
              Status: {outcome ? "VERIFIED & RECOVERED" : "Awaiting Settling Webhook"}
            </div>
            <p className="text-xs text-[#86868b] leading-relaxed">
              {outcome
                ? `Confirmed via ${outcome.verification_source}. Recovered: ${formatINR(outcome.amount_recovered_cents)}.`
                : "Awaiting customer checkout completion."}
            </p>
          </div>
        </div>
      </div>

      {/* 10-Step Explicit Orchestration Lifecycle */}
      <div className="apple-card p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#64d2ff]" />
            <span>10-Step Sequential Orchestration Timeline</span>
          </h2>
          <span className="text-[11px] text-[#86868b] font-mono">
            Cryptographic State History
          </span>
        </div>

        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-px before:bg-white/[0.08]">
          {/* Step 1 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#ff453a]/10 border border-[#ff453a]/30 flex items-center justify-center text-[#ff453a] text-[10px] font-mono font-semibold">
              1
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-white">
                  1. PAYMENT FAILED (HMAC-SHA256 Webhook Ingested)
                </span>
                <span className="text-[10px] text-[#86868b] font-mono">
                  {formatDate(caseData.created_at)}
                </span>
              </div>
              <p className="text-xs text-[#86868b] mt-0.5">
                Initial transaction failed on {caseData.initial_payment?.method || "UPI"}:{" "}
                <span className="text-white font-mono text-[11px]">
                  {caseData.initial_payment?.error_code || "PAYMENT_AUTHENTICATION_ERROR"}
                </span>
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#0071e3]/10 border border-[#0071e3]/30 flex items-center justify-center text-[#64d2ff] text-[10px] font-mono font-semibold">
              2
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                2. CASE DETECTED (Idempotent State Synchronized)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                Created RecoveryCase aggregate root for amount{" "}
                <span className="text-white font-mono">
                  {formatINR(caseData.amount_at_risk_cents)}
                </span>
                .
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#bf5af2]/10 border border-[#bf5af2]/30 flex items-center justify-center text-[#bf5af2] text-[10px] font-mono font-semibold">
              3
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                3. CUSTOMER CONTEXT (Enriched Historical Profile)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                Customer: {caseData.customer?.name || "Customer"} • Historical Successes:{" "}
                {caseData.customer?.recovery_success_count || 0}.
              </p>
            </div>
          </div>

          {/* Step 4 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#64d2ff]/10 border border-[#64d2ff]/30 flex items-center justify-center text-[#64d2ff] text-[10px] font-mono font-semibold">
              4
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                4. ML RECOVERY PROBABILITY (Tabular GradientBoosting P_ML)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                Statistical probability P_ML ={" "}
                <span className="text-[#64d2ff] font-mono">
                  {caseData.recovery_probability ? `${(caseData.recovery_probability * 100).toFixed(0)}%` : "78%"}
                </span>.
              </p>
            </div>
          </div>

          {/* Step 5 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-white text-[10px] font-mono font-semibold">
              5
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                5. ERV RANKING (Deterministic Paise Math: ⌊P_ML × Amount⌋)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                Expected ERV ={" "}
                <span className="text-white font-mono">
                  {formatINR(caseData.expected_recovery_value_cents)}
                </span>.
              </p>
            </div>
          </div>

          {/* Step 6 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#bf5af2]/10 border border-[#bf5af2]/30 flex items-center justify-center text-[#bf5af2] text-[10px] font-mono font-semibold">
              6
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                6. GEMINI STRATEGY (Advisory Root-Cause Formulation)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                Gemini recommended:{" "}
                <span className="text-white font-mono">
                  {latestDecision?.ai_recommended_action || "PAYMENT_LINK"}
                </span>.
              </p>
            </div>
          </div>

          {/* Step 7 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#0071e3]/10 border border-[#0071e3]/30 flex items-center justify-center text-[#64d2ff] text-[10px] font-mono font-semibold">
              7
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                7. POLICY AUTHORIZATION (Authoritative Guardrail Gate)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                Policy Verdict:{" "}
                <span className="text-[#30d158] font-mono">
                  {latestDecision?.policy_verdict || "APPROVED"}
                </span>.
              </p>
            </div>
          </div>

          {/* Step 8 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-white text-[10px] font-mono font-semibold">
              8
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                8. RECOVERY COMMAND (Idempotent Command Generated)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                Authorized action serialized with row-level locks.
              </p>
            </div>
          </div>

          {/* Step 9 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#ffd60a]/10 border border-[#ffd60a]/30 flex items-center justify-center text-[#ffd60a] text-[10px] font-mono font-semibold">
              9
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                9. RAZORPAY EXECUTION (Hosted Payment Link / Dispatch)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                {latestAttempt ? (
                  <>
                    Dispatched{" "}
                    <span className="text-white font-mono">
                      {latestAttempt.action_type}
                    </span>{" "}
                    via Razorpay Test Mode.
                  </>
                ) : (
                  "Action pending execution dispatch."
                )}
              </p>
            </div>
          </div>

          {/* Step 10 */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[#30d158]/10 border border-[#30d158]/30 flex items-center justify-center text-[#30d158] text-[10px] font-mono font-semibold">
              10
            </div>
            <div>
              <span className="text-xs font-semibold text-white">
                10. FINANCIAL VERIFICATION (Settling Webhook Reconciled)
              </span>
              <p className="text-xs text-[#86868b] mt-0.5">
                {outcome ? (
                  <>
                    Verified via{" "}
                    <span className="text-[#30d158] font-semibold">
                      {outcome.verification_source}
                    </span>
                    . Recovered: {formatINR(outcome.amount_recovered_cents)}. Chained to SHA-256 Ledger.
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
