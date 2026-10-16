'use client';

import { Sparkles } from 'lucide-react';

interface FollowupChipsProps {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

const DEFAULT_SUGGESTIONS = [
  'Does this contain palm oil?',
  'How much sugar per 100g?',
  'Explain the additives in plain English',
  'What are healthier alternatives?',
  'Is this suitable for children before bed?',
];

export function FollowupChips({ onSelect, disabled = false }: FollowupChipsProps) {
  return (
    <div className="space-y-2 pt-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
        <Sparkles aria-hidden className="size-3.5 text-primary" />
        <span>Suggested Follow-up Questions:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {DEFAULT_SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(suggestion)}
            className="rounded-full border border-border/80 bg-secondary/50 px-3 py-1.5 text-xs font-medium text-foreground transition-all hover:border-primary/50 hover:bg-primary/10 hover:text-primary disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
