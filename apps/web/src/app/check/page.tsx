import { Suspense } from 'react';
import { CheckClient } from '@/components/check-client';
import { Spinner } from '@/components/states';

export const metadata = { title: 'Result | LabelLens' };

export default function CheckPage() {
  // useSearchParams() needs a Suspense boundary so the page can still be built ahead of time.
  return (
    <Suspense fallback={<Spinner label="Loading…" />}>
      <CheckClient />
    </Suspense>
  );
}
