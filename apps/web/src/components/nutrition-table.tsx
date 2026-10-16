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
  low: 'bg-green-100 text-green-950',
  medium: 'bg-amber-100 text-amber-950',
  high: 'bg-red-100 text-red-950',
  unknown: 'border border-dashed text-muted-foreground',
};

export function NutritionTable({ product, verdicts }: { product: ProductSummary; verdicts: Verdicts }) {
  return (
    <table className="w-full text-sm">
      <caption className="mb-2 text-left text-sm text-muted-foreground">Per 100 g. Levels follow UK traffic-light guidance.</caption>
      <tbody>
        {ROWS.map((row) => {
          const value = product.nutrition_per_100g?.[row.key];
          const level = verdicts.nutrition[row.key]?.level;
          return (
            <tr key={row.key} className="border-b last:border-0">
              <th scope="row" className="py-2 pr-2 text-left font-normal">
                {row.label}
              </th>
              <td className="py-2 text-right tabular-nums">
                {value == null ? 'n/a' : `${Number(value).toFixed(row.unit === 'kcal' ? 0 : 1)} ${row.unit}`}
              </td>
              <td className="w-24 py-2 pl-2 text-right">
                {level ? (
                  <span className={cn('rounded px-2 py-0.5 text-xs font-medium capitalize', LEVEL_STYLES[level])}>
                    {level}
                  </span>
                ) : null}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
