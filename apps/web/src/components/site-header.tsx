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
    <header className="border-b">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
          <ScanBarcode aria-hidden className="size-5" />
          LabelLens
        </Link>
        <Link href="/profile" className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-muted">
          <UserRound aria-hidden className="size-4" />
          My profile
          {hydrated && count > 0 ? (
            <span className="rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
              <span className="sr-only">{count} selected: </span>
              {count}
            </span>
          ) : null}
        </Link>
      </div>
    </header>
  );
}
