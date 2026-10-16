'use client';

import { useState } from 'react';
import { ThumbsDown, ThumbsUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { sendFeedback } from '@/lib/api/client';

export function FeedbackButtons({
  productCode,
  threadId,
  requestId,
}: {
  productCode: string;
  threadId?: string | null;
  requestId?: string | null;
}) {
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'failed'>('idle');

  async function send(rating: 'up' | 'down') {
    setState('sending');
    try {
      await sendFeedback({
        rating,
        product_code: productCode,
        thread_id: threadId ?? null,
        request_id: requestId ?? null,
      });
      setState('sent');
    } catch {
      setState('failed');
    }
  }

  if (state === 'sent') {
    return (
      <div role="status" className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 dark:border-emerald-800/60 dark:bg-emerald-950/40 dark:text-emerald-300">
        Thanks, your feedback helps us improve.
      </div>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <span className="text-xs font-medium text-muted-foreground">Was this analysis accurate?</span>
      <div className="inline-flex items-center gap-1.5">
        <Button
          variant="outline"
          size="sm"
          disabled={state === 'sending'}
          onClick={() => send('up')}
          className="h-8 rounded-lg px-2.5 text-xs font-medium hover:border-emerald-500/50 hover:bg-emerald-50 hover:text-emerald-800 transition-colors"
        >
          <ThumbsUp aria-hidden className="size-3.5" /> Yes
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={state === 'sending'}
          onClick={() => send('down')}
          className="h-8 rounded-lg px-2.5 text-xs font-medium hover:border-red-500/50 hover:bg-red-50 hover:text-red-800 transition-colors"
        >
          <ThumbsDown aria-hidden className="size-3.5" /> No
        </Button>
      </div>
      {state === 'failed' ? (
        <span role="alert" className="text-xs font-medium text-red-600">
          Could not send. Try again.
        </span>
      ) : null}
    </div>
  );
}
