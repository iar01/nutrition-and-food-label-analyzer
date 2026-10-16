import Link from 'next/link';
import { HomeTabs } from '@/components/home-tabs';

export default function Home() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Is this food right for you?</h1>
        <p className="text-muted-foreground">
          Scan a barcode, take a photo or search by name. We check it against your allergens and diets.{' '}
          <Link href="/profile" className="underline">
            Set up your profile
          </Link>{' '}
          first for a personal answer.
        </p>
      </div>
      <HomeTabs />
    </div>
  );
}
