'use client';

import { AlertTriangle, GraduationCap, ShieldAlert } from 'lucide-react';

interface DisclaimerBannerProps {
  className?: string;
  compact?: boolean;
}

export function DisclaimerBanner({ className = '', compact = false }: DisclaimerBannerProps) {
  if (compact) {
    return (
      <aside
        role="note"
        aria-label="Educational learning project notice"
        className={`flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3.5 py-2 text-xs text-amber-900 dark:text-amber-200 ${className}`}
      >
        <AlertTriangle aria-hidden className="size-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <p className="leading-tight">
          <strong className="font-semibold">Learning Project Only:</strong> Not medical, health, or dietary advice. Always check the physical package and consult a doctor.
        </p>
      </aside>
    );
  }

  return (
    <aside
      role="alert"
      aria-label="Educational project and medical disclaimer"
      className={`rounded-2xl border-2 border-amber-500/40 bg-gradient-to-r from-amber-500/15 via-amber-500/10 to-orange-500/15 p-4 sm:p-5 shadow-xs transition-all ${className}`}
    >
      <div className="flex items-start gap-3.5">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/20 text-amber-700 dark:text-amber-300 ring-1 ring-amber-500/30">
          <AlertTriangle aria-hidden className="size-5.5 stroke-[2.2]" />
        </div>
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-bold tracking-tight text-amber-950 dark:text-amber-100 uppercase">
              Important: Personal Learning Project
            </h2>
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-600/15 px-2 py-0.5 text-[11px] font-semibold text-amber-800 dark:text-amber-300">
              <GraduationCap className="size-3" />
              Not Health Advice
            </span>
          </div>
          <p className="text-xs leading-relaxed text-amber-900/90 dark:text-amber-200/90 font-medium">
            This chatbot and label analyzer is an <strong>educational learning project</strong>. It does <strong>NOT</strong> provide medical, health, allergy, diagnosis, or dietary advice. Food data is crowd-sourced from Open Food Facts and may be incomplete or inaccurate.
          </p>
          <div className="pt-1 flex items-center gap-1.5 text-[11px] font-semibold text-amber-950 dark:text-amber-200">
            <ShieldAlert className="size-3.5 shrink-0 text-amber-600 dark:text-amber-400" />
            <span>Always consult a qualified doctor or dietitian and verify physical package ingredients before eating.</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
