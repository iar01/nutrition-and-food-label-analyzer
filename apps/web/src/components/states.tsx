import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import type { UiError } from '@/lib/api/types';

export function ErrorPanel({ error, onRetry }: { error: UiError; onRetry?: () => void }) {
  return (
    <Alert variant="destructive" role="alert">
      <AlertCircle aria-hidden className="size-4" />
      <AlertTitle>We could not complete that</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>{error.message}</p>
        {error.requestId ? <p className="text-xs">Reference for support: {error.requestId}</p> : null}
        {onRetry ? (
          <Button variant="outline" size="sm" onClick={onRetry}>
            Try again
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}

export function SlowNotice() {
  return (
    <p role="status" className="rounded-md border border-dashed p-3 text-sm">
      This is taking longer than usual. The server may be waking up, so please keep this page open.
    </p>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm">
      <Loader2 aria-hidden className="size-4 animate-spin motion-reduce:animate-none" />
      {label}
    </span>
  );
}
