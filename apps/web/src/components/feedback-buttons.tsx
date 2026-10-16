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

  if (state === 'sent') return <p role="status" className="text-sm">Thanks, your feedback helps us improve.</p>;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm">Was this helpful?</span>
      <Button variant="outline" size="sm" disabled={state === 'sending'} onClick={() => send('up')}>
        <ThumbsUp aria-hidden className="size-4" /> Yes
      </Button>
      <Button variant="outline" size="sm" disabled={state === 'sending'} onClick={() => send('down')}>
        <ThumbsDown aria-hidden className="size-4" /> No
      </Button>
      {state === 'failed' ? <span role="alert" className="text-sm text-red-700">Could not send. Try again.</span> : null}
    </div>
  );
}
