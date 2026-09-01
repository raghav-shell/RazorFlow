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
      <body className="min-h-screen flex flex-col bg-[#070a13] text-slate-100 antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="border-t border-slate-800/60 py-6 bg-[#070a13]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-400">RazorFlow Orchestrator</span>
              <span>•</span>
              <span>Razorpay Buildathon Edition</span>
            </div>
            <div className="flex items-center gap-4">
              <span>PostgreSQL Financial Idempotency</span>
              <span>•</span>
              <span>Gemini AI Strategist</span>
              <span>•</span>
              <span>Tamper-Evident SHA-256 Audit</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
