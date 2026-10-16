import { cn } from '@/lib/utils';

const NUTRI_COLORS: Record<string, string> = {
  a: 'bg-green-700 text-white',
  b: 'bg-lime-600 text-white',
  c: 'bg-yellow-400 text-black',
  d: 'bg-orange-500 text-white',
  e: 'bg-red-600 text-white',
};

export function NutriScoreBadge({ grade }: { grade?: string | null }) {
  const key = (grade ?? '').toLowerCase();
  const known = key in NUTRI_COLORS;
  return (
    <span
      role="img"
      aria-label={known ? `Nutri-Score ${key.toUpperCase()}` : 'Nutri-Score not available'}
      title="Nutri-Score: A is the best nutritional rating, E the worst"
      className={cn(
        'inline-flex size-9 items-center justify-center rounded-md text-lg font-bold',
        known ? NUTRI_COLORS[key] : 'border-2 border-dashed text-muted-foreground',
      )}
    >
      {known ? key.toUpperCase() : '?'}
    </span>
  );
}

const NOVA_LABELS: Record<number, string> = {
  1: 'Unprocessed or minimally processed',
  2: 'Processed culinary ingredient',
  3: 'Processed food',
  4: 'Ultra-processed food',
};

export function NovaBadge({ group }: { group?: number | null }) {
  const known = group != null && group in NOVA_LABELS;
  return (
    <span
      title="NOVA groups foods by how processed they are, from 1 to 4"
      className="inline-flex items-center gap-2 rounded-md border px-2 py-1 text-sm"
    >
      <span className="font-bold">NOVA {known ? group : '?'}</span>
      <span className="text-muted-foreground">{known ? NOVA_LABELS[group as number] : 'not available'}</span>
    </span>
  );
}
