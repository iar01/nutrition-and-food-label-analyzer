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
    <form onSubmit={submit} className="space-y-2" noValidate>
      <Label htmlFor="barcode-number">Barcode number</Label>
      <div className="flex gap-2">
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
        />
        <Button type="submit">Check</Button>
      </div>
      {error ? (
        <p id="barcode-error" role="alert" className="text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </form>
  );
}
