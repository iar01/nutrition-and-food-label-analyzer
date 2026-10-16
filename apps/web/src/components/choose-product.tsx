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
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{question}</DialogTitle>
          <DialogDescription>Pick the one that matches the pack in your hand.</DialogDescription>
        </DialogHeader>
        <ul className="space-y-2">
          {unique.map((c) => (
            <li key={c.code}>
              <button
                type="button"
                className="w-full rounded-md border p-3 text-left hover:bg-muted focus-visible:outline focus-visible:outline-2"
                onClick={() => c.code && onChoose(c.code)}
              >
                <span className="block font-medium">{c.name ?? c.code}</span>
                <span className="block text-sm text-muted-foreground">
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
