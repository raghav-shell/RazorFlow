import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { AmbientBackground } from "@/components/layout/AmbientBackground";

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
      <body className="min-h-screen flex flex-col bg-black text-white antialiased relative selection:bg-[#0071e3]/30 selection:text-white">
        {/* Luxury Multi-Layered Ambient Background */}
        <AmbientBackground />

        <Navbar />
        
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 z-10">
          {children}
        </main>
        
        <footer className="border-t border-white/[0.06] py-10 bg-black/40 backdrop-blur-2xl relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-[#86868b] gap-4">
            <div className="flex items-center gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#30d158] animate-pulse" />
              <span className="font-medium text-white">RazorFlow 2.0</span>
              <span className="text-[#48484a]">•</span>
              <span className="text-[#86868b]">Autonomous Payment Recovery Orchestrator</span>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-2.5 text-[#86868b] text-[11px] font-mono">
              <span className="px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-white">
                PostgreSQL Idempotency
              </span>
              <span>•</span>
              <span className="px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-[#bf5af2]">
                Gemini 3.6 Flash Advisory
              </span>
              <span>•</span>
              <span className="px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-[#30d158]">
                SHA-256 Merkle Chain
              </span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
