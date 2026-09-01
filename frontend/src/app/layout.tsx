import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RazorFlow | Intelligent Revenue Recovery Orchestrator",
  description:
    "Autonomous revenue recovery layer for Razorpay: AI strategy reasoning, deterministic financial policies, bounded execution, and immutable verification.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} dark`}
    >
      <body className="min-h-screen flex flex-col bg-[#040711] text-slate-100 antialiased relative selection:bg-blue-500/30 selection:text-white">
        {/* Ambient Top Glow Halo */}
        <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[350px] bg-gradient-to-b from-blue-600/10 via-purple-600/5 to-transparent blur-[120px] pointer-events-none -z-10" />
        <div className="fixed top-[40%] right-[-10%] w-[500px] h-[500px] bg-purple-600/5 blur-[140px] pointer-events-none -z-10" />
        <div className="fixed bottom-0 left-[-10%] w-[600px] h-[600px] bg-emerald-600/5 blur-[150px] pointer-events-none -z-10" />

        <Navbar />
        
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 z-10">
          {children}
        </main>
        
        <footer className="border-t border-slate-800/60 py-8 bg-[#040711]/90 backdrop-blur-md relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold text-slate-300">RazorFlow Autonomous Operations</span>
              <span className="text-slate-700">•</span>
              <span className="text-slate-400">Track 3 Edition</span>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3 text-slate-400">
              <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
                PostgreSQL Idempotency
              </span>
              <span>•</span>
              <span className="px-2 py-0.5 rounded bg-purple-950/40 border border-purple-500/30 text-[11px] font-mono text-purple-300">
                Gemini 3.6 Flash Advisory
              </span>
              <span>•</span>
              <span className="px-2 py-0.5 rounded bg-blue-950/40 border border-blue-500/30 text-[11px] font-mono text-blue-300">
                SHA-256 Hash Chain
              </span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
