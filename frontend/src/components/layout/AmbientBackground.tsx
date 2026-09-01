"use client";

import React, { useEffect, useRef } from "react";

export function AmbientBackground() {
  const spotlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let animationFrameId: number;
    let targetX = window.innerWidth / 2;
    let targetY = 200;
    let currentX = targetX;
    let currentY = targetY;

    const handlePointerMove = (e: PointerEvent) => {
      targetX = e.clientX;
      targetY = e.clientY;
    };

    const updatePosition = () => {
      // Smooth linear interpolation for buttery 60fps tracking
      currentX += (targetX - currentX) * 0.08;
      currentY += (targetY - currentY) * 0.08;

      if (spotlightRef.current) {
        spotlightRef.current.style.transform = `translate3d(${currentX - 300}px, ${currentY - 300}px, 0)`;
      }

      animationFrameId = requestAnimationFrame(updatePosition);
    };

    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    animationFrameId = requestAnimationFrame(updatePosition);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none select-none -z-10 bg-black">
      {/* 1. Primary Top Center Light Beam */}
      <div 
        className="absolute -top-[120px] left-1/2 -translate-x-1/2 w-[1000px] h-[500px] opacity-40 blur-[130px] rounded-full"
        style={{
          background: "radial-gradient(ellipse at center, rgba(0, 113, 227, 0.45) 0%, rgba(120, 40, 200, 0.25) 45%, rgba(0, 0, 0, 0) 75%)",
        }}
      />

      {/* 2. Floating Aurora Mesh Orbs (Animated Breathing Glows) */}
      <div 
        className="absolute top-[20%] -left-[10%] w-[650px] h-[650px] rounded-full opacity-25 blur-[150px] animate-aurora-slow"
        style={{
          background: "radial-gradient(circle, rgba(0, 113, 227, 0.4) 0%, rgba(100, 210, 255, 0.15) 50%, transparent 80%)",
        }}
      />
      <div 
        className="absolute top-[35%] -right-[10%] w-[700px] h-[700px] rounded-full opacity-20 blur-[160px] animate-aurora-reverse"
        style={{
          background: "radial-gradient(circle, rgba(191, 90, 242, 0.35) 0%, rgba(255, 45, 85, 0.1) 50%, transparent 80%)",
        }}
      />
      <div 
        className="absolute bottom-[-10%] left-[20%] w-[600px] h-[600px] rounded-full opacity-20 blur-[140px] animate-aurora-subtle"
        style={{
          background: "radial-gradient(circle, rgba(48, 209, 88, 0.3) 0%, rgba(0, 113, 227, 0.1) 50%, transparent 80%)",
        }}
      />

      {/* 3. Interactive Cursor-Following Ambient Light Spotlight */}
      <div
        ref={spotlightRef}
        className="absolute top-0 left-0 w-[600px] h-[600px] rounded-full pointer-events-none opacity-30 blur-[100px] will-change-transform"
        style={{
          background: "radial-gradient(circle at center, rgba(100, 210, 255, 0.18) 0%, rgba(0, 113, 227, 0.08) 40%, transparent 70%)",
          transform: "translate3d(50vw, 200px, 0)",
        }}
      />

      {/* 4. Precision Micro-Dot Matrix Layer with Radial Mask */}
      <div 
        className="absolute inset-0 opacity-[0.22]"
        style={{
          backgroundImage: "radial-gradient(rgba(255, 255, 255, 0.25) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          maskImage: "radial-gradient(ellipse 80% 65% at 50% 20%, black 25%, transparent 80%)",
          WebkitMaskImage: "radial-gradient(ellipse 80% 65% at 50% 20%, black 25%, transparent 80%)",
        }}
      />

      {/* 5. Architectural Hairline Top Guide Rays */}
      <div 
        className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-6xl h-px opacity-30"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 30%, rgba(100, 210, 255, 0.6) 50%, rgba(255, 255, 255, 0.3) 70%, transparent 100%)",
        }}
      />
      <div 
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] opacity-15"
        style={{
          background: "radial-gradient(ellipse at 50% 0%, rgba(255, 255, 255, 0.5) 0%, transparent 70%)",
        }}
      />

      {/* 6. Subtle Micro-Grain Noise Finish */}
      <div 
        className="absolute inset-0 opacity-[0.025] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
    </div>
  );
}
