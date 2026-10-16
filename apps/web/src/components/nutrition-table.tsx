import { cn } from '@/lib/utils';
import type { ProductSummary, Verdicts } from '@/lib/api/types';

const ROWS = [
  { key: 'energy_kcal', label: 'Energy', unit: 'kcal' },
  { key: 'fat_g', label: 'Fat', unit: 'g' },
  { key: 'sat_fat_g', label: 'of which saturates', unit: 'g' },
  { key: 'carbs_g', label: 'Carbohydrate', unit: 'g' },
  { key: 'sugars_g', label: 'of which sugars', unit: 'g' },
  { key: 'protein_g', label: 'Protein', unit: 'g' },
  { key: 'salt_g', label: 'Salt', unit: 'g' },
] as const;

const LEVEL_STYLES: Record<string, string> = {
  low: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/50 dark:text-emerald-300',
  medium: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/50 dark:text-amber-300',
  high: 'border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/50 dark:text-red-300',
  unknown: 'border-border/80 bg-secondary text-muted-foreground',
};

export function NutritionTable({ product, verdicts }: { product: ProductSummary; verdicts: Verdicts }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border/80 bg-card shadow-xs">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">Per 100 g. Levels follow UK traffic-light guidance.</caption>
        <thead className="border-b border-border/70 bg-secondary/40 text-xs font-semibold text-muted-foreground">
          <tr>
            <th scope="col" className="px-4 py-2.5">Nutrient (per 100 g)</th>
            <th scope="col" className="px-4 py-2.5 text-right">Amount</th>
            <th scope="col" className="w-28 px-4 py-2.5 text-right">Guidance</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {ROWS.map((row) => {
            const value = product.nutrition_per_100g?.[row.key];
            const level = verdicts.nutrition[row.key]?.level;
            const isSubItem = row.key === 'sat_fat_g' || row.key === 'sugars_g';
            return (
              <tr key={row.key} className="transition-colors hover:bg-secondary/20">
                <th
                  scope="row"
                  className={cn(
                    'py-2.5 pr-2 font-normal text-foreground',
                    isSubItem ? 'pl-8 text-xs text-muted-foreground' : 'pl-4 text-sm font-medium',
                  )}
                >
                  {row.label}
                </th>
                <td className="px-4 py-2.5 text-right font-mono text-xs tabular-nums text-foreground sm:text-sm">
                  {value == null ? (
                    <span className="text-muted-foreground">n/a</span>
                  ) : (
                    `${Number(value).toFixed(row.unit === 'kcal' ? 0 : 1)} ${row.unit}`
                  )}
                </td>
                <td className="px-4 py-2.5 text-right">
                  {level ? (
                    <span
                      className={cn(
                        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold capitalize',
                        LEVEL_STYLES[level],
                      )}
                    >
                      {level}
                    </span>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="border-t border-border/60 bg-secondary/20 px-4 py-2 text-[11px] text-muted-foreground">
        Nutritional evaluation thresholds follow the UK Department of Health Front-of-Pack Traffic Light guidance.
      </div>
    </div>
  );
}
