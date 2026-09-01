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
    <div className="space-y-6 pb-20 max-w-7xl mx-auto">
      {/* Title & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Calculator className="w-6 h-6 text-emerald-400" />
            Executive ROI & Financial Impact Calculator
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Simulate monthly revenue uplift, intervention costs, and net return on investment from RazorFlow autonomous recovery.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-semibold">Quick Presets:</span>
          {presets.map((p) => (
            <button
              key={p.label}
              onClick={() => applyPreset(p)}
              className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Calculator Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Interactive Inputs */}
        <div className="lg:col-span-6 space-y-5">
          <div className="p-6 rounded-2xl border border-slate-800 bg-[#0d1322] shadow-xl space-y-5">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              Merchant Volume Parameters
            </h2>

            {/* Monthly GMV Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-semibold">Monthly Gross Merchandise Value (GMV)</span>
                <span className="font-bold text-white font-mono text-sm">
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
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>₹10 Lakhs</span>
                <span>₹25 Cr</span>
                <span>₹50 Cr</span>
              </div>
            </div>

            {/* Payment Failure Rate Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-semibold">Payment Failure Rate (%)</span>
                <span className="font-bold text-amber-400 font-mono text-sm">
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
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>5% (Best-in-class)</span>
                <span>18% (Industry Average)</span>
                <span>35% (High Dropoff)</span>
              </div>
            </div>

            {/* Average Order Value Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-semibold">Average Order Value (AOV)</span>
                <span className="font-bold text-white font-mono text-sm">
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
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
            </div>

            {/* RazorFlow Projected Recovery Rate */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-semibold">
                  Projected Recovery Conversion Rate (%)
                </span>
                <span className="font-bold text-emerald-400 font-mono text-sm">
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
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <p className="text-[10px] text-slate-400">
                * Based on RazorFlow historical benchmark: 44.45% base recovery rate on validated ML model dataset.
              </p>
            </div>

            {/* Monthly SaaS & Platform Cost */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-semibold">Estimated Monthly Platform Cost</span>
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
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-slate-400"
              />
            </div>
          </div>

          {/* Methodology Card */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 text-xs text-slate-400 space-y-2">
            <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
              <Info className="w-4 h-4 text-blue-400" />
              Calculation Methodology & Transparency
            </div>
            <p className="text-[11px] leading-relaxed">
              Calculations use deterministic integer paise math: Gross ERV = ⌊P_ML × Amount⌋. Net recovery subtracts fixed SaaS licensing and per-link dispatch costs (₹2.30 per attempt).
            </p>
          </div>
        </div>

        {/* Right Column: Financial Returns & ROI Dashboard */}
        <div className="lg:col-span-6 space-y-5">
          {/* Primary ROI Hero Box */}
          <div className="p-6 rounded-2xl border border-emerald-500/40 bg-gradient-to-br from-emerald-950/50 via-[#0d1322] to-[#0d1322] shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-10">
              <TrendingUp className="w-32 h-32 text-emerald-400" />
            </div>

            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
              Estimated Monthly Net Revenue Uplift
            </span>
            <div className="text-4xl font-extrabold text-white mt-1 mb-2 tracking-tight">
              {formatINR(netMonthlyRecoveredPaise)}
            </div>
            <p className="text-xs text-emerald-300/90 font-medium">
              Pure bottom-line profit recovered from transactions that would have otherwise been permanently lost.
            </p>

            <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-800/80">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold">
                  Annualized Net Gain
                </span>
                <div className="text-lg font-bold text-white font-mono mt-0.5">
                  {formatINR(annualizedNetBenefitPaise)}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold">
                  Net ROI Multiple
                </span>
                <div className="text-lg font-extrabold text-emerald-400 font-mono mt-0.5 flex items-baseline gap-1">
                  <span>{roiMultiple}x</span>
                  <span className="text-xs text-emerald-500 font-normal">Return</span>
                </div>
              </div>
            </div>
          </div>

          {/* Breakdown Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322] space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">
                Monthly GMV at Risk
              </span>
              <div className="text-base font-bold text-rose-400 font-mono">
                {formatINR(failedGMVPaise)}
              </div>
              <span className="text-[10px] text-slate-500 block">
                {totalFailedTransactions.toLocaleString("en-IN")} dropped orders/mo
              </span>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322] space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">
                Gross Recovered GMV
              </span>
              <div className="text-base font-bold text-emerald-400 font-mono">
                {formatINR(estimatedRecoveredPaise)}
              </div>
              <span className="text-[10px] text-slate-500 block">
                {(totalFailedTransactions * (recoveryRatePct / 100)).toFixed(0)} orders rescued
              </span>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322] space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">
                Intervention & Link Cost
              </span>
              <div className="text-base font-bold text-slate-300 font-mono">
                {formatINR(totalInterventionCostPaise)}
              </div>
              <span className="text-[10px] text-slate-500 block">
                ₹2.30 per automated attempt
              </span>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-[#0d1322] space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">
                Total Monthly Platform Spend
              </span>
              <div className="text-base font-bold text-slate-300 font-mono">
                {formatINR(totalMonthlyCostPaise)}
              </div>
              <span className="text-[10px] text-slate-500 block">
                SaaS fee + link fees
              </span>
            </div>
          </div>

          {/* Disclaimer (Mandatory) */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-[10px] text-slate-400 leading-relaxed flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>
              <strong>Disclaimer:</strong> Projections are based on configured merchant assumptions and historical benchmark scoring models. Actual merchant recovery rates and financial yield may vary depending on customer segment and payment failure distribution.
            </span>
          </div>

          {/* CTA to run live demo */}
          <div className="p-4 rounded-xl bg-blue-950/40 border border-blue-500/30 flex items-center justify-between gap-4">
            <div>
              <h4 className="text-xs font-bold text-white">Experience the Live Recovery Engine</h4>
              <p className="text-[11px] text-slate-400">
                Run an autonomous payment recovery scenario in under 30 seconds.
              </p>
            </div>
            <Link
              href="/"
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition shrink-0 flex items-center gap-1.5"
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
