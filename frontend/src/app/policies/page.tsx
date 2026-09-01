"use client";

import React, { useEffect, useState } from "react";
import {
  Sliders,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Play,
  History,
  Save,
  RefreshCw,
  Zap,
  Info,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { PolicyConfig, PolicyPreviewResult, RecoveryActionType } from "@/lib/api/types";
import { formatINR } from "@/lib/utils";

export default function PolicyStudioPage() {
  const [policy, setPolicy] = useState<PolicyConfig | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State
  const [maxAttempts, setMaxAttempts] = useState(2);
  const [recoveryWindowHours, setRecoveryWindowHours] = useState(72);
  const [cooldownMinutes, setCooldownMinutes] = useState(30);
  const [highValueRupees, setHighValueRupees] = useState(50000);
  const [autoRetryTransient, setAutoRetryTransient] = useState(true);

  // Preview Simulator State
  const [simAction, setSimAction] = useState<RecoveryActionType>("PAYMENT_LINK");
  const [simAmountRupees, setSimAmountRupees] = useState(65000);
  const [simCategory, setSimCategory] = useState("INSUFFICIENT_FUNDS");
  const [simRiskScore, setSimRiskScore] = useState(0.15);
  const [previewResult, setPreviewResult] = useState<PolicyPreviewResult | null>(null);
  const [simulating, setSimulating] = useState(false);

  async function loadPolicies() {
    try {
      const data = await apiClient.getPolicies("demo-store");
      setPolicy(data.active_policy);
      setHistory(data.history || []);

      if (data.active_policy) {
        setMaxAttempts(data.active_policy.max_allowed_attempts);
        setRecoveryWindowHours(data.active_policy.recovery_window_hours);
        setCooldownMinutes(data.active_policy.cooldown_period_minutes);
        setHighValueRupees(
          data.active_policy.high_value_escalation_threshold_cents / 100
        );
        setAutoRetryTransient(
          data.active_policy.auto_retry_transient_failures
        );
      }
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to load policy configuration.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPolicies();
  }, []);

  async function handleSavePolicy(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(null);
    setErrorMessage(null);

    try {
      const res = await apiClient.updatePolicies("demo-store", {
        max_allowed_attempts: maxAttempts,
        recovery_window_hours: recoveryWindowHours,
        cooldown_period_minutes: cooldownMinutes,
        high_value_escalation_threshold_cents: highValueRupees * 100,
        auto_retry_transient_failures: autoRetryTransient,
        disallowed_actions: [],
      });

      setSaveSuccess(
        `Policy version ${res.policy_version} published! All future recovery cases will evaluate against these rules.`
      );
      await loadPolicies();
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to update policy.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRunSimulation() {
    setSimulating(true);
    try {
      const res = await apiClient.previewPolicyImpact("demo-store", {
        candidate_action: simAction,
        amount_at_risk_cents: simAmountRupees * 100,
        failure_category: simCategory,
        customer_risk_score: simRiskScore,
      });
      setPreviewResult(res);
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to run simulation preview.");
    } finally {
      setSimulating(false);
    }
  }

  if (loading) {
    return (
      <div className="py-24 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500 mb-3" />
        <p className="text-sm font-semibold text-slate-300">
          Loading Policy Studio...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-20 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="p-6 sm:p-8 rounded-3xl border border-white/[0.08] bg-gradient-to-br from-[#090e24]/90 via-[#070b1a]/90 to-[#040711]/90 backdrop-blur-2xl shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Shield className="w-3.5 h-3.5 text-blue-400" />
              Policy Engine v{policy?.policy_version || 1} • Immutable Authority
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Policy Studio & <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">Financial Guardrails</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Configure deterministic financial guardrails. Policy rules are authoritative and strictly govern AI recommendations.
          </p>
        </div>
      </div>

      {/* Save Success Alert */}
      {saveSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-950/70 border border-emerald-500/40 text-xs text-emerald-200 flex items-center gap-2.5 shadow-lg">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="font-medium">{saveSuccess}</span>
        </div>
      )}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-950/70 border border-rose-500/40 text-xs text-rose-200 flex items-center gap-2.5 shadow-lg">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span className="font-medium">{errorMessage}</span>
        </div>
      )}

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Policy Configuration Editor */}
        <div className="rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl p-6 sm:p-7 space-y-6">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
            <h2 className="text-base font-black text-white flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
                <Shield className="w-4 h-4 text-blue-400" />
              </div>
              <span>Active Merchant Guardrails</span>
            </h2>
            <span className="text-[10px] text-slate-400 font-mono font-bold px-2.5 py-1 rounded-full bg-slate-900 border border-white/[0.06]">
              Immutable Versioning
            </span>
          </div>

          <form onSubmit={handleSavePolicy} className="space-y-4 text-xs">
            {/* Field 1: Max Allowed Attempts */}
            <div className="space-y-1.5">
              <label className="block text-slate-200 font-bold">
                Max Allowed Recovery Attempts
              </label>
              <input
                type="number"
                min={1}
                max={5}
                value={maxAttempts}
                onChange={(e) => setMaxAttempts(parseInt(e.target.value) || 1)}
                className="w-full px-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-white font-mono focus:border-blue-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400">
                Hard limit on physical outreach attempts before marking case UNRECOVERABLE.
              </p>
            </div>

            {/* Field 2: Recovery Deadline Window */}
            <div className="space-y-1.5">
              <label className="block text-slate-200 font-bold">
                Recovery Window Deadline (Hours)
              </label>
              <input
                type="number"
                min={1}
                max={168}
                value={recoveryWindowHours}
                onChange={(e) =>
                  setRecoveryWindowHours(parseInt(e.target.value) || 24)
                }
                className="w-full px-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-white font-mono focus:border-blue-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400">
                Maximum time allowed for customer recovery completion (default 72h).
              </p>
            </div>

            {/* Field 3: Cooldown Window */}
            <div className="space-y-1.5">
              <label className="block text-slate-200 font-bold">
                Cooldown Period (Minutes)
              </label>
              <input
                type="number"
                min={0}
                max={1440}
                value={cooldownMinutes}
                onChange={(e) =>
                  setCooldownMinutes(parseInt(e.target.value) || 0)
                }
                className="w-full px-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-white font-mono focus:border-blue-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400">
                Minimum cooldown between repeated customer contacts to prevent spam.
              </p>
            </div>

            {/* Field 4: High Value Threshold */}
            <div className="space-y-1.5">
              <label className="block text-slate-200 font-bold">
                High-Value Human Escalation Threshold (₹)
              </label>
              <input
                type="number"
                min={1000}
                step={1000}
                value={highValueRupees}
                onChange={(e) =>
                  setHighValueRupees(parseInt(e.target.value) || 10000)
                }
                className="w-full px-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-white font-mono focus:border-blue-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400">
                Transactions at or above this amount trigger HUMAN_ESCALATION override.
              </p>
            </div>

            {/* Field 5: Auto-Retry Transient Toggle */}
            <div className="pt-3 flex items-center justify-between border-t border-white/[0.06]">
              <div>
                <span className="text-slate-200 font-bold block">
                  Auto-Retry Transient Bank Failures
                </span>
                <span className="text-[11px] text-slate-400">
                  Automatically schedule WAIT_AND_REASSESS for 503 bank outages.
                </span>
              </div>
              <input
                type="checkbox"
                checked={autoRetryTransient}
                onChange={(e) => setAutoRetryTransient(e.target.checked)}
                className="w-5 h-5 rounded-lg text-blue-600 bg-slate-950 border-white/[0.08] focus:ring-blue-500 cursor-pointer"
              />
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full mt-4 flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-black text-xs transition shadow-xl shadow-blue-500/25 disabled:opacity-50 cursor-pointer border border-white/15"
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Publish New Policy Version
            </button>
          </form>
        </div>

        {/* Right Column: Policy Impact Preview Simulator */}
        <div className="rounded-3xl border border-white/[0.08] bg-[#070b1c]/80 backdrop-blur-xl shadow-2xl p-6 sm:p-7 space-y-6">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
            <h2 className="text-base font-black text-white flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center">
                <Zap className="w-4 h-4 text-purple-400" />
              </div>
              <span>Policy Impact Sandbox</span>
            </h2>
            <span className="text-[10px] px-2.5 py-1 rounded-full bg-purple-950/80 text-purple-300 border border-purple-500/30 font-bold font-mono">
              Live Evaluation
            </span>
          </div>

          <div className="space-y-4 text-xs">
            <p className="text-slate-400 leading-relaxed">
              Test how the Policy Engine would evaluate a proposed recovery action on a payment with specific characteristics.
            </p>

            <div className="grid grid-cols-2 gap-3.5">
              <div className="space-y-1.5">
                <label className="block text-slate-200 font-bold">
                  Candidate Action
                </label>
                <select
                  value={simAction}
                  onChange={(e) =>
                    setSimAction(e.target.value as RecoveryActionType)
                  }
                  className="w-full px-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-white font-mono focus:border-blue-500 focus:outline-none"
                >
                  <option value="PAYMENT_LINK">PAYMENT_LINK</option>
                  <option value="CUSTOMER_REMINDER">CUSTOMER_REMINDER</option>
                  <option value="WAIT_AND_REASSESS">WAIT_AND_REASSESS</option>
                  <option value="HUMAN_ESCALATION">HUMAN_ESCALATION</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-slate-200 font-bold">
                  Payment Amount (₹)
                </label>
                <input
                  type="number"
                  step={1000}
                  value={simAmountRupees}
                  onChange={(e) =>
                    setSimAmountRupees(parseInt(e.target.value) || 0)
                  }
                  className="w-full px-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-white font-mono focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={simulating}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-black text-xs transition shadow-xl shadow-purple-500/25 disabled:opacity-50 cursor-pointer border border-white/15 mt-2"
            >
              {simulating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Evaluate Policy Guardrails
            </button>

            {/* Simulation Result Output */}
            {previewResult && (
              <div
                className={`p-5 rounded-2xl border space-y-3 mt-4 ${
                  previewResult.was_overridden
                    ? "bg-purple-950/50 border-purple-500/40"
                    : "bg-emerald-950/50 border-emerald-500/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-black uppercase tracking-wider text-slate-300">
                    Policy Engine Output
                  </span>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-bold font-mono ${
                      previewResult.policy_verdict === "APPROVED"
                        ? "bg-emerald-900 text-emerald-300 border border-emerald-500/30"
                        : "bg-purple-900 text-purple-300 border border-purple-500/30"
                    }`}
                  >
                    Verdict: {previewResult.policy_verdict}
                  </span>
                </div>

                <div className="text-xs text-slate-200">
                  Proposed:{" "}
                  <span className="font-bold text-slate-400 font-mono">
                    {previewResult.candidate_action}
                  </span>{" "}
                  $\rightarrow$ Authorized:{" "}
                  <span className="font-black text-white font-mono">
                    {previewResult.authorized_action}
                  </span>
                </div>

                {previewResult.was_overridden && (
                  <div className="text-[11px] text-amber-300 flex items-center gap-1.5 font-bold">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>Guardrail triggered: AI recommendation overridden by deterministic policy.</span>
                  </div>
                )}

                <p className="text-[11px] text-slate-300 leading-relaxed italic">
                  "{previewResult.reasoning}"
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
