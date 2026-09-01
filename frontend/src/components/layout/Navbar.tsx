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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DemoModal } from "../demo/DemoModal";

export function Navbar() {
  const pathname = usePathname();
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

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
      <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-[#070a13]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/25 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
                  Razor<span className="text-blue-400">Flow</span>
                </span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-slate-400">
                  Recovery Orchestrator
                </span>
              </div>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors",
                      isActive
                        ? "bg-blue-600/15 text-blue-400 border border-blue-500/30"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                    )}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right Toolbar */}
          <div className="flex items-center gap-3">
            {/* Razorpay Test Mode Badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-950/60 border border-blue-500/30 text-blue-300 text-[11px] font-semibold">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              Razorpay Test Mode
            </div>

            {/* Demo Scenario Modal Trigger */}
            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-bold shadow-lg shadow-purple-500/20 hover:from-purple-500 hover:to-blue-500 transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Run Recovery Demo</span>
            </button>
          </div>
        </div>
      </header>

      {/* Demo Modal */}
      <DemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </>
  );
}
