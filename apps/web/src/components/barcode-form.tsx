'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { isValidGs1, looksLikeBarcode } from '@/lib/barcode';

export function BarcodeForm() {
  const router = useRouter();
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | null>(null);

  const samples = [
    { label: '🌰 Hazelnut Spread', code: '3017620422003' },
    { label: '🍫 Alpine Milk Chocolate', code: '7622210449283' },
    { label: '🥤 Classic Soda', code: '5449000000996' },
  ];

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const code = value.replace(/\s+/g, '');
    if (!looksLikeBarcode(code)) {
      setError('A barcode has 8 to 14 digits.');
      return;
    }
    if (!isValidGs1(code)) {
      setError('That number does not look like a valid barcode. Check each digit.');
      return;
    }
    router.push(`/check?barcode=${code}`);
  }

  return (
    <form onSubmit={submit} className="space-y-3.5" noValidate>
      <div className="space-y-1.5">
        <Label htmlFor="barcode-number" className="text-sm font-semibold text-foreground">
          Barcode number
        </Label>
        <p className="text-xs text-muted-foreground">
          Enter the 8, 12, or 13 digits printed beneath the barcode stripes on the packaging.
        </p>
      </div>

      <div className="flex gap-2 sm:gap-3">
        <Input
          id="barcode-number"
          inputMode="numeric"
          autoComplete="off"
          placeholder="e.g. 3017620422003"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setError(null);
          }}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? 'barcode-error' : undefined}
          className="h-11 rounded-lg border-border/80 bg-background text-base shadow-2xs transition-all focus-visible:ring-2 focus-visible:ring-primary"
        />
        <Button
          type="submit"
          className="h-11 px-5 font-semibold shadow-xs transition-all hover:shadow-sm"
        >
          Check
        </Button>
      </div>

      {error ? (
        <div
          id="barcode-error"
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50/80 p-3 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300"
        >
          {error}
        </div>
      ) : null}

      <div className="pt-1">
        <p className="text-xs font-medium text-muted-foreground">Quick test examples:</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {samples.map((s) => (
            <button
              key={s.code}
              type="button"
              onClick={() => {
                setValue(s.code);
                setError(null);
              }}
              className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-secondary/50 px-3 py-1 text-xs font-medium text-foreground/85 transition-colors hover:border-primary/40 hover:bg-secondary hover:text-foreground"
            >
              <span>{s.label}</span>
              <span className="font-mono text-[11px] text-muted-foreground">({s.code})</span>
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
