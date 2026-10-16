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

  const [dragActive, setDragActive] = useState(false);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void onFile(file);
  }

  return (
    <div className="space-y-5">
      {/* Interactive Drop & Capture Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => !busy && inputRef.current?.click()}
        className={`group relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-all cursor-pointer ${
          dragActive
            ? 'border-primary bg-primary/5 shadow-inner'
            : 'border-border/80 bg-secondary/30 hover:border-primary/50 hover:bg-secondary/60'
        }`}
      >
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

        <div className="flex size-14 items-center justify-center rounded-2xl bg-card text-primary shadow-xs ring-1 ring-border/80 transition-transform group-hover:scale-105">
          <Camera aria-hidden className="size-7" />
        </div>

        <div className="mt-4 space-y-1">
          <p className="text-base font-semibold text-foreground">
            Photograph the packaging front
          </p>
          <p className="max-w-md text-xs text-muted-foreground">
            Snap the front label or drag & drop a photo here. We will match the closest product.
          </p>
        </div>

        <div className="mt-5">
          <Button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              inputRef.current?.click();
            }}
            disabled={busy}
            className="font-semibold shadow-xs"
          >
            <Camera aria-hidden className="size-4" />
            {busy ? 'Analysing…' : 'Take or choose a photo'}
          </Button>
        </div>
      </div>

      <p className="text-center text-xs text-muted-foreground">
        Photos are compressed locally on your device and are not stored.
      </p>

      {preview ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-border/80 bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Captured image preview:</p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview} alt="Your photo" className="max-h-52 rounded-lg border border-border/80 object-contain shadow-xs" />
        </div>
      ) : null}

      {busy ? (
        <div className="flex justify-center p-4">
          <Spinner label="Analysing your photo…" />
        </div>
      ) : null}
      {slow ? <SlowNotice /> : null}
      {error ? <ErrorPanel error={error} /> : null}
    </div>
  );
}
