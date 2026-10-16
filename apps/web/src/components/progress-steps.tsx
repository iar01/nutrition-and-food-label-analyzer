import { CheckCircle2 } from 'lucide-react';
import { SlowNotice, Spinner } from '@/components/states';
import type { Step } from '@/lib/api/types';

export function ProgressSteps({ steps, slow }: { steps: Step[]; slow: boolean }) {
  return (
    <section aria-label="Progress" className="space-y-4">
      <ol aria-live="polite" className="space-y-2">
        {steps.map((step, index) => (
          <li key={`${step.node}-${index}`} className="flex items-center gap-2 text-sm">
            <CheckCircle2 aria-hidden className="size-4 text-green-700" />
            {step.label}
          </li>
        ))}
      </ol>
      <Spinner label="Working on it…" />
      {slow ? <SlowNotice /> : null}
    </section>
  );
}
