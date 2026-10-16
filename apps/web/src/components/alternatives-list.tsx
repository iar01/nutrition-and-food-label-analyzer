import Link from 'next/link';
import { NutriScoreBadge } from '@/components/score-badges';
import type { AnalysisOut } from '@/lib/api/types';

export function AlternativesList({ alternatives }: { alternatives: AnalysisOut['alternatives'] }) {
  const alts = alternatives ?? [];
  return (
    <ul className="space-y-2">
      {alts.map((alt) => (
        <li key={alt.code}>
          <Link
            href={`/check?barcode=${alt.code}`}
            className="flex items-center gap-3 rounded-md border p-3 hover:bg-muted"
          >
            <NutriScoreBadge grade={alt.nutriscore} />
            <span>
              <span className="block font-medium">{alt.name ?? alt.code}</span>
              <span className="block text-sm text-muted-foreground">{alt.brand}</span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
