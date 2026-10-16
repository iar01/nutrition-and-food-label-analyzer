'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export function SearchBox() {
  const router = useRouter();
  const [value, setValue] = useState('');

  const suggestions = ['hazelnut spread', 'oat milk', 'granola', 'dark chocolate', 'hummus'];

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const q = value.trim();
    if (q.length >= 2) router.push(`/check?q=${encodeURIComponent(q)}`);
  }

  return (
    <form onSubmit={submit} className="space-y-4" role="search">
      <div className="space-y-1.5">
        <Label htmlFor="product-search" className="text-sm font-semibold text-foreground">
          Product name
        </Label>
        <p className="text-xs text-muted-foreground">
          Search over 3 million products in Open Food Facts by brand or product name.
        </p>
      </div>

      <div className="flex gap-2 sm:gap-3">
        <Input
          id="product-search"
          type="search"
          placeholder="e.g. hazelnut spread"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          maxLength={300}
          className="h-11 rounded-lg border-border/80 bg-background text-base shadow-2xs transition-all focus-visible:ring-2 focus-visible:ring-primary"
        />
        <Button
          type="submit"
          disabled={value.trim().length < 2}
          className="h-11 px-5 font-semibold shadow-xs transition-all"
        >
          <Search aria-hidden className="size-4" /> Search
        </Button>
      </div>

      <div className="pt-1">
        <p className="text-xs font-medium text-muted-foreground">Popular product searches:</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {suggestions.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setValue(item);
                router.push(`/check?q=${encodeURIComponent(item)}`);
              }}
              className="inline-flex items-center gap-1 rounded-full border border-border/80 bg-secondary/50 px-3 py-1 text-xs font-medium text-foreground/85 transition-colors hover:border-primary/40 hover:bg-secondary hover:text-foreground"
            >
              <Search aria-hidden className="size-3 text-muted-foreground" />
              <span>{item}</span>
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
