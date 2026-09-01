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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-sm rounded-3xl border border-slate-700 bg-[#070a13] shadow-2xl p-4 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 text-slate-400 hover:text-white p-1 rounded-full bg-slate-900 border border-slate-700 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Smartphone Header / Frame Indicator */}
        <div className="text-center pb-2">
          <div className="w-20 h-4 bg-slate-800 rounded-full mx-auto mb-2 flex items-center justify-center">
            <div className="w-2.5 h-2.5 bg-slate-900 rounded-full mr-2" />
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 flex items-center justify-center gap-1">
            <Smartphone className="w-3 h-3" /> Customer Communication Simulator
          </span>
        </div>

        {/* WhatsApp App Mockup */}
        <div className="rounded-2xl border border-slate-800 bg-[#0b141a] overflow-hidden shadow-inner flex flex-col h-[480px]">
          {/* WhatsApp Chat Top Header */}
          <div className="bg-[#1f2c34] p-3 flex items-center gap-2.5 border-b border-slate-700/50">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-xs font-bold text-white shadow">
              RF
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                <span className="text-xs font-bold text-slate-100 truncate">
                  Demo Merchant Enterprise
                </span>
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              </div>
              <span className="text-[10px] text-slate-400">Official Business Account</span>
            </div>
          </div>

          {/* Chat Messages Area */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3 bg-[radial-gradient(#1f2c34_1px,transparent_1px)] [background-size:16px_16px]">
            {/* Timestamp pill */}
            <div className="text-center">
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#182229] text-slate-400 font-mono">
                TODAY • 12:42 PM
              </span>
            </div>

            {/* AI Advisor Badge (Transparency) */}
            <div className="p-2 rounded-lg bg-purple-950/40 border border-purple-500/30 text-[10px] text-purple-300 flex items-start gap-1.5">
              <Bot className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <strong>Gemini AI Recovery Strategy:</strong>
                <p className="text-purple-200/80 mt-0.5 line-clamp-2">{reasoning}</p>
              </div>
            </div>

            {/* Customer Recovery Chat Bubble */}
            <div className="max-w-[90%] p-3 rounded-2xl rounded-tl-none bg-[#005c4b] text-white text-xs shadow-md space-y-2">
              <p>
                Hello <strong>{customerName}</strong> 👋
              </p>
              <p className="text-slate-100 text-[11px] leading-relaxed">
                Your payment of <strong>{amountFormatted}</strong> for order{" "}
                <span className="font-mono bg-[#004739] px-1 py-0.5 rounded">#{orderRef}</span> could not be completed at your bank.
              </p>
              <p className="text-slate-100 text-[11px] leading-relaxed">
                We have prepared an instant, secure Razorpay recovery checkout link so you don&apos;t lose your reserved order.
              </p>

              {/* Payment Link Card Inside Bubble */}
              <div className="p-2.5 rounded-xl bg-[#004739] border border-emerald-500/30 space-y-1.5">
                <div className="text-[10px] text-emerald-300 font-semibold uppercase tracking-wider">
                  Razorpay Hosted Payment Link
                </div>
                <div className="text-sm font-bold text-white flex justify-between items-center">
                  <span>Amount Due</span>
                  <span>{amountFormatted}</span>
                </div>

                <Link
                  href={`/pay/${caseData.payment_link_id || caseData.id}`}
                  onClick={onClose}
                  className="w-full mt-2 py-2 px-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 transition shadow cursor-pointer"
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
          <div className="bg-[#1f2c34] p-2 text-center text-[10px] text-slate-400 border-t border-slate-700/50 flex items-center justify-center gap-1">
            <Info className="w-3 h-3 text-blue-400" />
            <span>Simulated message preview • No actual WhatsApp dispatched</span>
          </div>
        </div>
      </div>
    </div>
  );
}
