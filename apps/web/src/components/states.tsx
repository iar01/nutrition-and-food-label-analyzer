import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import type { UiError } from '@/lib/api/types';

export function ErrorPanel({ error, onRetry }: { error: UiError; onRetry?: () => void }) {
  return (
    <Alert variant="destructive" role="alert" className="rounded-xl border-red-300 bg-red-50/90 text-red-950 shadow-xs dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
      <AlertCircle aria-hidden className="size-4.5 text-red-600 dark:text-red-400" />
      <AlertTitle className="text-base font-bold tracking-tight">We could not complete that</AlertTitle>
      <AlertDescription className="space-y-3 mt-1.5">
        <p className="text-sm leading-relaxed">{error.message}</p>
        {error.requestId ? (
          <p className="font-mono text-xs text-muted-foreground opacity-80">Reference for support: {error.requestId}</p>
        ) : null}
        {onRetry ? (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="border-red-300 bg-card text-foreground hover:bg-secondary font-semibold"
          >
            Try again
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}

export function SlowNotice() {
  return (
    <div
      role="status"
      className="flex items-center gap-3 rounded-xl border border-dashed border-amber-300 bg-amber-50/80 p-3.5 text-xs text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200"
    >
      <span className="size-2 rounded-full bg-amber-500 animate-ping" />
      <p>This is taking longer than usual. The server may be waking up, so please keep this page open.</p>
    </div>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <span
      role="status"
      className="inline-flex items-center gap-2.5 rounded-full border border-border/80 bg-card px-4 py-2 text-xs font-semibold text-foreground shadow-xs"
    >
      <Loader2 aria-hidden className="size-4 animate-spin text-primary motion-reduce:animate-none" />
      <span>{label}</span>
    </span>
  );
}
