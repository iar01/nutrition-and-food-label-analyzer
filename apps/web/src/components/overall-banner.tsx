import Link from 'next/link';
import { AlertTriangle, CheckCircle2, HelpCircle, UserRound } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Verdicts } from '@/lib/api/types';

const BANNERS: Record<
  Verdicts['overall'],
  { title: string; body: string; containerClass: string; iconBoxClass: string; Icon: LucideIcon }
> = {
  not_suitable: {
    title: 'Not suitable for your profile',
    body: 'At least one of your allergens or diets conflicts with this product.',
    containerClass:
      'border-red-200 bg-red-50/90 text-red-950 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-100 shadow-xs',
    iconBoxClass: 'bg-red-600 text-white shadow-xs',
    Icon: AlertTriangle,
  },
  check: {
    title: 'Needs a check',
    body: 'Some information is missing or uncertain in the data. Always read the physical pack before consuming.',
    containerClass:
      'border-dashed border-amber-300 bg-amber-50/90 text-amber-950 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-100 shadow-xs',
    iconBoxClass: 'bg-amber-600 text-white shadow-xs',
    Icon: HelpCircle,
  },
  no_conflicts_found: {
    title: 'No conflicts found in the data',
    body: 'This analysis is based on available Open Food Facts data. If you have a severe allergy, always double-check the packaging.',
    containerClass:
      'border-emerald-200 bg-emerald-50/90 text-emerald-950 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-100 shadow-xs',
    iconBoxClass: 'bg-emerald-600 text-white shadow-xs',
    Icon: CheckCircle2,
  },
  no_profile: {
    title: 'No profile set',
    body: 'Add your allergens and diets to get a personalised safety and suitability verdict.',
    containerClass:
      'border-border/80 bg-secondary/70 text-foreground dark:border-border/60 shadow-xs',
    iconBoxClass: 'bg-muted-foreground/20 text-foreground',
    Icon: UserRound,
  },
};

export function OverallBanner({ overall }: { overall: Verdicts['overall'] }) {
  const banner = BANNERS[overall] ?? BANNERS.check; // unknown value: be cautious
  const { Icon } = banner;
  return (
    <section
      aria-label="Overall result"
      className={cn('flex items-start gap-4 rounded-xl border p-4 sm:p-5 transition-all', banner.containerClass)}
    >
      <div className={cn('flex size-10 shrink-0 items-center justify-center rounded-xl', banner.iconBoxClass)}>
        <Icon aria-hidden className="size-5" />
      </div>
      <div className="space-y-1">
        <h2 className="text-base font-bold tracking-tight sm:text-lg">{banner.title}</h2>
        <p className="text-xs leading-relaxed opacity-90 sm:text-sm">{banner.body}</p>
        {overall === 'no_profile' ? (
          <Link
            href="/profile"
            className="mt-2 inline-flex items-center text-xs font-semibold underline underline-offset-2 hover:opacity-80"
          >
            Set up my profile →
          </Link>
        ) : null}
      </div>
    </section>
  );
}
