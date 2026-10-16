import { CheckCircle2 } from 'lucide-react';
import { SlowNotice, Spinner } from '@/components/states';
import type { Step } from '@/lib/api/types';

export function ProgressSteps({ steps, slow }: { steps: Step[]; slow: boolean }) {
  return (
    <section aria-label="Progress" className="rounded-2xl border border-border/80 bg-card p-6 shadow-xs space-y-5">
      <div className="space-y-1 border-b border-border/60 pb-3">
        <h2 className="text-base font-bold tracking-tight text-foreground">Analyzing Food Label</h2>
        <p className="text-xs text-muted-foreground">Evaluating ingredients against your active dietary profile</p>
      </div>

      <ol aria-live="polite" className="space-y-3">
        {steps.map((step, index) => (
          <li key={`${step.node}-${index}`} className="flex items-center gap-3 text-sm text-foreground">
            <div className="flex size-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              <CheckCircle2 aria-hidden className="size-4" />
            </div>
            <span className="font-medium">{step.label}</span>
          </li>
        ))}
      </ol>

      <div className="pt-2">
        <Spinner label="Analyzing nutritional ingredients…" />
      </div>

      {slow ? <SlowNotice /> : null}
    </section>
  );
}
