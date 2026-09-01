"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  ShieldCheck,
  Zap,
  Sliders,
  FileText,
  Sparkles,
  Calculator,
  Radio,
  Menu,
  X,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DemoModal } from "../demo/DemoModal";

export function Navbar() {
  const pathname = usePathname();
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { label: "Cockpit", href: "/", icon: Activity },
    { label: "Decisions", href: "/decisions", icon: Zap },
    { label: "Policy Studio", href: "/policies", icon: Sliders },
    { label: "Telemetry Radar", href: "/radar", icon: Radio },
    { label: "ROI Model", href: "/calculator", icon: Calculator },
    { label: "Audit Ledger", href: "/audit", icon: FileText },
  ];

  return (
    <>
      <div className="sticky top-3 z-50 w-full px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <header className="rounded-full border-[0.5px] border-white/12 bg-black/70 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.85)] px-4 sm:px-5 py-2.5 flex items-center justify-between transition-all duration-300">
          {/* Brand Logo */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="relative w-8 h-8 rounded-full bg-gradient-to-tr from-[#0071e3] to-[#64d2ff] p-[1px] shadow-sm">
                <div className="w-full h-full rounded-full bg-[#08080c] flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4 text-[#64d2ff] group-hover:text-white transition-colors" />
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-sm tracking-tight text-white">
                  Razor<span className="text-[#64d2ff]">Flow</span>
                </span>
                <span className="hidden sm:inline-block text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-white/[0.06] text-[#86868b] border border-white/[0.04]">
                  PRO
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <nav className="hidden lg:flex items-center gap-1 p-1 rounded-full bg-white/[0.03] border border-white/[0.05]">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200",
                      isActive
                        ? "bg-white/10 text-white shadow-sm border border-white/10 font-semibold"
                        : "text-[#86868b] hover:text-white hover:bg-white/[0.04]"
                    )}
                  >
                    <Icon className={cn("w-3.5 h-3.5", isActive ? "text-[#64d2ff]" : "text-[#86868b]")} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right Toolbar */}
          <div className="flex items-center gap-2.5">
            {/* Live Test Mode Jewel */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-[#30d158] text-[10px] font-mono font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-[#30d158] animate-pulse" />
              <span>TEST MODE</span>
            </div>

            {/* Apple-Style Minimalist CTA */}
            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="relative group flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-[#0071e3] to-[#005bb5] hover:from-[#0077ed] hover:to-[#0066cc] text-white text-xs font-semibold shadow-[0_4px_20px_rgba(0,113,227,0.35)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] cursor-pointer border border-white/20"
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-200" />
              <span>Simulate Recovery</span>
            </button>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 rounded-full bg-white/[0.05] border border-white/[0.08] text-white"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </header>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div className="lg:hidden mt-2 p-3 rounded-3xl border border-white/10 bg-black/90 backdrop-blur-2xl shadow-2xl space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium",
                    isActive
                      ? "bg-white/10 text-white font-semibold"
                      : "text-[#86868b] hover:text-white hover:bg-white/[0.04]"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-[#6e6e73]" />
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Interactive Demo Showcase Modal */}
      <DemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </>
  );
}
