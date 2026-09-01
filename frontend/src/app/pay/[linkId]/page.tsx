"use client";

import React, { useEffect, useState, useRef } from "react";
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
  ScanFace,
  QrCode,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { RecoveryCase } from "@/lib/api/types";
import { formatINR } from "@/lib/utils";
import { soundFX } from "@/lib/audio/soundFX";
import { RecoveryCelebration } from "@/components/ui/RecoveryCelebration";

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
  const [showCelebration, setShowCelebration] = useState(false);

  // 3D Card Physics State
  const cardRef = useRef<HTMLDivElement>(null);
  const [cardRotate, setCardRotate] = useState({ x: 0, y: 0 });
  const [sheenPos, setSheenPos] = useState({ x: 50, y: 50 });

  const handleCardMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -12;
    const rotateY = ((x - centerX) / centerX) * 12;

    setCardRotate({ x: rotateX, y: rotateY });
    setSheenPos({ x: (x / rect.width) * 100, y: (y / rect.height) * 100 });
  };

  const handleCardMouseLeave = () => {
    setCardRotate({ x: 0, y: 0 });
    setSheenPos({ x: 50, y: 50 });
  };

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
    soundFX.playPulse();
    setIsProcessing(true);
    setError(null);
    setSimulationStep("SUBMITTING");

    try {
      await new Promise((r) => setTimeout(r, 600));
      soundFX.playClick();
      setSimulationStep("WEBHOOK_RECEIVED");

      await new Promise((r) => setTimeout(r, 600));
      soundFX.playClick();
      setSimulationStep("VERIFYING");

      const res = await apiClient.simulatePayment("demo-store", caseData.id);
      
      await new Promise((r) => setTimeout(r, 500));
      setSimulationResult(res);
      setSimulationStep("RECOVERED");
      setShowCelebration(true);
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
        <h2 className="text-lg font-semibold text-white">Checkout Session Expired</h2>
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
      {/* Particle Fountain on Recovery */}
      <RecoveryCelebration
        show={showCelebration}
        amountFormatted={formatINR(caseData.amount_at_risk_cents)}
        onComplete={() => setShowCelebration(false)}
      />

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
          {/* Apple Titanium Card with Interactive 3D Physics */}
          <div
            ref={cardRef}
            onMouseMove={handleCardMouseMove}
            onMouseLeave={handleCardMouseLeave}
            style={{
              transform: `perspective(1000px) rotateX(${cardRotate.x}deg) rotateY(${cardRotate.y}deg)`,
              transition: "transform 0.15s ease-out",
            }}
            className="relative h-56 rounded-3xl p-6 bg-gradient-to-br from-[#242429] via-[#141418] to-[#0a0a0d] border-[0.5px] border-white/25 shadow-[0_30px_70px_rgba(0,0,0,0.9)] flex flex-col justify-between overflow-hidden cursor-pointer select-none"
          >
            {/* Dynamic Holographic Cursor Sheen */}
            <div
              className="absolute inset-0 pointer-events-none transition-opacity duration-300"
              style={{
                background: `radial-gradient(circle at ${sheenPos.x}% ${sheenPos.y}%, rgba(255,255,255,0.18) 0%, rgba(100,210,255,0.06) 40%, transparent 80%)`,
              }}
            />

            <div className="flex justify-between items-start z-10">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center font-bold text-xs text-white border border-white/20">
                  RF
                </div>
                <span className="text-xs font-semibold text-white tracking-tight">RazorFlow Titanium</span>
              </div>
              <Wifi className="w-5 h-5 text-white/50 rotate-90" />
            </div>

            {/* Gold EMV Chip Graphic */}
            <div className="w-10 h-8 rounded-md bg-gradient-to-br from-[#ffd60a] via-[#ff9f0a] to-[#d4af37] border border-amber-300/60 shadow-sm opacity-90 z-10" />

            <div className="flex justify-between items-end z-10">
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
                onClick={() => {
                  soundFX.playClick();
                  setPaymentMethod("upi");
                }}
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
                onClick={() => {
                  soundFX.playClick();
                  setPaymentMethod("card");
                }}
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
                onClick={() => {
                  soundFX.playClick();
                  setPaymentMethod("netbanking");
                }}
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
                  <div className="text-xs font-medium text-[#86868b]">Simulated Bank Gateway</div>
                  <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-xs text-white flex justify-between">
                    <span>HDFC Bank (Retail NetBanking)</span>
                    <span className="text-[#30d158] font-mono font-semibold">Online (99.8%)</span>
                  </div>
                </div>
              )}
            </div>

            {/* Simulation Progress Stepper */}
            {simulationStep !== "IDLE" && (
              <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.08] space-y-3">
                <div className="text-[11px] font-semibold text-white uppercase tracking-wider">
                  Settlement Verification Pipeline
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2">
                    {simulationStep === "SUBMITTING" ? (
                      <RefreshCw className="w-3.5 h-3.5 text-[#0071e3] animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#30d158]" />
                    )}
                    <span className="text-white">Authorizing transaction on mock gateway</span>
                  </div>

                  {(simulationStep === "WEBHOOK_RECEIVED" ||
                    simulationStep === "VERIFYING" ||
                    simulationStep === "RECOVERED") && (
                    <div className="flex items-center gap-2">
                      {simulationStep === "WEBHOOK_RECEIVED" ? (
                        <RefreshCw className="w-3.5 h-3.5 text-[#0071e3] animate-spin" />
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#30d158]" />
                      )}
                      <span className="text-white">HMAC-SHA256 Webhook ingested</span>
                    </div>
                  )}

                  {(simulationStep === "VERIFYING" ||
                    simulationStep === "RECOVERED") && (
                    <div className="flex items-center gap-2">
                      {simulationStep === "VERIFYING" ? (
                        <RefreshCw className="w-3.5 h-3.5 text-[#0071e3] animate-spin" />
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#30d158]" />
                      )}
                      <span className="text-white">Cryptographic ledger block minted</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Primary Action Button */}
            {!isAlreadyRecovered ? (
              <button
                type="button"
                onClick={handleSimulatePayment}
                disabled={isProcessing}
                className="w-full py-3.5 px-4 rounded-full bg-white hover:bg-[#e5e5ea] text-black font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-[0_4px_20px_rgba(255,255,255,0.2)] hover:scale-[1.01] active:scale-[0.99] cursor-pointer disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-[#0071e3]" />
                    <span>Processing Payment Capture...</span>
                  </>
                ) : (
                  <>
                    <ScanFace className="w-4 h-4 text-[#0071e3]" />
                    <span>Authorize & Pay {formatINR(caseData.amount_at_risk_cents)}</span>
                  </>
                )}
              </button>
            ) : (
              <div className="p-4 rounded-2xl bg-[#30d158]/10 border border-[#30d158]/30 text-center space-y-2">
                <CheckCircle2 className="w-6 h-6 text-[#30d158] mx-auto" />
                <div className="text-sm font-semibold text-white">Payment Recovered & Verified</div>
                <p className="text-xs text-[#86868b]">
                  Settlement reconciled into immutable ledger.
                </p>
                <Link
                  href={`/cases/${caseData.id}`}
                  className="inline-flex items-center gap-1.5 text-xs text-[#64d2ff] hover:text-white font-medium mt-1"
                >
                  <span>Return to Case Dossier</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}

            {/* Footer Trust Bar */}
            <div className="flex items-center justify-center gap-4 text-[10px] text-[#86868b] pt-2 border-t border-white/[0.04]">
              <span className="flex items-center gap-1">
                <Lock className="w-3 h-3 text-[#30d158]" /> 256-Bit SSL
              </span>
              <span>•</span>
              <span>PCI-DSS Level 1</span>
              <span>•</span>
              <span>Instant Bank Confirmation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
