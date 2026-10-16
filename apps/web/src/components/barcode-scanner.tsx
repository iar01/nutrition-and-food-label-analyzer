'use client';

import { useEffect, useRef, useState } from 'react';
import type { IScannerControls } from '@zxing/browser';
import type { DecodeHintType } from '@zxing/library';
import { Camera, CameraOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { isValidGs1 } from '@/lib/barcode';

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
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-lg bg-black">
        <video
          ref={videoRef}
          aria-label="Camera preview for scanning a barcode"
          className="aspect-[4/3] w-full object-cover"
          playsInline
          muted
        />
        {status === 'scanning' ? (
          <div aria-hidden className="pointer-events-none absolute inset-x-8 top-1/2 h-0.5 -translate-y-1/2 bg-red-500/80" />
        ) : null}
        {status !== 'scanning' ? (
          <div className="absolute inset-0 flex items-center justify-center p-4">
            {status === 'denied' || status === 'no_camera' || status === 'insecure' || status === 'error' ? (
              <CameraOff aria-hidden className="size-10 text-white/70" />
            ) : (
              <Button onClick={start} disabled={status === 'starting'}>
                <Camera aria-hidden className="size-4" />
                {status === 'starting' ? 'Starting camera…' : 'Start camera'}
              </Button>
            )}
          </div>
        ) : null}
      </div>

      {status === 'scanning' ? (
        <div className="flex items-center justify-between gap-3">
          <p role="status" className="text-sm">Point the camera at the barcode.</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              stop();
              setStatus('idle');
            }}
          >
            Stop camera
          </Button>
        </div>
      ) : null}
      {message ? <p role="alert" className="rounded-md border border-dashed p-3 text-sm">{message}</p> : null}
    </div>
  );
}
