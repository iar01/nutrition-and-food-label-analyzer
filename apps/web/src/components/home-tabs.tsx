'use client';

import { useRouter } from 'next/navigation';
import { ScanBarcode, Camera, Search } from 'lucide-react';
import { BarcodeForm } from '@/components/barcode-form';
import { BarcodeScanner } from '@/components/barcode-scanner';
import { PhotoUpload } from '@/components/photo-upload';
import { SearchBox } from '@/components/search-box';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function HomeTabs() {
  const router = useRouter();
  return (
    <Tabs defaultValue="barcode" className="space-y-5">
      <TabsList className="grid h-12 w-full grid-cols-3 rounded-xl border border-border/80 bg-muted/70 p-1.5 shadow-xs">
        <TabsTrigger
          value="barcode"
          className="flex h-full items-center justify-center gap-2 rounded-lg text-xs font-semibold sm:text-sm transition-all"
        >
          <ScanBarcode aria-hidden className="size-4 shrink-0 text-primary" />
          <span>Barcode</span>
        </TabsTrigger>
        <TabsTrigger
          value="photo"
          className="flex h-full items-center justify-center gap-2 rounded-lg text-xs font-semibold sm:text-sm transition-all"
        >
          <Camera aria-hidden className="size-4 shrink-0 text-primary" />
          <span>Photo</span>
        </TabsTrigger>
        <TabsTrigger
          value="search"
          className="flex h-full items-center justify-center gap-2 rounded-lg text-xs font-semibold sm:text-sm transition-all"
        >
          <Search aria-hidden className="size-4 shrink-0 text-primary" />
          <span>Search</span>
        </TabsTrigger>
      </TabsList>

      <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm transition-all sm:p-7">
        <TabsContent value="barcode" className="mt-0 space-y-6">
          <BarcodeScanner onDetected={(code) => router.push(`/check?barcode=${code}`)} />
          <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border/70" />
            </div>
            <span className="relative bg-card px-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Or enter barcode manually
            </span>
          </div>
          <BarcodeForm />
        </TabsContent>

        <TabsContent value="photo" className="mt-0">
          <PhotoUpload />
        </TabsContent>

        <TabsContent value="search" className="mt-0">
          <SearchBox />
        </TabsContent>
      </div>
    </Tabs>
  );
}
