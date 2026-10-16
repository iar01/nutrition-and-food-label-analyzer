'use client';

import { useEffect, useRef, useState } from 'react';
import type { IScannerControls } from '@zxing/browser';
import type { DecodeHintType } from '@zxing/library';
import { Camera, CameraOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { isValidGs1 } from '@/lib/barcode';
import { cn } from '@/lib/utils';

type Status = 'idle' | 'starting' | 'scanning' | 'denied' | 'no_camera' | 'insecure' | 'error';

const MESSAGES: Partial<Record<Status, string>> = {
  denied:
    'Camera access was denied. You can allow it in your browser settings for this site, or type the barcode below instead.',
  no_camera: 'No camera was found on this device. Type the barcode below instead.',
  insecure: 'The camera needs a secure (HTTPS) connection. Type the barcode below instead.',
  error: 'The camera could not be started. Type the barcode below instead.',
};

function classify(err: unknown): Status {
  if (err instanceof DOMException) {
    if (err.name === 'NotAllowedError' || err.name === 'SecurityError') return 'denied';
    if (err.name === 'NotFoundError' || err.name === 'OverconstrainedError') return 'no_camera';
  }
  return 'error';
}

export function BarcodeScanner({ onDetected }: { onDetected: (code: string) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const doneRef = useRef(false);
  const [status, setStatus] = useState<Status>('idle');

  function stop() {
    controlsRef.current?.stop(); // turns the camera off
    controlsRef.current = null;
  }

  // Always stop the camera when this component goes away.
  useEffect(() => stop, []);

  async function start() {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setStatus('insecure');
      return;
    }
    setStatus('starting');
    doneRef.current = false;
    try {
      const [{ BrowserMultiFormatReader }, { BarcodeFormat, DecodeHintType }] = await Promise.all([
        import('@zxing/browser'),
        import('@zxing/library'),
      ]);
      const hints = new Map<DecodeHintType, unknown>();
      hints.set(DecodeHintType.POSSIBLE_FORMATS, [
        BarcodeFormat.EAN_13,
        BarcodeFormat.EAN_8,
        BarcodeFormat.UPC_A,
        BarcodeFormat.UPC_E,
      ]);
      const reader = new BrowserMultiFormatReader(hints, { delayBetweenScanAttempts: 150 });

      const controls = await reader.decodeFromConstraints(
        { video: { facingMode: { ideal: 'environment' } } },
        videoRef.current!,
        (result) => {
          if (!result || doneRef.current) return;
          const text = result.getText();
          if (!isValidGs1(text)) return; // ignore misreads
          doneRef.current = true;
          stop();
          setStatus('idle');
          onDetected(text);
        },
      );
      if (doneRef.current) controls.stop(); // a code was read before start() returned
      else controlsRef.current = controls;
      if (!doneRef.current) setStatus('scanning');
    } catch (err) {
      setStatus(classify(err));
    }
  }

  const message = MESSAGES[status];

  return (
    <div className="space-y-4">
      <div className="relative overflow-hidden rounded-xl border border-border/80 bg-slate-950 shadow-inner">
        {/* Video Element for Scanner */}
        <video
          ref={videoRef}
          aria-label="Camera preview for scanning a barcode"
          className={cn(
            'aspect-[4/3] w-full object-cover transition-opacity duration-300',
            status === 'scanning' ? 'opacity-100' : 'opacity-20',
          )}
          playsInline
          muted
        />

        {/* Reticle Overlay Corners when scanning */}
        {status === 'scanning' ? (
          <div aria-hidden className="pointer-events-none absolute inset-6 sm:inset-10 flex flex-col justify-between">
            <div className="flex justify-between">
              <span className="size-6 border-l-3 border-t-3 border-emerald-400 rounded-tl-sm" />
              <span className="size-6 border-r-3 border-t-3 border-emerald-400 rounded-tr-sm" />
            </div>
            {/* Animated Laser Scanning Line */}
            <div className="absolute inset-x-4 h-0.5 animate-scan-laser bg-emerald-400 shadow-[0_0_12px_2px_rgba(52,211,153,0.8)]" />
            <div className="flex justify-between">
              <span className="size-6 border-l-3 border-b-3 border-emerald-400 rounded-bl-sm" />
              <span className="size-6 border-r-3 border-b-3 border-emerald-400 rounded-br-sm" />
            </div>
          </div>
        ) : null}

        {/* Idle / Error / Start State Overlay */}
        {status !== 'scanning' ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
            {status === 'denied' || status === 'no_camera' || status === 'insecure' || status === 'error' ? (
              <div className="flex flex-col items-center gap-3">
                <div className="flex size-14 items-center justify-center rounded-full bg-red-950/80 text-red-400 ring-1 ring-red-500/30">
                  <CameraOff aria-hidden className="size-7" />
                </div>
                <p className="max-w-xs text-xs text-slate-400">
                  Camera unavailable. Use manual barcode entry below.
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="flex size-14 items-center justify-center rounded-2xl bg-white/10 text-emerald-400 ring-1 ring-white/15 backdrop-blur-sm">
                  <Camera aria-hidden className="size-7" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-white">Instant Barcode Scanning</p>
                  <p className="text-xs text-slate-400">Point your device camera at the EAN or UPC on the pack</p>
                </div>
                <Button
                  onClick={start}
                  disabled={status === 'starting'}
                  className="bg-emerald-600 font-semibold text-white shadow-md hover:bg-emerald-500 transition-all"
                >
                  <Camera aria-hidden className="size-4" />
                  {status === 'starting' ? 'Starting camera…' : 'Start camera'}
                </Button>
              </div>
            )}
          </div>
        ) : null}
      </div>

      {status === 'scanning' ? (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-2.5">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
            <p role="status" className="text-sm font-medium text-foreground">
              Point the camera at the barcode.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              stop();
              setStatus('idle');
            }}
            className="h-8 text-xs font-semibold"
          >
            Stop camera
          </Button>
        </div>
      ) : null}

      {message ? (
        <div role="alert" className="rounded-xl border border-dashed border-red-300 bg-red-50/70 p-3.5 text-sm text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          <p>{message}</p>
        </div>
      ) : null}
    </div>
  );
}
