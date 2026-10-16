import { AlertTriangle, CheckCircle2, HelpCircle, Info, XCircle } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

type Status = 'suitable' | 'not_suitable' | 'unknown' | 'contains' | 'may_contain' | 'not_listed';

const STYLES: Record<Status, { label: string; className: string; Icon: LucideIcon }> = {
  suitable: {
    label: 'Suitable',
    className:
      'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800/60 dark:bg-emerald-950/40 dark:text-emerald-300',
    Icon: CheckCircle2,
  },
  not_suitable: {
    label: 'Not suitable',
    className:
      'border-red-200 bg-red-50 text-red-800 dark:border-red-800/60 dark:bg-red-950/40 dark:text-red-300',
    Icon: XCircle,
  },
  contains: {
    label: 'Contains',
    className:
      'border-red-200 bg-red-50 text-red-800 dark:border-red-800/60 dark:bg-red-950/40 dark:text-red-300',
    Icon: AlertTriangle,
  },
  may_contain: {
    label: 'May contain traces',
    className:
      'border-orange-200 bg-orange-50 text-orange-800 dark:border-orange-800/60 dark:bg-orange-950/40 dark:text-orange-300',
    Icon: AlertTriangle,
  },
  unknown: {
    label: 'Unknown: check the pack',
    className:
      'border-dashed border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-300',
    Icon: HelpCircle,
  },
  not_listed: {
    label: 'Not listed in the data',
    className:
      'border-border/80 bg-secondary text-muted-foreground dark:border-border/60 dark:bg-secondary/40',
    Icon: Info,
  },
};

function isStatus(value: string): value is Status {
  return value in STYLES;
}

export function VerdictChip({ status }: { status: string }) {
  const style = isStatus(status) ? STYLES[status] : STYLES.unknown; // unrecognised means unknown
  const { Icon } = style;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold shadow-2xs transition-all',
        style.className,
      )}
    >
      <Icon aria-hidden className="size-3.5 shrink-0" />
      <span>{style.label}</span>
    </span>
  );
}
