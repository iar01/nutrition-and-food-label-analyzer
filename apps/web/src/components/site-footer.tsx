import Link from 'next/link';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border/80 bg-card/60 backdrop-blur-xs">
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8 text-xs leading-relaxed text-muted-foreground sm:px-6">
        <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3.5 py-2 text-xs text-amber-950 dark:text-amber-200">
          <div className="flex items-center gap-2 min-w-0">
            <AlertTriangle aria-hidden className="size-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <span className="truncate">
              <strong className="font-semibold">Personal Learning Project:</strong> Not health or medical advice. Always check physical packaging.
            </span>
          </div>
          <Link
            href="/disclaimer"
            className="shrink-0 font-semibold text-amber-800 underline underline-offset-2 hover:text-amber-950 dark:text-amber-300 dark:hover:text-amber-100 transition-colors"
          >
            Disclaimer &rarr;
          </Link>
        </div>

        <div className="flex flex-col items-center justify-between gap-3 text-center sm:flex-row sm:text-left">
          <p>
            Product data from{' '}
            <a
              className="font-medium text-foreground underline underline-offset-2 transition-colors hover:text-primary"
              href="https://world.openfoodfacts.org"
              rel="noopener noreferrer"
              target="_blank"
            >
              Open Food Facts
            </a>{' '}
            (ODbL). Built for educational demonstration.
          </p>
          <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
            <Link
              href="/disclaimer"
              className="underline underline-offset-2 hover:text-foreground transition-colors"
            >
              Educational Disclaimer
            </Link>
            <div className="inline-flex items-center gap-1.5">
              <ShieldCheck aria-hidden className="size-3.5 text-primary" />
              <span>Zero cloud profile storage</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
