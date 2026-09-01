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
    { label: "Command Center", href: "/", icon: Activity },
    { label: "Decisions", href: "/decisions", icon: Zap },
    { label: "Policy Studio", href: "/policies", icon: Sliders },
    { label: "Failure Radar", href: "/radar", icon: Radio },
    { label: "ROI Calculator", href: "/calculator", icon: Calculator },
    { label: "Audit Ledger", href: "/audit", icon: FileText },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-white/[0.07] bg-[#040711]/85 backdrop-blur-xl shadow-2xl shadow-black/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative flex items-center justify-center">
                <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400 opacity-70 blur-md group-hover:opacity-100 transition duration-300" />
                <div className="relative w-9 h-9 rounded-xl bg-[#090d20] border border-white/20 flex items-center justify-center shadow-inner">
                  <ShieldCheck className="w-5 h-5 text-blue-400 group-hover:text-cyan-300 transition-colors" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-lg tracking-tight text-white flex items-center gap-1">
                  Razor<span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">Flow</span>
                </span>
                <span className="text-[9px] uppercase font-bold tracking-widest text-slate-400">
                  Institutional Recovery
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <nav className="hidden lg:flex items-center gap-1 p-1 rounded-xl bg-slate-950/60 border border-white/[0.06] backdrop-blur-md">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200",
                      isActive
                        ? "bg-gradient-to-r from-blue-600/30 to-indigo-600/20 text-blue-300 border border-blue-500/40 shadow-sm shadow-blue-500/20"
                        : "text-slate-400 hover:text-slate-100 hover:bg-white/[0.04]"
                    )}
                  >
                    <Icon className={cn("w-3.5 h-3.5", isActive ? "text-blue-400" : "text-slate-500")} />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right Toolbar */}
          <div className="flex items-center gap-3">
            {/* Live System Indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-[11px] font-medium shadow-inner">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="font-mono text-[10px] tracking-wide text-emerald-400 font-bold">TEST MODE</span>
            </div>

            {/* Demo Scenario Modal Trigger Button */}
            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="relative group overflow-hidden flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:via-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-lg shadow-blue-500/25 transition-all duration-200 hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-[0.98] cursor-pointer border border-white/20"
            >
              <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
              <Sparkles className="w-4 h-4 text-cyan-200 animate-spin-slow" />
              <span>Run Recovery Demo</span>
            </button>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div className="lg:hidden px-4 pt-2 pb-4 border-t border-slate-800/80 bg-[#060a19] space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold",
                    isActive
                      ? "bg-blue-600/20 text-blue-300 border border-blue-500/30"
                      : "text-slate-400 hover:text-white hover:bg-slate-900"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                </Link>
              );
            })}
          </div>
        )}
      </header>

      {/* Demo Modal */}
      <DemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </>
  );
}
