'use client';

import Link from 'next/link';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface DisclaimerBannerProps {
  className?: string;
  compact?: boolean;
}

export function DisclaimerBanner({ className = '' }: DisclaimerBannerProps) {
  return (
    <aside
      role="note"
      aria-label="Educational learning project notice"
      className={`flex flex-wrap items-center justify-between gap-x-3 gap-y-1 rounded-xl border border-amber-500/35 bg-amber-500/10 px-3.5 py-2 text-xs text-amber-900 dark:text-amber-200 shadow-2xs transition-all ${className}`}
    >
      <div className="flex items-center gap-2 min-w-0">
        <AlertTriangle aria-hidden className="size-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <span className="truncate leading-tight">
          <strong className="font-semibold">Personal Learning Project:</strong> Not medical or health advice. Always check physical packaging.
        </span>
      </div>
      <Link
        href="/disclaimer"
        className="inline-flex shrink-0 items-center gap-1 font-semibold text-amber-800 underline underline-offset-2 hover:text-amber-950 dark:text-amber-300 dark:hover:text-amber-100 transition-colors"
      >
        <span>Full Disclaimer</span>
        <ArrowRight aria-hidden className="size-3" />
      </Link>
    </aside>
  );
}
