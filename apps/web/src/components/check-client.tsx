'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { AnalysisView } from '@/components/analysis-view';
import { ChatThread } from '@/components/chat/chat-thread';
import { DisclaimerBanner } from '@/components/chat/disclaimer-banner';
import { ChooseProduct } from '@/components/choose-product';
import { ProgressSteps } from '@/components/progress-steps';
import { ErrorPanel } from '@/components/states';
import { useAnalysis } from '@/hooks/use-analysis';
import { useHydrated } from '@/hooks/use-hydrated';
import { looksLikeBarcode } from '@/lib/barcode';
import { profileKey, useProfile } from '@/lib/profile';

export function CheckClient() {
  const router = useRouter();
  const params = useSearchParams();
  const hydrated = useHydrated();
  const profile = useProfile();

  const barcode = params.get('barcode');
  const query = params.get('q')?.trim() ?? '';
  const message =
    barcode && looksLikeBarcode(barcode) ? barcode : query.length >= 2 ? query.slice(0, 300) : null;

  // Wait for hydration so we never send the empty server-side profile by mistake.
  const { state, choose, retry } = useAnalysis(message, profileKey(profile), hydrated);

  if (!message) {
    return <ErrorPanel error={{ code: 'no_input', message: 'Enter a barcode or a product name to check.', requestId: null }} />;
  }

  return (
    <div className="space-y-6">
      {/* Prominent Educational Notice */}
      <DisclaimerBanner />

      {state.phase === 'idle' || state.phase === 'running' || state.phase === 'choosing' ? (
        <ProgressSteps
          steps={state.phase === 'idle' ? [] : state.steps}
          slow={state.phase === 'running' && state.slow}
        />
      ) : null}

      {state.phase === 'error' ? <ErrorPanel error={state.error} onRetry={retry} /> : null}

      {state.phase === 'done' ? (
        <>
          <AnalysisView result={state.result} requestId={state.requestId} />
          {state.result.thread_id ? (
            <ChatThread
              threadId={state.result.thread_id}
              profile={profile}
              productName={state.result.product.name ?? 'this product'}
            />
          ) : null}
        </>
      ) : null}

      <ChooseProduct
        open={state.phase === 'choosing'}
        question={state.phase === 'choosing' ? state.question : ''}
        candidates={state.phase === 'choosing' ? state.candidates : []}
        onChoose={choose}
        onCancel={() => router.push('/')}
      />
    </div>
  );
}
