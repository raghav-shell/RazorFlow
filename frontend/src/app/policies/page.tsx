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
      <div className="py-24 text-center text-[#86868b]">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#0071e3] mb-3" />
        <p className="text-sm">Loading Policy Studio...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-28 max-w-7xl mx-auto px-2 sm:px-4">
      {/* Top Header */}
      <section className="pt-4 pb-2 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
            <Shield className="w-3.5 h-3.5 text-[#ffd60a]" />
            <span className="text-xs font-medium text-[#86868b]">
              Policy Engine v{policy?.policy_version || 1} • Immutable Authority
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-[-0.03em] text-white">
            Policy Studio & Guardrails
          </h1>
          <p className="text-sm text-[#86868b] leading-relaxed">
            Configure deterministic financial guardrails. Policy rules are authoritative and strictly govern all AI recommendations.
          </p>
        </div>
      </section>

      {/* Save Success Alert */}
      {saveSuccess && (
        <div className="apple-card p-4 text-xs text-[#30d158] flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{saveSuccess}</span>
        </div>
      )}
      {errorMessage && (
        <div className="apple-card p-4 text-xs text-[#ff453a] flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Policy Configuration Editor */}
        <div className="apple-card p-7 space-y-6">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
            <h2 className="text-sm font-semibold text-white">
              Active Merchant Guardrails
            </h2>
            <span className="text-[10px] text-[#86868b] font-mono px-2 py-0.5 rounded-full bg-white/[0.04]">
              v{policy?.policy_version || 1} Active
            </span>
          </div>

          <form onSubmit={handleSavePolicy} className="space-y-4 text-xs">
            <div className="space-y-1.5">
              <label className="block text-white font-medium">Max Allowed Recovery Attempts</label>
              <input
                type="number"
                min={1}
                max={5}
                value={maxAttempts}
                onChange={(e) => setMaxAttempts(parseInt(e.target.value) || 1)}
                className="apple-input w-full px-3.5 py-2 font-mono text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-white font-medium">Recovery Window Deadline (Hours)</label>
              <input
                type="number"
                min={1}
                max={168}
                value={recoveryWindowHours}
                onChange={(e) => setRecoveryWindowHours(parseInt(e.target.value) || 24)}
                className="apple-input w-full px-3.5 py-2 font-mono text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-white font-medium">Cooldown Period (Minutes)</label>
              <input
                type="number"
                min={0}
                max={1440}
                value={cooldownMinutes}
                onChange={(e) => setCooldownMinutes(parseInt(e.target.value) || 0)}
                className="apple-input w-full px-3.5 py-2 font-mono text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-white font-medium">High-Value Escalation Threshold (₹)</label>
              <input
                type="number"
                min={1000}
                step={1000}
                value={highValueRupees}
                onChange={(e) => setHighValueRupees(parseInt(e.target.value) || 10000)}
                className="apple-input w-full px-3.5 py-2 font-mono text-xs"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 rounded-full bg-white text-black hover:bg-[#e5e5ea] font-semibold text-xs transition cursor-pointer flex items-center justify-center gap-2"
              >
                {saving ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#0071e3]" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                <span>Publish Guardrail Configuration</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Live Policy Impact Simulator */}
        <div className="apple-card p-7 space-y-6">
          <div className="border-b border-white/[0.06] pb-3">
            <h2 className="text-sm font-semibold text-white">Policy Impact Sandbox</h2>
            <p className="text-xs text-[#86868b] mt-0.5">Test candidate actions against guardrails</p>
          </div>

          <div className="space-y-4 text-xs">
            <div className="space-y-1.5">
              <label className="block text-[#86868b]">Candidate Action</label>
              <select
                value={simAction}
                onChange={(e) => setSimAction(e.target.value as any)}
                className="apple-input w-full px-3.5 py-2 font-mono text-xs"
              >
                <option value="PAYMENT_LINK">PAYMENT_LINK (Hosted Checkout)</option>
                <option value="INSTANT_RETRY">INSTANT_RETRY (Transient Retry)</option>
                <option value="WHATSAPP_INTERACTIVE">WHATSAPP_INTERACTIVE</option>
                <option value="HUMAN_ESCALATION">HUMAN_ESCALATION</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-[#86868b]">Simulated Order Amount (₹)</label>
              <input
                type="number"
                value={simAmountRupees}
                onChange={(e) => setSimAmountRupees(Number(e.target.value) || 0)}
                className="apple-input w-full px-3.5 py-2 font-mono text-xs"
              />
            </div>

            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={simulating}
              className="w-full py-2.5 rounded-full bg-white/10 hover:bg-white/20 text-white font-medium text-xs transition cursor-pointer flex items-center justify-center gap-2"
            >
              {simulating ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 text-[#64d2ff]" />
              )}
              <span>Evaluate Policy Impact</span>
            </button>

            {previewResult && (
              <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.08] space-y-3 mt-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#86868b]">Evaluation Verdict</span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${
                      previewResult.policy_verdict === "APPROVED"
                        ? "bg-[#30d158]/10 border-[#30d158]/30 text-[#30d158]"
                        : "bg-[#bf5af2]/10 border-[#bf5af2]/30 text-[#bf5af2]"
                    }`}
                  >
                    {previewResult.policy_verdict}
                  </span>
                </div>

                <div className="text-xs text-[#86868b]">
                  Proposed: <span className="text-white font-mono">{previewResult.candidate_action}</span> → Authorized: <span className="text-white font-mono font-semibold">{previewResult.authorized_action}</span>
                </div>

                {previewResult.was_overridden && (
                  <div className="text-[11px] text-[#ffd60a] flex items-center gap-1.5 font-medium">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    <span>Guardrail enforced: overridden by policy rule.</span>
                  </div>
                )}

                {previewResult.reasoning && (
                  <p className="text-[11px] text-[#86868b] leading-relaxed">
                    {previewResult.reasoning}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
