import Link from 'next/link';
import { AlertTriangle, CheckCircle2, HelpCircle, UserRound } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Verdicts } from '@/lib/api/types';

const BANNERS: Record<Verdicts['overall'], { title: string; body: string; className: string; Icon: LucideIcon }> = {
  not_suitable: {
    title: 'Not suitable for your profile',
    body: 'At least one of your allergens or diets conflicts with this product.',
    className: 'border-red-700 bg-red-50 text-red-950',
    Icon: AlertTriangle,
  },
  check: {
    title: 'Needs a check',
    body: 'Some information is missing or uncertain. Read the pack before you decide.',
    className: 'border-dashed border-amber-700 bg-amber-50 text-amber-950',
    Icon: HelpCircle,
  },
  no_conflicts_found: {
    title: 'No conflicts found in the data',
    body: 'This is based on the product data, which can be wrong or out of date. If you have an allergy, still read the pack.',
    className: 'border-green-700 bg-green-50 text-green-950',
    Icon: CheckCircle2,
  },
  no_profile: {
    title: 'No profile set',
    body: 'Add your allergens and diets to get a personal check.',
    className: 'border-slate-400 bg-slate-50 text-slate-900',
    Icon: UserRound,
  },
};

export function OverallBanner({ overall }: { overall: Verdicts['overall'] }) {
  const banner = BANNERS[overall] ?? BANNERS.check; // unknown value: be cautious
  const { Icon } = banner;
  return (
    <section aria-label="Overall result" className={cn('flex gap-3 rounded-lg border-2 p-4', banner.className)}>
      <Icon aria-hidden className="mt-0.5 size-6 shrink-0" />
      <div>
        <h2 className="text-lg font-semibold">{banner.title}</h2>
        <p className="text-sm">{banner.body}</p>
        {overall === 'no_profile' ? (
          <Link href="/profile" className="mt-2 inline-block text-sm font-medium underline">
            Set up my profile
          </Link>
        ) : null}
      </div>
    </section>
  );
}
