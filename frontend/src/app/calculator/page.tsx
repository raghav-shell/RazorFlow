"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Calculator,
  TrendingUp,
  DollarSign,
  ShieldCheck,
  Zap,
  ArrowRight,
  Info,
  Sparkles,
  PieChart,
  BarChart3,
  CheckCircle2,
} from "lucide-react";
import { formatINR } from "@/lib/utils";

export default function ROICalculatorPage() {
  // Preset Profiles
  const presets = [
    { label: "Startup D2C", gmv: 2500000, failureRate: 20, aov: 1500, cost: 15000 },
    { label: "Growth Brand", gmv: 20000000, failureRate: 18, aov: 2500, cost: 49000 },
    { label: "Enterprise Merchant", gmv: 100000000, failureRate: 16, aov: 4000, cost: 149000 },
  ];

  // Inputs State
  const [monthlyGMV, setMonthlyGMV] = useState(20000000); // ₹2 Cr
  const [failureRatePct, setFailureRatePct] = useState(18); // 18%
  const [aovRupees, setAovRupees] = useState(2500); // ₹2,500
  const [recoveryRatePct, setRecoveryRatePct] = useState(44.5); // 44.5% (Model Baseline)
  const [monthlySaaSCost, setMonthlySaaSCost] = useState(49000); // ₹49,000

  function applyPreset(p: typeof presets[0]) {
    setMonthlyGMV(p.gmv);
    setFailureRatePct(p.failureRate);
    setAovRupees(p.aov);
    setMonthlySaaSCost(p.cost);
  }

  // Financial Calculations (Paise integer math)
  const monthlyGMVPaise = Math.round(monthlyGMV * 100);
  const failedGMVPaise = Math.round(monthlyGMVPaise * (failureRatePct / 100));
  const estimatedRecoveredPaise = Math.round(failedGMVPaise * (recoveryRatePct / 100));

  // Estimated intervention costs (e.g. ₹2.00 link fee + ₹0.30 messaging per failed transaction)
  const totalFailedTransactions = Math.max(1, Math.round(monthlyGMV / Math.max(1, aovRupees) * (failureRatePct / 100)));
  const totalInterventionCostPaise = Math.round(totalFailedTransactions * 230); // ₹2.30 per attempt in paise

  const totalMonthlyCostPaise = Math.round(monthlySaaSCost * 100) + totalInterventionCostPaise;
  const netMonthlyRecoveredPaise = Math.max(0, estimatedRecoveredPaise - totalMonthlyCostPaise);
  const annualizedNetBenefitPaise = netMonthlyRecoveredPaise * 12;

  const roiMultiple =
    totalMonthlyCostPaise > 0
      ? (netMonthlyRecoveredPaise / totalMonthlyCostPaise).toFixed(1)
      : "0.0";

  return (
    <div className="space-y-8 pb-20 max-w-7xl mx-auto">
      {/* Title & Header */}
      <div className="p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-gradient-to-br from-[#090e24]/90 via-[#070b1a]/90 to-[#040711]/90 backdrop-blur-2xl shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              Financial Modeling Engine
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Executive ROI & Financial <span className="bg-gradient-to-r from-emerald-400 to-cyan-300 bg-clip-text text-transparent">Impact Calculator</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Simulate monthly revenue uplift, intervention costs, and net return on investment from RazorFlow autonomous recovery.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <span className="text-xs text-slate-400 font-bold mr-1">Presets:</span>
          {presets.map((p) => (
            <button
              key={p.label}
              onClick={() => applyPreset(p)}
              className="px-3 py-1.5 rounded-xl bg-slate-900 border border-white/[0.08] hover:border-blue-500/40 hover:bg-slate-800 text-slate-300 text-xs font-bold transition cursor-pointer shadow-sm"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Calculator Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Interactive Inputs */}
        <div className="lg:col-span-6 space-y-6">
          <div className="p-6 sm:p-7 rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl space-y-6">
            <h2 className="text-base font-black text-white flex items-center gap-2.5 pb-2 border-b border-white/[0.06]">
              <div className="w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-blue-400" />
              </div>
              <span>Merchant Volume Parameters</span>
            </h2>

            {/* Monthly GMV Slider */}
            <div className="space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Monthly Gross Merchandise Value (GMV)</span>
                <span className="font-black text-white font-mono text-sm">
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
                className="w-full h-2.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>₹10 Lakhs</span>
                <span>₹25 Cr</span>
                <span>₹50 Cr</span>
              </div>
            </div>

            {/* Payment Failure Rate Slider */}
            <div className="space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Payment Failure Rate (%)</span>
                <span className="font-black text-amber-400 font-mono text-sm">
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
                className="w-full h-2.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>5% (Best-in-class)</span>
                <span>18% (Industry Average)</span>
                <span>35% (High Dropoff)</span>
              </div>
            </div>

            {/* Average Order Value Slider */}
            <div className="space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Average Order Value (AOV)</span>
                <span className="font-black text-white font-mono text-sm">
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
                className="w-full h-2.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
            </div>

            {/* RazorFlow Projected Recovery Rate */}
            <div className="space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">
                  Projected Recovery Conversion Rate (%)
                </span>
                <span className="font-black text-emerald-400 font-mono text-sm">
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
                className="w-full h-2.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <p className="text-[10px] text-slate-400">
                * Based on RazorFlow historical benchmark: 44.45% base recovery rate on validated ML model dataset.
              </p>
            </div>

            {/* Monthly SaaS & Platform Cost */}
            <div className="space-y-2.5 pt-3 border-t border-white/[0.06]">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Estimated Monthly Platform Cost</span>
                <span className="font-bold text-slate-300 font-mono text-sm">
                  ₹{monthlySaaSCost.toLocaleString("en-IN")}
                </span>
              </div>
              <input
                type="range"
                min="9000"
                max="200000"
                step="5000"
                value={monthlySaaSCost}
                onChange={(e) => setMonthlySaaSCost(Number(e.target.value))}
                className="w-full h-2.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-slate-400"
              />
            </div>
          </div>

          {/* Methodology Card */}
          <div className="p-5 rounded-2xl border border-white/[0.06] bg-slate-950/50 text-xs text-slate-400 space-y-2">
            <div className="flex items-center gap-2 text-slate-200 font-bold">
              <Info className="w-4 h-4 text-blue-400" />
              Calculation Methodology & Precision
            </div>
            <p className="text-[11px] leading-relaxed">
              Calculations use deterministic integer paise math: Gross ERV = ⌊P_ML × Amount⌋. Net recovery subtracts fixed SaaS licensing and per-link dispatch costs (₹2.30 per attempt).
            </p>
          </div>
        </div>

        {/* Right Column: Financial Returns & ROI Dashboard */}
        <div className="lg:col-span-6 space-y-6">
          {/* Primary ROI Hero Box */}
          <div className="p-7 rounded-3xl border border-emerald-500/40 bg-gradient-to-br from-emerald-950/60 via-[#0a1526]/90 to-[#070b1c]/90 backdrop-blur-2xl shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
              <TrendingUp className="w-36 h-36 text-emerald-400" />
            </div>

            <span className="text-xs font-black uppercase tracking-widest text-emerald-400">
              Estimated Monthly Net Revenue Uplift
            </span>
            <div className="text-4xl sm:text-5xl font-black text-white mt-2 mb-3 tracking-tight font-mono">
              {formatINR(netMonthlyRecoveredPaise)}
            </div>
            <p className="text-xs text-emerald-300 font-medium max-w-md leading-relaxed">
              Pure bottom-line profit recovered from transactions that would have otherwise been permanently lost.
            </p>

            <div className="grid grid-cols-2 gap-5 mt-7 pt-6 border-t border-white/[0.08]">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                  Annualized Net Gain
                </span>
                <div className="text-xl font-black text-white font-mono mt-1">
                  {formatINR(annualizedNetBenefitPaise)}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                  Net ROI Multiplier
                </span>
                <div className="text-xl font-black text-emerald-400 font-mono mt-1 flex items-baseline gap-1.5">
                  <span>{roiMultiple}x</span>
                  <span className="text-xs text-emerald-500 font-normal">Return</span>
                </div>
              </div>
            </div>
          </div>

          {/* Breakdown Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 space-y-1.5 shadow-xl">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                Monthly GMV at Risk
              </span>
              <div className="text-lg font-black text-rose-400 font-mono">
                {formatINR(failedGMVPaise)}
              </div>
              <span className="text-[10px] text-slate-400 block font-medium">
                {totalFailedTransactions.toLocaleString("en-IN")} dropped orders/mo
              </span>
            </div>

            <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 space-y-1.5 shadow-xl">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                Gross Recovered GMV
              </span>
              <div className="text-lg font-black text-emerald-400 font-mono">
                {formatINR(estimatedRecoveredPaise)}
              </div>
              <span className="text-[10px] text-slate-400 block font-medium">
                {(totalFailedTransactions * (recoveryRatePct / 100)).toFixed(0)} orders rescued
              </span>
            </div>

            <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 space-y-1.5 shadow-xl">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                Intervention & Link Cost
              </span>
              <div className="text-lg font-black text-slate-300 font-mono">
                {formatINR(totalInterventionCostPaise)}
              </div>
              <span className="text-[10px] text-slate-400 block font-medium">
                ₹2.30 per automated attempt
              </span>
            </div>

            <div className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b1c]/80 space-y-1.5 shadow-xl">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                Total Platform Spend
              </span>
              <div className="text-lg font-black text-slate-300 font-mono">
                {formatINR(totalMonthlyCostPaise)}
              </div>
              <span className="text-[10px] text-slate-400 block font-medium">
                SaaS fee + link fees
              </span>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-white/[0.06] text-[10px] text-slate-400 leading-relaxed flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>
              <strong>Disclaimer:</strong> Projections are based on configured merchant assumptions and historical benchmark scoring models. Actual merchant recovery rates and financial yield may vary depending on customer segment and payment failure distribution.
            </span>
          </div>

          {/* CTA */}
          <div className="p-5 rounded-2xl bg-blue-950/40 border border-blue-500/30 flex items-center justify-between gap-4 shadow-xl">
            <div>
              <h4 className="text-xs font-bold text-white">Experience the Live Recovery Engine</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Run an autonomous payment recovery scenario in under 30 seconds.
              </p>
            </div>
            <Link
              href="/"
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition shrink-0 flex items-center gap-1.5 shadow-lg shadow-blue-500/20"
            >
              <span>Command Center</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
