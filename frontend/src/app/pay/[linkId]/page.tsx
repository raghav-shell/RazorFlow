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
  Radio,
  Wifi,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { RecoveryCase } from "@/lib/api/types";
import { formatINR } from "@/lib/utils";

export default function CustomerPaymentSimulatorPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const caseId = (params?.linkId as string) || searchParams.get("caseId") || "";

  const [caseData, setCaseData] = useState<RecoveryCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [paymentMethod, setPaymentMethod] = useState<"upi" | "card" | "netbanking">("upi");
  const [upiVpa, setUpiVpa] = useState("customer@okaxis");

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
      await new Promise((r) => setTimeout(r, 600));
      setSimulationStep("WEBHOOK_RECEIVED");

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
      <div className="min-h-[80vh] flex flex-col items-center justify-center text-[#86868b]">
        <RefreshCw className="w-8 h-8 animate-spin text-[#0071e3] mb-3" />
        <p className="text-sm font-medium">Securing hosted checkout session...</p>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="max-w-md mx-auto my-16 p-8 rounded-3xl apple-card text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-[#ff453a] mx-auto" />
        <h2 className="text-lg font-semibold text-white">Checkout Unavailable</h2>
        <p className="text-xs text-[#86868b]">{error || "Case record not found."}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white text-black font-semibold text-xs transition"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Cockpit
        </Link>
      </div>
    );
  }

  const isAlreadyRecovered =
    caseData.status === "RECOVERED" || simulationStep === "RECOVERED";

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 pb-28 space-y-8">
      {/* Top Banner */}
      <div className="p-3.5 rounded-full apple-card flex items-center justify-between px-5 text-xs">
        <div className="flex items-center gap-2 text-white">
          <Sparkles className="w-4 h-4 text-[#64d2ff]" />
          <span className="font-medium">
            Hosted Recovery Checkout <span className="text-[#86868b]">• Razorpay Test Mode</span>
          </span>
        </div>
        <Link
          href={`/cases/${caseData.id}`}
          className="text-xs text-[#0071e3] hover:text-[#64d2ff] transition-colors font-semibold"
        >
          Case Dossier ➔
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left Column: Titanium Card & Summary */}
        <div className="md:col-span-5 space-y-6">
          {/* Apple Titanium Card Mockup */}
          <div className="relative h-56 rounded-3xl p-6 bg-gradient-to-br from-[#1c1c1e] via-[#121214] to-[#08080a] border-[0.5px] border-white/20 shadow-[0_20px_50px_rgba(0,0,0,0.9)] flex flex-col justify-between overflow-hidden group">
            {/* Ambient Card Sheen */}
            <div className="absolute inset-0 bg-gradient-to-tr from-white/[0.04] to-transparent pointer-events-none" />
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl pointer-events-none" />

            <div className="flex justify-between items-start">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center font-bold text-xs text-white">
                  RF
                </div>
                <span className="text-xs font-semibold text-white tracking-tight">RazorFlow Pay</span>
              </div>
              <Wifi className="w-5 h-5 text-white/40 rotate-90" />
            </div>

            {/* Micro Chip Graphic */}
            <div className="w-10 h-8 rounded-md bg-gradient-to-br from-[#e5e5ea] to-[#8e8e93] border border-white/40 opacity-80" />

            <div className="flex justify-between items-end">
              <div>
                <div className="text-[10px] text-[#86868b] font-mono uppercase">Order Ref</div>
                <div className="text-xs font-mono font-semibold text-white">
                  {caseData.order?.external_order_id || "ord_demo_101"}
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-[#86868b] font-mono uppercase">Amount Due</div>
                <div className="text-base font-mono font-semibold text-white">
                  {formatINR(caseData.amount_at_risk_cents)}
                </div>
              </div>
            </div>
          </div>

          {/* Context Card */}
          <div className="apple-card p-6 space-y-4">
            <div className="flex justify-between items-center text-xs pb-3 border-b border-white/[0.06]">
              <span className="text-[#86868b]">Customer</span>
              <span className="text-white font-medium">{caseData.customer?.name || "Verified Customer"}</span>
            </div>
            <div className="flex justify-between items-center text-xs pb-3 border-b border-white/[0.06]">
              <span className="text-[#86868b]">Previous Failure</span>
              <span className="text-[#ffd60a] font-medium">{caseData.failure_category.replace(/_/g, " ")}</span>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-[#30d158]">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Completing payment unlocks order fulfillment instantly.</span>
            </div>
          </div>
        </div>

        {/* Right Column: Checkout Instrument Selector */}
        <div className="md:col-span-7 space-y-5">
          <div className="apple-card p-7 space-y-6">
            <div className="flex items-center justify-between pb-2">
              <div>
                <h3 className="text-base font-semibold text-white">Select Payment Method</h3>
                <p className="text-xs text-[#86868b] mt-0.5">Choose preferred test instrument</p>
              </div>
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[#30d158] font-mono font-semibold">
                TEST MODE
              </span>
            </div>

            {/* Apple-Style Segmented Selector */}
            <div className="grid grid-cols-3 gap-2.5">
              <button
                type="button"
                onClick={() => setPaymentMethod("upi")}
                className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col gap-1 ${
                  paymentMethod === "upi"
                    ? "bg-white/10 border-white/20 text-white shadow-sm"
                    : "bg-white/[0.02] border-white/[0.06] text-[#86868b] hover:text-white"
                }`}
              >
                <Smartphone className="w-4 h-4 text-[#64d2ff]" />
                <span className="text-xs font-semibold">UPI / QR</span>
                <span className="text-[10px] text-[#86868b]">GPay, PhonePe</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("card")}
                className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col gap-1 ${
                  paymentMethod === "card"
                    ? "bg-white/10 border-white/20 text-white shadow-sm"
                    : "bg-white/[0.02] border-white/[0.06] text-[#86868b] hover:text-white"
                }`}
              >
                <CreditCard className="w-4 h-4 text-[#bf5af2]" />
                <span className="text-xs font-semibold">Cards</span>
                <span className="text-[10px] text-[#86868b]">Test Card</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("netbanking")}
                className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col gap-1 ${
                  paymentMethod === "netbanking"
                    ? "bg-white/10 border-white/20 text-white shadow-sm"
                    : "bg-white/[0.02] border-white/[0.06] text-[#86868b] hover:text-white"
                }`}
              >
                <Building2 className="w-4 h-4 text-[#30d158]" />
                <span className="text-xs font-semibold">NetBanking</span>
                <span className="text-[10px] text-[#86868b]">HDFC, ICICI</span>
              </button>
            </div>

            {/* Instrument Details */}
            <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06] space-y-3">
              {paymentMethod === "upi" && (
                <div className="space-y-2">
                  <label className="text-xs font-medium text-[#86868b] block">Virtual Payment Address (VPA)</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={upiVpa}
                      onChange={(e) => setUpiVpa(e.target.value)}
                      className="apple-input flex-1 px-3.5 py-2 text-xs text-white font-mono"
                    />
                    <div className="px-3 py-2 rounded-xl bg-white/[0.05] border border-white/10 text-[10px] font-semibold text-white flex items-center gap-1.5 shrink-0">
                      <Zap className="w-3.5 h-3.5 text-[#64d2ff]" /> Instant Intent
                    </div>
                  </div>
                </div>
              )}

              {paymentMethod === "card" && (
                <div className="space-y-2">
                  <div className="text-xs font-medium text-[#86868b]">Simulated Card</div>
                  <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.08] font-mono text-xs text-white flex justify-between">
                    <span>•••• •••• •••• 4242</span>
                    <span>12/28 • CVV ***</span>
                  </div>
                </div>
              )}

              {paymentMethod === "netbanking" && (
                <div className="space-y-2">
                  <div className="text-xs font-medium text-[#86868b]">Select Bank</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-white/10 border border-white/20 text-white font-semibold flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#0071e3]" /> HDFC Bank
                    </div>
                    <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] text-[#86868b] flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-white/20" /> ICICI Bank
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Stepper Status */}
            {simulationStep !== "IDLE" && (
              <div className="p-4 rounded-2xl bg-black/60 border border-white/10 space-y-2 text-xs">
                <div className="flex items-center justify-between text-[#86868b]">
                  <span>Execution Status</span>
                  <span className="font-mono text-[#64d2ff] font-semibold">{simulationStep}</span>
                </div>
                <div className="space-y-1.5 text-[11px] text-[#30d158]">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                    <span>Payment Authorized on Razorpay Test Gateway</span>
                  </div>
                  {simulationStep !== "SUBMITTING" && (
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                      <span>HMAC-SHA256 Webhook Ingested</span>
                    </div>
                  )}
                  {simulationStep === "RECOVERED" && (
                    <div className="flex items-center gap-2 font-semibold text-white">
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#30d158] shrink-0" />
                      <span>Reconciled & Added to Hash-Chain</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action CTA */}
            {!isAlreadyRecovered ? (
              <button
                type="button"
                onClick={handleSimulatePayment}
                disabled={isProcessing}
                className="w-full py-3.5 px-5 rounded-full bg-white hover:bg-[#e5e5ea] text-black font-semibold text-xs shadow-[0_10px_30px_rgba(255,255,255,0.2)] transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-[#0071e3]" />
                    <span>Processing Payment Simulation...</span>
                  </>
                ) : (
                  <>
                    <span>Pay {formatINR(caseData.amount_at_risk_cents)} & Complete Recovery</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            ) : (
              <div className="p-5 rounded-2xl bg-[#30d158]/10 border border-[#30d158]/30 text-center space-y-3">
                <CheckCircle2 className="w-8 h-8 text-[#30d158] mx-auto" />
                <div>
                  <h4 className="text-sm font-semibold text-white">Payment Recovered Successfully</h4>
                  <p className="text-xs text-[#86868b] mt-0.5">
                    {formatINR(caseData.amount_at_risk_cents)} verified and settled.
                  </p>
                </div>
                <div className="flex justify-center gap-2 pt-1">
                  <Link
                    href={`/cases/${caseData.id}`}
                    className="px-4 py-1.5 rounded-full bg-[#30d158] hover:bg-[#28cd41] text-black text-xs font-semibold transition"
                  >
                    View Case Dossier
                  </Link>
                  <Link
                    href="/"
                    className="px-4 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition"
                  >
                    Cockpit
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
