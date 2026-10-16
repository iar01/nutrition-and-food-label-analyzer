'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { Camera } from 'lucide-react';
import { ErrorPanel, Spinner, SlowNotice } from '@/components/states';
import { Button } from '@/components/ui/button';
import { analyzeImage } from '@/lib/api/client';
import { toUiError } from '@/lib/api/errors';
import type { UiError } from '@/lib/api/types';
import { putCached } from '@/lib/cache';
import { resizeImage } from '@/lib/image';
import { profileKey, useProfile } from '@/lib/profile';

export function PhotoUpload() {
  const router = useRouter();
  const profile = useProfile();
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState<UiError | null>(null);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview); // free the memory when the preview changes or we leave
    };
  }, [preview]);

  async function onFile(file: File) {
    setError(null);
    if (!file.type.startsWith('image/')) {
      setError({ code: 'unsupported_media_type', message: 'Please choose an image file.', requestId: null });
      return;
    }
    setBusy(true);
    const timer = window.setTimeout(() => setSlow(true), 8000);
    try {
      const blob = await resizeImage(file); // phones take big photos, our API accepts 4 MB
      setPreview(URL.createObjectURL(blob));
      const result = await analyzeImage(blob, profile);
      putCached(result.product.code, profileKey(profile), result);
      router.push(`/check?barcode=${result.product.code}`);
    } catch (err) {
      if (err instanceof Error && !('info' in err)) {
        setError({ code: 'image', message: err.message, requestId: null }); // e.g. unsupported format
      } else {
        setError(toUiError(err));
      }
      setBusy(false);
    } finally {
      window.clearTimeout(timer);
      setSlow(false);
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Photograph the front of the pack. We find the closest product, which you can confirm on the next screen. The
        photo is shrunk on your device and is not stored.
      </p>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        aria-label="Take or choose a photo of the product"
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = ''; // allow choosing the same file again
          if (file) void onFile(file);
        }}
      />
      <Button onClick={() => inputRef.current?.click()} disabled={busy}>
        <Camera aria-hidden className="size-4" />
        {busy ? 'Analysing…' : 'Take or choose a photo'}
      </Button>
      {preview ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt="Your photo" className="max-h-48 rounded-md border" />
      ) : null}
      {busy ? <Spinner label="Analysing your photo…" /> : null}
      {slow ? <SlowNotice /> : null}
      {error ? <ErrorPanel error={error} /> : null}
    </div>
  );
}
