import Link from 'next/link';
import { NutriScoreBadge } from '@/components/score-badges';
import type { AnalysisOut } from '@/lib/api/types';

import { ArrowUpRight } from 'lucide-react';

export function AlternativesList({ alternatives }: { alternatives: AnalysisOut['alternatives'] }) {
  const alts = alternatives ?? [];
  return (
    <ul className="grid gap-2.5 sm:grid-cols-2">
      {alts.map((alt) => (
        <li key={alt.code}>
          <Link
            href={`/check?barcode=${alt.code}`}
            className="group flex items-center justify-between gap-3 rounded-xl border border-border/80 bg-card p-3.5 shadow-2xs transition-all hover:border-primary/40 hover:bg-secondary/40 hover:shadow-xs"
          >
            <div className="flex items-center gap-3 min-w-0">
              <NutriScoreBadge grade={alt.nutriscore} />
              <div className="min-w-0">
                <span className="block truncate text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {alt.name ?? alt.code}
                </span>
                <span className="block truncate text-xs text-muted-foreground">{alt.brand}</span>
              </div>
            </div>
            <ArrowUpRight aria-hidden className="size-4 shrink-0 text-muted-foreground opacity-50 transition-all group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-primary" />
          </Link>
        </li>
      ))}
    </ul>
  );
}
