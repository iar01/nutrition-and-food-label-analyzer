'use client';

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { CandidateOut } from '@/lib/api/types';

export function ChooseProduct({
  open,
  question,
  candidates,
  onChoose,
  onCancel,
}: {
  open: boolean;
  question: string;
  candidates: CandidateOut[];
  onChoose: (code: string) => void;
  onCancel: () => void;
}) {
  // The API can return the same product more than once: show each barcode once.
  const unique = candidates.filter((c, i) => candidates.findIndex((o) => o.code === c.code) === i);
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onCancel()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold tracking-tight text-foreground">{question}</DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Multiple potential matches were discovered. Select the exact product matching your pack.
          </DialogDescription>
        </DialogHeader>
        <ul className="mt-2 space-y-2 max-h-[60vh] overflow-y-auto pr-1">
          {unique.map((c) => (
            <li key={c.code}>
              <button
                type="button"
                className="group flex w-full flex-col gap-1 rounded-xl border border-border/80 bg-card p-3.5 text-left transition-all hover:border-primary/50 hover:bg-secondary/40 hover:shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onClick={() => c.code && onChoose(c.code)}
              >
                <span className="font-semibold text-foreground group-hover:text-primary transition-colors text-sm sm:text-base">
                  {c.name ?? c.code}
                </span>
                <span className="text-xs text-muted-foreground">
                  {[c.brands, c.code].filter(Boolean).join(' · ')}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
