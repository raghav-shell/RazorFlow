"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Activity,
  Zap,
  Sliders,
  Radio,
  Calculator,
  FileText,
  Sparkles,
  CreditCard,
  Volume2,
  VolumeX,
  ArrowRight,
  Command,
  CornerDownLeft,
} from "lucide-react";
import { soundFX } from "@/lib/audio/soundFX";
import { apiClient } from "@/lib/api/client";
import { RecoveryCase } from "@/lib/api/types";
import { formatINR } from "@/lib/utils";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenDemoModal: () => void;
}

export function CommandPalette({
  isOpen,
  onClose,
  onOpenDemoModal,
}: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCases, setRecentCases] = useState<RecoveryCase[]>([]);
  const [isAudioMuted, setIsAudioMuted] = useState(soundFX.isMuted);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      soundFX.playClick();
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);

      apiClient
        .listCases("demo-store", { limit: 5 })
        .then((res) => setRecentCases(res.cases || []))
        .catch(() => {});
    }
  }, [isOpen]);

  const defaultNavigation = [
    {
      id: "nav-cockpit",
      title: "Executive Cockpit",
      description: "Real-time revenue recovery command center",
      icon: Activity,
      action: () => router.push("/"),
      category: "Navigation",
    },
    {
      id: "nav-decisions",
      title: "Decisions Intelligence",
      description: "Inspect AI vs. Policy historical registry",
      icon: Zap,
      action: () => router.push("/decisions"),
      category: "Navigation",
    },
    {
      id: "nav-policies",
      title: "Policy Studio & Guardrails",
      description: "Configure deterministic risk & financial guardrails",
      icon: Sliders,
      action: () => router.push("/policies"),
      category: "Navigation",
    },
    {
      id: "nav-radar",
      title: "Failure Concentration Radar",
      description: "Live failure telemetry and recovery yield",
      icon: Radio,
      action: () => router.push("/radar"),
      category: "Navigation",
    },
    {
      id: "nav-calculator",
      title: "ROI Calculator & Financial Model",
      description: "Interactive recovery yield and GMV modeler",
      icon: Calculator,
      action: () => router.push("/calculator"),
      category: "Navigation",
    },
    {
      id: "nav-audit",
      title: "Cryptographic Audit Ledger",
      description: "Inspect SHA-256 Merkle hash-chained blocks",
      icon: FileText,
      action: () => router.push("/audit"),
      category: "Navigation",
    },
  ];

  const quickActions = [
    {
      id: "act-simulate",
      title: "Simulate Evaluator Recovery Scenario",
      description: "Launch interactive dropoff scenarios",
      icon: Sparkles,
      action: () => {
        onClose();
        onOpenDemoModal();
      },
      category: "Actions",
    },
    {
      id: "act-audio",
      title: isAudioMuted ? "Enable Audio Feedback (Web Audio FX)" : "Mute Audio Feedback",
      description: "Apple-style tactile click & recovery chime synthesizers",
      icon: isAudioMuted ? Volume2 : VolumeX,
      action: () => {
        const muted = soundFX.toggleMute();
        setIsAudioMuted(muted);
      },
      category: "Settings",
    },
  ];

  const caseItems = recentCases.map((c) => ({
    id: `case-${c.id}`,
    title: `Order #${c.order?.external_order_id || c.id.slice(0, 8)}`,
    description: `${c.customer?.name || "Customer"} • ${formatINR(c.amount_at_risk_cents)} • ${c.status}`,
    icon: CreditCard,
    action: () => router.push(`/cases/${c.id}`),
    category: "Recent Cases",
  }));

  const allItems = [...quickActions, ...defaultNavigation, ...caseItems];

  const filteredItems = query
    ? allItems.filter(
        (item) =>
          item.title.toLowerCase().includes(query.toLowerCase()) ||
          item.description.toLowerCase().includes(query.toLowerCase()) ||
          item.category.toLowerCase().includes(query.toLowerCase())
      )
    : allItems;

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      soundFX.playClick();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      soundFX.playClick();
      setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredItems[selectedIndex]) {
        soundFX.playPulse();
        filteredItems[selectedIndex].action();
        onClose();
      }
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/80 backdrop-blur-xl animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl rounded-[28px] border-[0.5px] border-white/20 bg-[#0d0d12]/95 backdrop-blur-3xl shadow-[0_40px_100px_rgba(0,0,0,0.95)] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Header Bar */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/[0.08]">
          <Search className="w-5 h-5 text-[#64d2ff]" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, search case, or jump to page..."
            className="flex-1 bg-transparent text-sm text-white placeholder:text-[#6e6e73] outline-none font-normal"
          />
          <kbd className="px-2 py-1 rounded-md bg-white/[0.06] border border-white/10 text-[10px] font-mono text-[#86868b] flex items-center gap-1">
            <Command className="w-3 h-3" />
            <span>K</span>
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-[380px] overflow-y-auto p-2 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="py-12 text-center text-[#86868b] text-xs">
              No matching commands or cases found for "{query}".
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    soundFX.playPulse();
                    item.action();
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-2xl cursor-pointer transition-all duration-150 ${
                    isSelected
                      ? "bg-white/[0.08] text-white shadow-sm border border-white/10"
                      : "text-[#86868b] hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                        isSelected
                          ? "bg-[#0071e3]/20 text-[#64d2ff] border border-[#0071e3]/40"
                          : "bg-white/[0.04] text-[#86868b]"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-white truncate">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-[#86868b] truncate">
                        {item.description}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[9px] px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-[#86868b] uppercase font-mono">
                      {item.category}
                    </span>
                    {isSelected && (
                      <CornerDownLeft className="w-3.5 h-3.5 text-[#64d2ff]" />
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Navigation Hints */}
        <div className="px-5 py-2.5 bg-black/40 border-t border-white/[0.06] flex items-center justify-between text-[10px] text-[#86868b] font-mono">
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>Esc Close</span>
          </div>
          <span className="text-[#64d2ff]">RazorFlow 2.0 Spotlight</span>
        </div>
      </div>
    </div>
  );
}
