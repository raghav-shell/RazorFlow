"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Calculator,
  TrendingUp,
  ShieldCheck,
  ArrowRight,
  Info,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import { formatINR } from "@/lib/utils";

export default function ROICalculatorPage() {
  const presets = [
    { label: "Startup D2C", gmv: 2500000, failureRate: 20, aov: 1500, cost: 15000 },
    { label: "Growth Brand", gmv: 20000000, failureRate: 18, aov: 2500, cost: 49000 },
    { label: "Enterprise", gmv: 100000000, failureRate: 16, aov: 4000, cost: 149000 },
  ];

  const [monthlyGMV, setMonthlyGMV] = useState(20000000);
  const [failureRatePct, setFailureRatePct] = useState(18);
  const [aovRupees, setAovRupees] = useState(2500);
  const [recoveryRatePct, setRecoveryRatePct] = useState(44.5);
  const [monthlySaaSCost, setMonthlySaaSCost] = useState(49000);

  function applyPreset(p: typeof presets[0]) {
    setMonthlyGMV(p.gmv);
    setFailureRatePct(p.failureRate);
    setAovRupees(p.aov);
    setMonthlySaaSCost(p.cost);
  }

  const monthlyGMVPaise = Math.round(monthlyGMV * 100);
  const failedGMVPaise = Math.round(monthlyGMVPaise * (failureRatePct / 100));
  const estimatedRecoveredPaise = Math.round(failedGMVPaise * (recoveryRatePct / 100));

  const totalFailedTransactions = Math.max(1, Math.round(monthlyGMV / Math.max(1, aovRupees) * (failureRatePct / 100)));
  const totalInterventionCostPaise = Math.round(totalFailedTransactions * 230);

  const totalMonthlyCostPaise = Math.round(monthlySaaSCost * 100) + totalInterventionCostPaise;
  const netMonthlyRecoveredPaise = Math.max(0, estimatedRecoveredPaise - totalMonthlyCostPaise);
  const annualizedNetBenefitPaise = netMonthlyRecoveredPaise * 12;

  const roiMultiple =
    totalMonthlyCostPaise > 0
      ? (netMonthlyRecoveredPaise / totalMonthlyCostPaise).toFixed(1)
      : "0.0";

  return (
    <div className="space-y-8 pb-28 max-w-7xl mx-auto px-2 sm:px-4">
      {/* Title & Header */}
      <section className="pt-4 pb-2 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
            <Sparkles className="w-3.5 h-3.5 text-[#30d158]" />
            <span className="text-xs font-medium text-[#86868b]">Financial Impact Model</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-white">
            Executive ROI & Financial Yield
          </h1>
          <p className="text-sm text-[#86868b] leading-relaxed">
            Deterministic financial modeling of revenue rescued, intervention costs, and net bottom-line return.
          </p>
        </div>

        {/* Preset Selector */}
        <div className="apple-segmented inline-flex items-center self-start">
          {presets.map((p) => (
            <button
              key={p.label}
              onClick={() => applyPreset(p)}
              className="px-3.5 py-1.5 rounded-full text-xs font-medium text-[#86868b] hover:text-white transition-all cursor-pointer"
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      {/* Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Sliders */}
        <div className="lg:col-span-6 space-y-6">
          <div className="apple-card p-7 space-y-6">
            <h2 className="text-sm font-semibold text-white tracking-tight pb-3 border-b border-white/[0.06]">
              Volume & Failure Inputs
            </h2>

            {/* Monthly GMV Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#86868b]">Monthly GMV</span>
                <span className="font-semibold text-white font-mono text-sm">
                  {formatINR(monthlyGMVPaise)}
                </span>
              </div>
              <input
                type="range"
                min="1000000"
                max="500000000"
                step="1000000"
                value={monthlyGMV}
                onChange={(e) => setMonthlyGMV(Number(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-[#0071e3]"
              />
            </div>

            {/* Payment Failure Rate Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#86868b]">Payment Failure Rate</span>
                <span className="font-semibold text-[#ffd60a] font-mono text-sm">
                  {failureRatePct}%
                </span>
              </div>
              <input
                type="range"
                min="5"
                max="35"
                step="0.5"
                value={failureRatePct}
                onChange={(e) => setFailureRatePct(Number(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-[#ffd60a]"
              />
            </div>

            {/* Average Order Value Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#86868b]">Average Order Value (AOV)</span>
                <span className="font-semibold text-white font-mono text-sm">
                  ₹{aovRupees.toLocaleString("en-IN")}
                </span>
              </div>
              <input
                type="range"
                min="500"
                max="25000"
                step="500"
                value={aovRupees}
                onChange={(e) => setAovRupees(Number(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-[#bf5af2]"
              />
            </div>

            {/* Projected Recovery Rate */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#86868b]">Projected Recovery Rate</span>
                <span className="font-semibold text-[#30d158] font-mono text-sm">
                  {recoveryRatePct}%
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="75"
                step="0.5"
                value={recoveryRatePct}
                onChange={(e) => setRecoveryRatePct(Number(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-[#30d158]"
              />
            </div>
          </div>

          {/* Methodology Info */}
          <div className="apple-card p-5 text-xs text-[#86868b] space-y-1.5">
            <div className="flex items-center gap-1.5 text-white font-medium">
              <Info className="w-3.5 h-3.5 text-[#0071e3]" />
              <span>Calculation Logic</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Deterministic integer paise math: Gross ERV = ⌊P_ML × Amount⌋. Net recovery subtracts SaaS licensing and link dispatch fees.
            </p>
          </div>
        </div>

        {/* Right Column: Hero ROI Tile & Breakdown */}
        <div className="lg:col-span-6 space-y-6">
          {/* Primary ROI Hero Box */}
          <div className="apple-card p-7 space-y-4 relative overflow-hidden group">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#30d158]">
              Estimated Monthly Net Revenue Uplift
            </span>
            <div className="text-4xl sm:text-5xl font-semibold text-white tracking-tight font-mono">
              {formatINR(netMonthlyRecoveredPaise)}
            </div>
            <p className="text-xs text-[#86868b] leading-relaxed max-w-md">
              Bottom-line profit rescued from dropped payments with zero merchant chasing.
            </p>

            <div className="grid grid-cols-2 gap-5 pt-6 border-t border-white/[0.06]">
              <div>
                <span className="text-[10px] text-[#86868b] uppercase tracking-wider">
                  Annualized Gain
                </span>
                <div className="text-lg font-semibold text-white font-mono mt-0.5">
                  {formatINR(annualizedNetBenefitPaise)}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-[#86868b] uppercase tracking-wider">
                  ROI Multiplier
                </span>
                <div className="text-lg font-semibold text-[#30d158] font-mono mt-0.5 flex items-baseline gap-1">
                  <span>{roiMultiple}x</span>
                  <span className="text-xs text-[#86868b] font-normal">Return</span>
                </div>
              </div>
            </div>
          </div>

          {/* Breakdown Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="apple-card p-5 space-y-1">
              <span className="text-[10px] text-[#86868b] uppercase tracking-wider">GMV at Risk</span>
              <div className="text-base font-semibold text-[#ff453a] font-mono">
                {formatINR(failedGMVPaise)}
              </div>
              <span className="text-[10px] text-[#86868b] block font-mono">
                {totalFailedTransactions.toLocaleString("en-IN")} dropped orders/mo
              </span>
            </div>

            <div className="apple-card p-5 space-y-1">
              <span className="text-[10px] text-[#86868b] uppercase tracking-wider">Gross Recovered</span>
              <div className="text-base font-semibold text-[#30d158] font-mono">
                {formatINR(estimatedRecoveredPaise)}
              </div>
              <span className="text-[10px] text-[#86868b] block font-mono">
                {(totalFailedTransactions * (recoveryRatePct / 100)).toFixed(0)} rescued
              </span>
            </div>

            <div className="apple-card p-5 space-y-1">
              <span className="text-[10px] text-[#86868b] uppercase tracking-wider">Dispatch Cost</span>
              <div className="text-base font-semibold text-white font-mono">
                {formatINR(totalInterventionCostPaise)}
              </div>
              <span className="text-[10px] text-[#86868b] block">₹2.30 per attempt</span>
            </div>

            <div className="apple-card p-5 space-y-1">
              <span className="text-[10px] text-[#86868b] uppercase tracking-wider">Total Spend</span>
              <div className="text-base font-semibold text-white font-mono">
                {formatINR(totalMonthlyCostPaise)}
              </div>
              <span className="text-[10px] text-[#86868b] block">Platform + links</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
