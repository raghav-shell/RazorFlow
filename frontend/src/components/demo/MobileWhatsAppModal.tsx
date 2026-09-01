"use client";

import React from "react";
import Link from "next/link";
import {
  X,
  ShieldCheck,
  CheckCheck,
  ArrowRight,
  ExternalLink,
  Bot,
  Sparkles,
  Smartphone,
  Info,
} from "lucide-react";
import { RecoveryCase } from "@/lib/api/types";
import { formatINR } from "@/lib/utils";

interface MobileWhatsAppModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseData: RecoveryCase;
}

export function MobileWhatsAppModal({
  isOpen,
  onClose,
  caseData,
}: MobileWhatsAppModalProps) {
  if (!isOpen) return null;

  const customerName = caseData.customer?.name || "Customer";
  const orderRef = caseData.order?.external_order_id || "order_demo_101";
  const amountFormatted = formatINR(caseData.amount_at_risk_cents);

  // Extract latest Gemini advisory reasoning if present
  const latestDecision =
    caseData.decisions && caseData.decisions.length > 0
      ? caseData.decisions[caseData.decisions.length - 1]
      : null;

  const reasoning =
    latestDecision?.ai_reasoning ||
    "Payment dropped at bank authentication. Payment link prepared for instant retry.";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
      <div className="relative w-full max-w-sm rounded-[36px] border-4 border-slate-700/80 bg-[#070a14] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9)] p-4 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 z-20 text-slate-400 hover:text-white p-1.5 rounded-full bg-slate-900/90 border border-slate-700 transition cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Dynamic Island Top Bar */}
        <div className="text-center pb-2 pt-1">
          <div className="w-24 h-4 bg-black rounded-full mx-auto mb-2 flex items-center justify-between px-2.5 border border-white/10">
            <div className="w-2 h-2 bg-slate-900 rounded-full border border-slate-800" />
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
          </div>
          <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400 flex items-center justify-center gap-1.5">
            <Smartphone className="w-3.5 h-3.5" /> Customer WhatsApp Simulator
          </span>
        </div>

        {/* WhatsApp App Mockup */}
        <div className="rounded-[24px] border border-white/[0.08] bg-[#0b141a] overflow-hidden shadow-inner flex flex-col h-[490px]">
          {/* WhatsApp Chat Top Header */}
          <div className="bg-[#1f2c34] p-3.5 flex items-center gap-3 border-b border-slate-700/50">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-xs font-black text-white shadow-md border border-white/20">
              RF
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-slate-100 truncate">
                  RazorFlow Recovery
                </span>
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              </div>
              <span className="text-[10px] text-emerald-400 font-medium">Official Business Account</span>
            </div>
          </div>

          {/* Chat Messages Area */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3 bg-[#0b141a]">
            {/* Timestamp pill */}
            <div className="text-center">
              <span className="text-[9px] px-2.5 py-0.5 rounded-full bg-[#182229] text-slate-400 font-mono">
                TODAY • 12:42 PM
              </span>
            </div>

            {/* AI Advisor Badge (Transparency) */}
            <div className="p-2.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-[10px] text-purple-300 flex items-start gap-2">
              <Bot className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-purple-200">Gemini Strategy Reasoning:</strong>
                <p className="text-purple-300/80 mt-0.5 line-clamp-2">{reasoning}</p>
              </div>
            </div>

            {/* Customer Recovery Chat Bubble */}
            <div className="max-w-[92%] p-3.5 rounded-2xl rounded-tl-none bg-[#005c4b] text-white text-xs shadow-lg space-y-2.5">
              <p className="font-medium">
                Hello <strong>{customerName}</strong> 👋
              </p>
              <p className="text-slate-100 text-[11px] leading-relaxed">
                Your payment of <strong className="text-emerald-200">{amountFormatted}</strong> for order{" "}
                <span className="font-mono bg-[#004739] px-1.5 py-0.5 rounded">#{orderRef}</span> could not be completed at your bank.
              </p>
              <p className="text-slate-100 text-[11px] leading-relaxed">
                We have prepared a one-click, secure Razorpay checkout link so your reserved items remain confirmed.
              </p>

              {/* Payment Link Card Inside Bubble */}
              <div className="p-3 rounded-xl bg-[#004739] border border-emerald-400/30 space-y-2">
                <div className="text-[10px] text-emerald-300 font-bold uppercase tracking-wider">
                  Razorpay Hosted Checkout
                </div>
                <div className="text-sm font-black text-white flex justify-between items-center font-mono">
                  <span>Amount Due</span>
                  <span>{amountFormatted}</span>
                </div>

                <Link
                  href={`/pay/${caseData.payment_link_id || caseData.id}`}
                  onClick={onClose}
                  className="w-full mt-2 py-2.5 px-3 rounded-xl bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 text-slate-950 font-black text-xs flex items-center justify-center gap-1.5 transition shadow-lg shadow-emerald-950/40 cursor-pointer"
                >
                  <span>Pay Now (Demo Checkout)</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Bubble timestamp and read receipt */}
              <div className="flex items-center justify-end gap-1 text-[9px] text-slate-300 font-mono pt-1">
                <span>12:42 PM</span>
                <CheckCheck className="w-3.5 h-3.5 text-cyan-300" />
              </div>
            </div>
          </div>

          {/* Simulator Disclaimer Footer */}
          <div className="bg-[#1f2c34] p-2.5 text-center text-[10px] text-slate-400 border-t border-slate-700/50 flex items-center justify-center gap-1.5">
            <Info className="w-3 h-3 text-blue-400" />
            <span>Simulated message preview • No actual WhatsApp dispatched</span>
          </div>
        </div>
      </div>
    </div>
  );
}
