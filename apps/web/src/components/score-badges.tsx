import { cn } from '@/lib/utils';

const NUTRI_COLORS: Record<string, string> = {
  a: 'bg-[#038141] text-white shadow-xs',
  b: 'bg-[#85bb2f] text-white shadow-xs',
  c: 'bg-[#fecb02] text-slate-950 shadow-xs font-extrabold',
  d: 'bg-[#ee8100] text-white shadow-xs',
  e: 'bg-[#e63e11] text-white shadow-xs',
};

export function NutriScoreBadge({ grade }: { grade?: string | null }) {
  const key = (grade ?? '').toLowerCase();
  const known = key in NUTRI_COLORS;
  return (
    <div
      role="img"
      aria-label={known ? `Nutri-Score ${key.toUpperCase()}` : 'Nutri-Score not available'}
      title="Nutri-Score: A is the best nutritional rating, E the worst"
      className="inline-flex items-center gap-1.5 rounded-lg border border-border/80 bg-card px-2.5 py-1 text-xs font-semibold shadow-2xs"
    >
      <span className="text-muted-foreground">Nutri-Score</span>
      <span
        className={cn(
          'inline-flex size-6 items-center justify-center rounded-md text-xs font-black uppercase tracking-wider',
          known ? NUTRI_COLORS[key] : 'border border-dashed text-muted-foreground bg-secondary',
        )}
      >
        {known ? key.toUpperCase() : '?'}
      </span>
    </div>
  );
}

const NOVA_LABELS: Record<number, string> = {
  1: 'Minimally processed',
  2: 'Culinary ingredient',
  3: 'Processed',
  4: 'Ultra-processed food',
};

const NOVA_COLORS: Record<number, string> = {
  1: 'bg-emerald-600 text-white',
  2: 'bg-lime-600 text-white',
  3: 'bg-amber-600 text-white',
  4: 'bg-red-600 text-white',
};

export function NovaBadge({ group }: { group?: number | null }) {
  const known = group != null && group in NOVA_LABELS;
  return (
    <span
      title="NOVA groups foods by degree of processing, from 1 (unprocessed) to 4 (ultra-processed)"
      className="inline-flex items-center gap-1.5 rounded-lg border border-border/80 bg-card px-2.5 py-1 text-xs shadow-2xs"
    >
      <span
        className={cn(
          'inline-flex size-5 items-center justify-center rounded-full text-[11px] font-bold',
          known ? NOVA_COLORS[group as number] : 'bg-secondary text-muted-foreground',
        )}
      >
        {known ? group : '?'}
      </span>
      <span className="font-semibold text-foreground">NOVA</span>
      <span className="text-muted-foreground">{known ? NOVA_LABELS[group as number] : 'not available'}</span>
    </span>
  );
}
