import type { AnalysisOut } from '@/lib/api/types';

export function AdditiveList({ additives }: { additives: NonNullable<AnalysisOut['additives']> }) {
  const notes = additives.notes ?? [];
  const missing = additives.missing ?? [];
  if (notes.length === 0 && missing.length === 0) {
    return (
      <div className="rounded-xl border border-border/80 bg-card p-4 text-sm text-muted-foreground shadow-2xs">
        No additives are listed for this product.
      </div>
    );
  }
  return (
    <ul className="space-y-2.5">
      {notes.map((note) => (
        <li key={note.e_number} className="rounded-xl border border-border/80 bg-card p-4 shadow-2xs">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-md bg-secondary px-2 py-0.5 font-mono text-xs font-bold text-foreground">
              {note.e_number}
            </span>
          </div>
          <p className="mt-1.5 text-xs text-foreground/90 sm:text-sm">{note.explanation}</p>
          {note.relevant_to_user ? (
            <p className="mt-2 rounded-lg border border-amber-200 bg-amber-50/80 p-2 text-xs font-medium text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
              {note.relevant_to_user}
            </p>
          ) : null}
        </li>
      ))}
      {missing.map((code) => (
        <li key={code} className="rounded-xl border border-dashed border-border/80 bg-secondary/30 p-3.5 text-xs text-muted-foreground">
          <span className="font-mono font-bold text-foreground">{code}</span>: we have no explanation for this additive yet.
        </li>
      ))}
    </ul>
  );
}
