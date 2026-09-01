"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, CheckCircle2 } from "lucide-react";
import { soundFX } from "@/lib/audio/soundFX";

interface RecoveryCelebrationProps {
  show: boolean;
  amountFormatted?: string;
  onComplete?: () => void;
}

export function RecoveryCelebration({
  show,
  amountFormatted,
  onComplete,
}: RecoveryCelebrationProps) {
  const [particles, setParticles] = useState<
    Array<{ id: number; x: number; y: number; size: number; color: string; delay: number }>
  >([]);

  useEffect(() => {
    if (show) {
      soundFX.playSuccessChime();

      // Generate 24 luxury glowing micro-particles
      const colors = ["#30d158", "#64d2ff", "#bf5af2", "#ffd60a", "#ffffff"];
      const newParticles = Array.from({ length: 24 }).map((_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 6 + 3,
        color: colors[Math.floor(Math.random() * colors.length)],
        delay: Math.random() * 0.4,
      }));
      setParticles(newParticles);

      const timer = setTimeout(() => {
        if (onComplete) onComplete();
      }, 3500);

      return () => clearTimeout(timer);
    } else {
      setParticles([]);
    }
  }, [show]);

  if (!show) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {/* Particle Canvas */}
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute rounded-full animate-ping"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            backgroundColor: p.color,
            boxShadow: `0 0 12px ${p.color}`,
            animationDuration: "2s",
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}

      {/* Floating Settlement Toast */}
      {amountFormatted && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 pointer-events-auto">
          <div className="apple-card px-5 py-3 rounded-full flex items-center gap-3 shadow-[0_20px_50px_rgba(48,209,88,0.25)] border-[#30d158]/40 animate-bounce">
            <div className="w-6 h-6 rounded-full bg-[#30d158]/20 flex items-center justify-center text-[#30d158]">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div className="text-xs font-semibold text-white">
              Settlement Confirmed:{" "}
              <span className="text-[#30d158] font-mono">{amountFormatted}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
