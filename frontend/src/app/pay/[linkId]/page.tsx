"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ShieldCheck,
  CreditCard,
  Smartphone,
  Building2,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Lock,
  Zap,
  ArrowLeft,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { RecoveryCase } from "@/lib/api/types";
import { formatINR, formatDate } from "@/lib/utils";

export default function CustomerPaymentSimulatorPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  // The linkId can be a case_id directly, or passed via query
  const caseId = (params?.linkId as string) || searchParams.get("caseId") || "";

  const [caseData, setCaseData] = useState<RecoveryCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected Payment Method in Checkout
  const [paymentMethod, setPaymentMethod] = useState<"upi" | "card" | "netbanking">("upi");
  const [upiVpa, setUpiVpa] = useState("customer@okaxis");

  // Step-by-Step Payment Simulation State
  const [isProcessing, setIsProcessing] = useState(false);
  const [simulationStep, setSimulationStep] = useState<
    "IDLE" | "SUBMITTING" | "WEBHOOK_RECEIVED" | "VERIFYING" | "RECOVERED"
  >("IDLE");
  const [simulationResult, setSimulationResult] = useState<any | null>(null);

  async function loadCase() {
    if (!caseId) {
      setError("No case identifier provided for payment recovery.");
      setLoading(false);
      return;
    }
    try {
      const data = await apiClient.getCase("demo-store", caseId);
      setCaseData(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load recovery checkout details.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCase();
  }, [caseId]);

  async function handleSimulatePayment() {
    if (!caseData) return;
    setIsProcessing(true);
    setError(null);
    setSimulationStep("SUBMITTING");

    try {
      // Step 1: Submitting Payment
      await new Promise((r) => setTimeout(r, 600));
      setSimulationStep("WEBHOOK_RECEIVED");

      // Step 2: Ingesting captured webhook & executing verification
      await new Promise((r) => setTimeout(r, 600));
      setSimulationStep("VERIFYING");

      const res = await apiClient.simulatePayment("demo-store", caseData.id);
      
      await new Promise((r) => setTimeout(r, 500));
      setSimulationResult(res);
      setSimulationStep("RECOVERED");
      await loadCase();
    } catch (err: any) {
      setError(err?.message || "Payment simulation failed.");
      setSimulationStep("IDLE");
    } finally {
      setIsProcessing(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mb-3" />
        <p className="text-sm font-medium">Loading secure payment recovery checkout...</p>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 rounded-2xl border border-rose-500/30 bg-[#0d1322] shadow-2xl text-center">
        <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-white mb-2">Checkout Unavailable</h2>
        <p className="text-xs text-slate-400 mb-6">{error || "Case record not found."}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Command Center
        </Link>
      </div>
    );
  }

  const isAlreadyRecovered =
    caseData.status === "RECOVERED" || simulationStep === "RECOVERED";

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 pb-24">
      {/* Top Banner: Simulator Disclaimer */}
      <div className="mb-8 p-4 rounded-2xl bg-blue-950/40 border border-blue-500/30 backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-lg">
        <div className="flex items-center gap-2.5 text-blue-300 font-medium">
          <Sparkles className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            <strong>Razorpay Hosted Recovery Simulator:</strong> Demonstrates real-time customer re-checkout under Razorpay Test Mode.
          </span>
        </div>
        <Link
          href={`/cases/${caseData.id}`}
          className="text-xs text-blue-400 hover:text-blue-300 underline shrink-0 font-bold"
        >
          Back to Case Dossier
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left Column: Order & Recovery Context */}
        <div className="md:col-span-5 space-y-6">
          <div className="p-6 sm:p-7 rounded-3xl border border-white/[0.08] bg-[#070b1c]/85 backdrop-blur-xl shadow-2xl space-y-5">
            {/* Merchant Identity */}
            <div className="flex items-center gap-3.5 pb-5 border-b border-white/[0.06]">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-500 flex items-center justify-center font-black text-white shadow-lg shadow-blue-500/20 border border-white/20">
                RF
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Demo Merchant Enterprise</h2>
                <span className="text-[11px] text-slate-400 flex items-center gap-1 font-medium mt-0.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Verified Merchant Account
                </span>
              </div>
            </div>

            {/* Order Summary */}
            <div className="py-2 space-y-3.5 border-b border-white/[0.06] text-xs">
              <div className="flex justify-between items-center text-slate-400">
                <span className="uppercase text-[10px] font-bold tracking-wider">Order Reference</span>
                <span className="font-mono font-bold text-white text-xs">
                  {caseData.order?.external_order_id || "order_demo_101"}
                </span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span className="uppercase text-[10px] font-bold tracking-wider">Customer</span>
                <span className="font-medium text-slate-200">
                  {caseData.customer?.name || "Verified Customer"}
                </span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span className="uppercase text-[10px] font-bold tracking-wider">Previous Cause</span>
                <span className="text-amber-300 font-semibold">
                  {caseData.failure_category.replace(/_/g, " ")}
                </span>
              </div>
            </div>

            {/* Total Amount */}
            <div className="pt-2 flex justify-between items-baseline">
              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Total Due</span>
              <span className="text-3xl font-black text-white tracking-tight font-mono">
                {formatINR(caseData.amount_at_risk_cents)}
              </span>
            </div>

            {/* Recovery Value Badge */}
            <div className="p-3.5 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="leading-relaxed font-medium">
                Completing this payment re-secures your order reservation instantly.
              </span>
            </div>
          </div>

          {/* Security & Non-Repudiation Info */}
          <div className="p-5 rounded-2xl border border-white/[0.06] bg-slate-950/50 text-xs text-slate-400 space-y-2">
            <div className="flex items-center gap-2 text-slate-200 font-bold">
              <Lock className="w-4 h-4 text-blue-400" />
              <span>Bank-Grade 256-Bit SSL Encryption</span>
            </div>
            <p className="leading-relaxed">
              Secured by Razorpay Test Gateway with deterministic SHA-256 cryptographic audit chaining.
            </p>
          </div>
        </div>

        {/* Right Column: Interactive Payment Checkout Simulator */}
        <div className="md:col-span-7">
          <div className="p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-[#070b1c]/85 backdrop-blur-xl shadow-2xl space-y-6">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <div>
                <h3 className="text-lg font-black text-white">Select Payment Instrument</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Choose a checkout method to simulate customer recovery.
                </p>
              </div>
              <span className="text-[10px] px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 font-bold font-mono">
                TEST MODE
              </span>
            </div>

            {/* Payment Method Selector Tabs */}
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setPaymentMethod("upi")}
                className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col gap-1.5 ${
                  paymentMethod === "upi"
                    ? "bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/15"
                    : "bg-slate-950/60 border-white/[0.06] text-slate-400 hover:border-slate-700"
                }`}
              >
                <Smartphone className="w-5 h-5 text-blue-400" />
                <span className="text-xs font-bold">UPI / QR</span>
                <span className="text-[10px] text-slate-400">GPay, PhonePe</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("card")}
                className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col gap-1.5 ${
                  paymentMethod === "card"
                    ? "bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/15"
                    : "bg-slate-950/60 border-white/[0.06] text-slate-400 hover:border-slate-700"
                }`}
              >
                <CreditCard className="w-5 h-5 text-purple-400" />
                <span className="text-xs font-bold">Cards</span>
                <span className="text-[10px] text-slate-400">Debit / Credit</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("netbanking")}
                className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col gap-1.5 ${
                  paymentMethod === "netbanking"
                    ? "bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/15"
                    : "bg-slate-950/60 border-white/[0.06] text-slate-400 hover:border-slate-700"
                }`}
              >
                <Building2 className="w-5 h-5 text-emerald-400" />
                <span className="text-xs font-bold">NetBanking</span>
                <span className="text-[10px] text-slate-400">HDFC, ICICI, SBI</span>
              </button>
            </div>

            {/* Instrument Detail Inputs */}
            <div className="p-4 rounded-2xl border border-white/[0.06] bg-slate-950/80">
              {paymentMethod === "upi" && (
                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-300 block">
                    UPI Virtual Payment Address (VPA)
                  </label>
                  <div className="flex gap-2.5">
                    <input
                      type="text"
                      value={upiVpa}
                      onChange={(e) => setUpiVpa(e.target.value)}
                      className="flex-1 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/[0.08] text-xs text-white font-mono focus:outline-none focus:border-blue-500"
                      placeholder="customer@okaxis"
                    />
                    <div className="px-3.5 py-2.5 rounded-xl bg-blue-950/60 border border-blue-500/30 text-[11px] font-bold text-blue-300 flex items-center gap-1.5 shrink-0">
                      <Zap className="w-3.5 h-3.5 text-blue-400" /> Instant Intent
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-400 pt-1">
                    <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-white/[0.06] font-mono">Google Pay</span>
                    <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-white/[0.06] font-mono">PhonePe</span>
                    <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-white/[0.06] font-mono">Paytm UPI</span>
                    <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-white/[0.06] font-mono">BHIM</span>
                  </div>
                </div>
              )}

              {paymentMethod === "card" && (
                <div className="space-y-3">
                  <div className="text-xs font-bold text-slate-300">Simulated Card Details</div>
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-white/[0.08] font-mono text-xs text-slate-300 flex justify-between">
                    <span>•••• •••• •••• 4242</span>
                    <span>12/28 • CVV ***</span>
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Razorpay Test Card (Auto-populated for instant recovery demonstration).
                  </p>
                </div>
              )}

              {paymentMethod === "netbanking" && (
                <div className="space-y-3">
                  <div className="text-xs font-bold text-slate-300">Select Bank</div>
                  <div className="grid grid-cols-2 gap-2.5 text-xs">
                    <div className="p-3 rounded-xl bg-slate-900 border border-blue-500/40 text-white font-bold flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full bg-blue-400" /> HDFC Bank
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900 border border-white/[0.08] text-slate-400 flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full bg-slate-600" /> ICICI Bank
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Simulation Status Stepper */}
            {simulationStep !== "IDLE" && (
              <div className="p-5 rounded-2xl bg-slate-950/90 border border-white/[0.08] space-y-3 shadow-inner">
                <div className="text-xs font-bold text-white flex items-center justify-between">
                  <span>Recovery Execution Lifecycle</span>
                  <span className="font-mono text-[10px] text-blue-400 font-bold animate-pulse">
                    {simulationStep}
                  </span>
                </div>

                <div className="space-y-2 text-[11px]">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>PAYMENT SUBMITTED (Customer Authorize)</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      simulationStep === "SUBMITTING"
                        ? "text-slate-600"
                        : "text-emerald-400"
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>WEBHOOK INGESTED (`payment.captured` HMAC-SHA256)</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      simulationStep === "SUBMITTING" || simulationStep === "WEBHOOK_RECEIVED"
                        ? "text-slate-600"
                        : "text-emerald-400"
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>PAYMENT VERIFIED (Reconciled against Order)</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      simulationStep === "RECOVERED"
                        ? "text-emerald-300 font-bold"
                        : "text-slate-600"
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>
                      RECOVERY CONFIRMED → {formatINR(caseData.amount_at_risk_cents)} RECOVERED
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Complete Payment Button */}
            {!isAlreadyRecovered ? (
              <button
                type="button"
                onClick={handleSimulatePayment}
                disabled={isProcessing}
                className="w-full py-4 px-5 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:via-indigo-500 hover:to-purple-500 text-white font-black text-sm shadow-xl shadow-blue-500/30 transition flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer border border-white/20"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Processing Payment Simulation...
                  </>
                ) : (
                  <>
                    <span>Pay {formatINR(caseData.amount_at_risk_cents)} & Complete Recovery</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            ) : (
              <div className="p-6 rounded-2xl bg-emerald-950/60 border border-emerald-500/40 text-center space-y-4 shadow-xl">
                <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
                <div>
                  <h4 className="text-base font-black text-white">Payment Recovered Successfully!</h4>
                  <p className="text-xs text-emerald-300 mt-1 font-mono">
                    {formatINR(caseData.amount_at_risk_cents)} verified and reconciled into immutable audit ledger.
                  </p>
                </div>
                <div className="flex flex-wrap justify-center gap-3 pt-2">
                  <Link
                    href={`/cases/${caseData.id}`}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow-lg shadow-emerald-500/25"
                  >
                    View Case Dossier
                  </Link>
                  <Link
                    href="/"
                    className="px-4 py-2 rounded-xl bg-slate-900 border border-white/[0.08] hover:bg-slate-800 text-slate-300 text-xs font-bold transition"
                  >
                    Command Center
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
