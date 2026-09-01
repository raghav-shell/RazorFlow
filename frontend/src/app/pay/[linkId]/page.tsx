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
    <div className="max-w-4xl mx-auto py-6 px-4 pb-20">
      {/* Top Banner: Simulator Disclaimer */}
      <div className="mb-6 p-3 rounded-xl bg-blue-950/40 border border-blue-500/30 flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-blue-300 font-medium">
          <Sparkles className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            <strong>Demo Customer Checkout Simulator:</strong> Demonstrates the hosted payment recovery flow for Razorpay Test Mode.
          </span>
        </div>
        <Link
          href={`/cases/${caseData.id}`}
          className="text-xs text-blue-400 hover:text-blue-300 underline shrink-0 font-semibold"
        >
          Back to Case Dossier
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left Column: Order & Recovery Context */}
        <div className="md:col-span-5 space-y-5">
          <div className="p-6 rounded-2xl border border-slate-800 bg-[#0d1322] shadow-xl">
            {/* Merchant Identity */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-md">
                RF
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Demo Merchant Enterprise</h2>
                <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" /> Verified Razorpay Merchant
                </span>
              </div>
            </div>

            {/* Order Summary */}
            <div className="py-4 space-y-3 border-b border-slate-800 text-xs">
              <div className="flex justify-between items-center text-slate-400">
                <span>Order Reference</span>
                <span className="font-mono font-semibold text-slate-200">
                  {caseData.order?.external_order_id || "order_demo_101"}
                </span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Customer</span>
                <span className="font-medium text-slate-200">
                  {caseData.customer?.name || "Verified Customer"}
                </span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Previous Issue</span>
                <span className="text-amber-300 font-medium">
                  {caseData.failure_category.replace(/_/g, " ")}
                </span>
              </div>
            </div>

            {/* Total Amount */}
            <div className="pt-4 flex justify-between items-baseline">
              <span className="text-xs text-slate-400 font-semibold uppercase">Total Amount</span>
              <span className="text-2xl font-bold text-white tracking-tight">
                {formatINR(caseData.amount_at_risk_cents)}
              </span>
            </div>

            {/* Recovery Value Badge */}
            <div className="mt-4 p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-[11px] text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                Completing this payment re-secures your reserved order instantly.
              </span>
            </div>
          </div>

          {/* Security & Non-Repudiation Info */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/50 text-[11px] text-slate-400 space-y-1.5">
            <div className="flex items-center gap-2 text-slate-300 font-semibold">
              <Lock className="w-3.5 h-3.5 text-blue-400" />
              <span>Bank-Grade 256-Bit Encryption</span>
            </div>
            <p>
              Simulated under Razorpay Test Mode with deterministic cryptographic ledger audit.
            </p>
          </div>
        </div>

        {/* Right Column: Interactive Payment Checkout Simulator */}
        <div className="md:col-span-7">
          <div className="p-6 rounded-2xl border border-slate-800 bg-[#0d1322] shadow-2xl">
            <h3 className="text-base font-bold text-white mb-1 flex items-center justify-between">
              <span>Select Payment Method</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950 border border-blue-500/30 text-blue-300 font-semibold">
                Test Mode
              </span>
            </h3>
            <p className="text-xs text-slate-400 mb-5">
              Choose an instrument below to simulate customer recovery payment.
            </p>

            {/* Payment Method Selector Tabs */}
            <div className="grid grid-cols-3 gap-2.5 mb-5">
              <button
                type="button"
                onClick={() => setPaymentMethod("upi")}
                className={`p-3 rounded-xl border text-left transition cursor-pointer flex flex-col gap-1.5 ${
                  paymentMethod === "upi"
                    ? "bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <Smartphone className="w-5 h-5 text-blue-400" />
                <span className="text-xs font-bold">UPI / QR</span>
                <span className="text-[10px] text-slate-400">GPay, PhonePe</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("card")}
                className={`p-3 rounded-xl border text-left transition cursor-pointer flex flex-col gap-1.5 ${
                  paymentMethod === "card"
                    ? "bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <CreditCard className="w-5 h-5 text-purple-400" />
                <span className="text-xs font-bold">Cards</span>
                <span className="text-[10px] text-slate-400">Debit / Credit</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("netbanking")}
                className={`p-3 rounded-xl border text-left transition cursor-pointer flex flex-col gap-1.5 ${
                  paymentMethod === "netbanking"
                    ? "bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <Building2 className="w-5 h-5 text-emerald-400" />
                <span className="text-xs font-bold">NetBanking</span>
                <span className="text-[10px] text-slate-400">HDFC, ICICI, SBI</span>
              </button>
            </div>

            {/* Instrument Detail Inputs */}
            <div className="mb-6 p-4 rounded-xl border border-slate-800 bg-slate-950/60">
              {paymentMethod === "upi" && (
                <div className="space-y-3">
                  <label className="text-xs font-semibold text-slate-300 block">
                    UPI Virtual Payment Address (VPA)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={upiVpa}
                      onChange={(e) => setUpiVpa(e.target.value)}
                      className="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-blue-500"
                      placeholder="username@bank"
                    />
                    <div className="px-3 py-2 rounded-lg bg-blue-950/60 border border-blue-500/30 text-[11px] font-semibold text-blue-300 flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-blue-400" /> Fast Intent
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800">Google Pay</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-800">PhonePe</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-800">Paytm</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-800">BHIM</span>
                  </div>
                </div>
              )}

              {paymentMethod === "card" && (
                <div className="space-y-3">
                  <div className="text-xs font-semibold text-slate-300">Simulated Card Details</div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs text-slate-300 flex justify-between">
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
                  <div className="text-xs font-semibold text-slate-300">Select Bank</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-lg bg-slate-900 border border-blue-500/40 text-white font-medium flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-400" /> HDFC Bank
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-slate-600" /> ICICI Bank
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Simulation Status Stepper */}
            {simulationStep !== "IDLE" && (
              <div className="mb-6 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-xs font-bold text-white mb-2 flex items-center justify-between">
                  <span>Recovery Execution Lifecycle</span>
                  <span className="font-mono text-[10px] text-blue-400 animate-pulse">
                    {simulationStep}
                  </span>
                </div>

                <div className="space-y-1.5 text-[11px]">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                    <span>PAYMENT SUBMITTED (Simulated Customer Authorize)</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      simulationStep === "SUBMITTING"
                        ? "text-slate-500"
                        : "text-emerald-400"
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                    <span>WEBHOOK RECEIVED (`payment.captured` HMAC-SHA256 Auth)</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      simulationStep === "SUBMITTING" || simulationStep === "WEBHOOK_RECEIVED"
                        ? "text-slate-500"
                        : "text-emerald-400"
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                    <span>PAYMENT VERIFIED (Funds Reconciled against Order)</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      simulationStep === "RECOVERED"
                        ? "text-emerald-300 font-bold"
                        : "text-slate-500"
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
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
                className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-xl shadow-blue-500/25 transition flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
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
              <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-center space-y-3">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
                <div>
                  <h4 className="text-sm font-bold text-white">Payment Recovered Successfully!</h4>
                  <p className="text-xs text-emerald-300 mt-0.5">
                    {formatINR(caseData.amount_at_risk_cents)} verified and reconciled into immutable audit ledger.
                  </p>
                </div>
                <div className="flex justify-center gap-3 pt-2">
                  <Link
                    href={`/cases/${caseData.id}`}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow-md shadow-emerald-500/20"
                  >
                    View Updated Case Dossier
                  </Link>
                  <Link
                    href="/"
                    className="px-4 py-2 rounded-lg bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition"
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
