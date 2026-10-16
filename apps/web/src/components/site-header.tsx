'use client';

import Link from 'next/link';
import { ScanBarcode, UserRound } from 'lucide-react';
import { useHydrated } from '@/hooks/use-hydrated';
import { useProfile } from '@/lib/profile';

export function SiteHeader() {
  const profile = useProfile();
  const hydrated = useHydrated();
  const count = (profile.diets?.length ?? 0) + (profile.allergens?.length ?? 0);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/70 bg-background/80 backdrop-blur-md transition-colors">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3 sm:px-6">
        <Link
          href="/"
          className="group flex items-center gap-2.5 rounded-lg text-base font-semibold tracking-tight transition-opacity hover:opacity-90"
          aria-label="LabelLens Home"
        >
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs transition-transform group-hover:scale-105">
            <ScanBarcode aria-hidden className="size-4.5" />
          </div>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Label<span className="text-primary">Lens</span>
          </span>
        </Link>

        <Link
          href="/profile"
          className="group inline-flex items-center gap-2 rounded-full border border-border/80 bg-card/90 px-3.5 py-1.5 text-sm font-medium text-foreground shadow-xs transition-all hover:border-primary/40 hover:bg-secondary/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <UserRound aria-hidden className="size-3.5 text-muted-foreground transition-colors group-hover:text-primary" />
          <span>My profile</span>
          {hydrated && count > 0 ? (
            <span className="inline-flex size-5 items-center justify-center rounded-full bg-primary text-[11px] font-bold text-primary-foreground">
              <span className="sr-only">{count} selected: </span>
              {count}
            </span>
          ) : (
            <span className="hidden text-xs text-muted-foreground sm:inline">Set rules</span>
          )}
        </Link>
      </div>
    </header>
  );
}
