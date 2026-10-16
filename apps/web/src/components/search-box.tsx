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

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const q = value.trim();
    if (q.length >= 2) router.push(`/check?q=${encodeURIComponent(q)}`);
  }

  return (
    <form onSubmit={submit} className="space-y-2" role="search">
      <Label htmlFor="product-search">Product name</Label>
      <div className="flex gap-2">
        <Input
          id="product-search"
          type="search"
          placeholder="e.g. hazelnut spread"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          maxLength={300}
        />
        <Button type="submit" disabled={value.trim().length < 2}>
          <Search aria-hidden className="size-4" /> Search
        </Button>
      </div>
    </form>
  );
}
