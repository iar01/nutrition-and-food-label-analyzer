'use client';

import { useRouter } from 'next/navigation';
import { BarcodeForm } from '@/components/barcode-form';
import { BarcodeScanner } from '@/components/barcode-scanner';
import { PhotoUpload } from '@/components/photo-upload';
import { SearchBox } from '@/components/search-box';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function HomeTabs() {
  const router = useRouter();
  return (
    <Tabs defaultValue="barcode" className="space-y-4">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="barcode">Barcode</TabsTrigger>
        <TabsTrigger value="photo">Photo</TabsTrigger>
        <TabsTrigger value="search">Search</TabsTrigger>
      </TabsList>
      <TabsContent value="barcode" className="space-y-6">
        <BarcodeScanner onDetected={(code) => router.push(`/check?barcode=${code}`)} />
        <BarcodeForm />
      </TabsContent>
      <TabsContent value="photo">
        <PhotoUpload />
      </TabsContent>
      <TabsContent value="search">
        <SearchBox />
      </TabsContent>
    </Tabs>
  );
}
