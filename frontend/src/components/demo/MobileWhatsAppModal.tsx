"use client";

import React from "react";
import Link from "next/link";
import {
  X,
  ShieldCheck,
  CheckCheck,
  ExternalLink,
  Bot,
  Smartphone,
  ChevronLeft,
  Phone,
  Video,
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

  const latestDecision =
    caseData.decisions && caseData.decisions.length > 0
      ? caseData.decisions[caseData.decisions.length - 1]
      : null;

  const reasoning =
    latestDecision?.ai_reasoning ||
    "Payment dropped at bank authentication. Payment link prepared for instant retry.";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl">
      {/* iPhone 16 Pro Titanium Chassis */}
      <div className="relative w-full max-w-[340px] rounded-[50px] p-[10px] bg-gradient-to-b from-[#2a2a2e] via-[#1a1a1e] to-[#0a0a0d] shadow-[0_30px_90px_rgba(0,0,0,0.95),inset_0_1px_1px_rgba(255,255,255,0.3)] border border-white/20">
        
        {/* Close Action Button */}
        <button
          onClick={onClose}
          className="absolute -top-3 -right-3 z-30 text-[#86868b] hover:text-white p-2 rounded-full bg-[#1c1c22] border border-white/20 shadow-xl transition cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        {/* iPhone Screen Area */}
        <div className="relative rounded-[42px] bg-[#000000] overflow-hidden flex flex-col h-[560px] border border-black select-none">
          
          {/* Dynamic Island */}
          <div className="pt-2.5 pb-2 px-6 flex items-center justify-between z-20">
            <span className="text-[12px] font-semibold text-white font-mono">9:41</span>
            
            {/* Dynamic Island Capsule */}
            <div className="w-[90px] h-[24px] bg-black rounded-full flex items-center justify-between px-2 border border-white/10 shadow-inner">
              <div className="w-2 h-2 rounded-full bg-[#1c1c22] border border-white/10" />
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#30d158] animate-pulse" />
                <span className="text-[9px] text-white/80 font-mono">RF</span>
              </div>
            </div>

            <div className="flex items-center gap-1 text-[11px] text-white">
              <span>5G</span>
              <div className="w-4 h-2 border border-white rounded-[2px] p-[1px] flex items-center">
                <div className="w-full h-full bg-[#30d158] rounded-[1px]" />
              </div>
            </div>
          </div>

          {/* WhatsApp Header */}
          <div className="bg-[#121b22] px-3.5 py-2.5 flex items-center justify-between border-b border-white/[0.08]">
            <div className="flex items-center gap-2.5">
              <ChevronLeft className="w-4 h-4 text-[#0071e3]" />
              <div className="w-8 h-8 rounded-full bg-[#0071e3] flex items-center justify-center text-xs font-semibold text-white shadow-sm">
                RF
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-semibold text-white truncate">
                    RazorFlow
                  </span>
                  <ShieldCheck className="w-3.5 h-3.5 text-[#30d158] shrink-0" />
                </div>
                <span className="text-[10px] text-[#30d158] font-mono">Verified Business</span>
              </div>
            </div>

            <div className="flex items-center gap-3 text-[#0071e3]">
              <Video className="w-4 h-4 opacity-70" />
              <Phone className="w-3.5 h-3.5 opacity-70" />
            </div>
          </div>

          {/* Chat Messages Body */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3 bg-[#0b141a]">
            {/* Timestamp */}
            <div className="text-center">
              <span className="text-[9px] px-2.5 py-0.5 rounded-full bg-[#182229] text-[#86868b] font-mono">
                TODAY
              </span>
            </div>

            {/* AI Advisor Badge */}
            <div className="p-2.5 rounded-2xl bg-[#bf5af2]/10 border border-[#bf5af2]/30 text-[10px] text-[#bf5af2] space-y-1">
              <div className="flex items-center gap-1.5 font-semibold">
                <Bot className="w-3.5 h-3.5" />
                <span>Gemini Strategy Advisory</span>
              </div>
              <p className="text-white/80 leading-relaxed text-[10px]">
                {reasoning}
              </p>
            </div>

            {/* WhatsApp Bubble */}
            <div className="max-w-[92%] p-3.5 rounded-2xl rounded-tl-none bg-[#005c4b] text-white text-xs shadow-md space-y-2">
              <p className="font-semibold text-xs">
                Hi {customerName},
              </p>
              <p className="text-white/90 text-[11px] leading-relaxed">
                Your payment of <strong className="text-[#64d2ff]">{amountFormatted}</strong> for order <span className="font-mono bg-black/20 px-1 py-0.5 rounded">#{orderRef}</span> encountered a bank auth dropoff.
              </p>
              <p className="text-white/90 text-[11px] leading-relaxed">
                We've reserved your items and created a secure 1-click Razorpay hosted checkout link:
              </p>

              {/* In-Message Checkout Card */}
              <div className="p-3 rounded-xl bg-black/30 border border-white/10 space-y-2">
                <div className="flex justify-between items-center text-[10px] text-[#64d2ff] uppercase font-mono">
                  <span>Razorpay Checkout</span>
                  <span className="text-white font-semibold">{amountFormatted}</span>
                </div>

                <Link
                  href={`/pay/${caseData.payment_link_id || caseData.id}`}
                  onClick={onClose}
                  className="w-full py-2 px-3 rounded-lg bg-white text-black font-semibold text-xs flex items-center justify-center gap-1.5 transition hover:bg-[#e5e5ea] cursor-pointer"
                >
                  <span>Complete Payment</span>
                  <ExternalLink className="w-3 h-3 text-black" />
                </Link>
              </div>

              <div className="flex items-center justify-end gap-1 text-[9px] text-white/60 font-mono pt-0.5">
                <span>9:41 AM</span>
                <CheckCheck className="w-3.5 h-3.5 text-[#64d2ff]" />
              </div>
            </div>
          </div>

          {/* iPhone Home Indicator */}
          <div className="py-2 flex justify-center bg-[#0b141a]">
            <div className="w-28 h-1 bg-white/30 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
