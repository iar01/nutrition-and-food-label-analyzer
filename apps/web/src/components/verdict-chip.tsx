import { AlertTriangle, CheckCircle2, HelpCircle, Info, XCircle } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

type Status = 'suitable' | 'not_suitable' | 'unknown' | 'contains' | 'may_contain' | 'not_listed';

const STYLES: Record<Status, { label: string; className: string; Icon: LucideIcon }> = {
  suitable: { label: 'Suitable', className: 'border-green-700 bg-green-50 text-green-950', Icon: CheckCircle2 },
  not_suitable: { label: 'Not suitable', className: 'border-red-700 bg-red-50 text-red-950', Icon: XCircle },
  contains: { label: 'Contains', className: 'border-red-700 bg-red-50 text-red-950', Icon: AlertTriangle },
  may_contain: { label: 'May contain traces', className: 'border-orange-700 bg-orange-50 text-orange-950', Icon: AlertTriangle },
  unknown: {
    label: 'Unknown: check the pack',
    className: 'border-dashed border-amber-700 bg-amber-50 text-amber-950',
    Icon: HelpCircle,
  },
  not_listed: { label: 'Not listed in the data', className: 'border-slate-400 bg-slate-50 text-slate-900', Icon: Info },
};

function isStatus(value: string): value is Status {
  return value in STYLES;
}

export function VerdictChip({ status }: { status: string }) {
  const style = isStatus(status) ? STYLES[status] : STYLES.unknown; // unrecognised means unknown
  const { Icon } = style;
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-md border-2 px-2 py-1 text-sm font-medium', style.className)}>
      <Icon aria-hidden className="size-4 shrink-0" />
      {style.label}
    </span>
  );
}
