'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Copy } from 'lucide-react';
import { AdditiveList } from '@/components/additive-list';
import { AlternativesList } from '@/components/alternatives-list';
import { EvidenceList } from '@/components/evidence-list';
import { FeedbackButtons } from '@/components/feedback-buttons';
import { IngredientText } from '@/components/ingredient-text';
import { NutritionTable } from '@/components/nutrition-table';
import { OverallBanner } from '@/components/overall-banner';
import { NovaBadge, NutriScoreBadge } from '@/components/score-badges';
import { VerdictChip } from '@/components/verdict-chip';
import { Button } from '@/components/ui/button';
import type { AnalysisResult } from '@/lib/api/types';

function ProductImage({ code }: { code: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div className="flex size-24 shrink-0 items-center justify-center rounded-md border border-dashed text-xs text-muted-foreground">
        No photo
      </div>
    );
  }
  return (
    // A plain <img>: the picture comes from our own API, so Next's image optimiser adds nothing here.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={`/api/v1/products/${code}/image`}
      alt=""
      width={96}
      height={96}
      className="size-24 shrink-0 rounded-md border object-contain"
      onError={() => setFailed(true)}
    />
  );
}

export function AnalysisView({ result, requestId }: { result: AnalysisResult; requestId: string | null }) {
  const { product, verdicts } = result;
  const [copied, setCopied] = useState(false);

  const checks = [
    ...Object.entries(verdicts.allergens ?? {}).map(([id, item]) => ({ kind: 'Allergen', id, item })),
    ...Object.entries(verdicts.diets ?? {}).map(([id, item]) => ({ kind: 'Diet', id, item })),
  ];

  async function copy() {
    await navigator.clipboard.writeText(result.answer_markdown);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <article className="space-y-8">
      <header className="flex gap-4">
        <ProductImage code={product.code} />
        <div className="space-y-2">
          <h1 className="text-2xl font-bold leading-tight">{product.name ?? 'Unnamed product'}</h1>
          <p className="text-muted-foreground">
            {[product.brand, product.quantity].filter(Boolean).join(' · ') || 'Brand unknown'}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <NutriScoreBadge grade={product.nutriscore} />
            <NovaBadge group={product.nova_group} />
          </div>
        </div>
      </header>

      {result.matched_by === 'image' && (result.candidates?.length ?? 0) > 1 ? (
        <section aria-label="Other possible matches" className="rounded-md border p-3 text-sm">
          <p className="font-medium">Matched from your photo. Not the right product?</p>
          <ul className="mt-2 space-y-1">
            {result.candidates!.slice(1).map((c) => (
              <li key={c.code}>
                <Link className="underline" href={`/check?barcode=${c.code}`}>
                  {c.name ?? c.code}
                  {c.brands ? ` (${c.brands})` : ''}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <OverallBanner overall={verdicts.overall} />

      {result.summary ? (
        <section aria-label="Summary">
          <p>{result.summary}</p>
          {(result.tips?.length ?? 0) > 0 ? (
            <ul className="mt-2 list-disc pl-5 text-sm">
              {result.tips?.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {checks.length > 0 ? (
        <section aria-labelledby="profile-h" className="space-y-3">
          <h2 id="profile-h" className="text-xl font-semibold">Your profile</h2>
          <ul className="space-y-3">
            {checks.map(({ kind, id, item }) => (
              <li key={`${kind}-${id}`} className="rounded-md border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium capitalize">
                    {kind}: {id.replace(/_/g, ' ')}
                  </span>
                  <VerdictChip status={item.status} />
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{item.reasons?.join(' ') ?? ''}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section aria-labelledby="nutrition-h" className="space-y-2">
        <h2 id="nutrition-h" className="text-xl font-semibold">Nutrition</h2>
        <NutritionTable product={product} verdicts={verdicts} />
      </section>

      <section aria-labelledby="ingredients-h" className="space-y-2">
        <h2 id="ingredients-h" className="text-xl font-semibold">Ingredients</h2>
        {product.ingredients ? (
          <IngredientText text={product.ingredients} />
        ) : (
          <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
            The ingredient list is missing in the data. Check the pack.
          </p>
        )}
        {result.ingredients?.summary ? <p className="text-sm text-muted-foreground">{result.ingredients.summary}</p> : null}
      </section>

      {result.additives ? (
        <section aria-labelledby="additives-h" className="space-y-2">
          <h2 id="additives-h" className="text-xl font-semibold">Additives</h2>
          <AdditiveList additives={result.additives} />
        </section>
      ) : null}

      {(result.alternatives?.length ?? 0) > 0 ? (
        <section aria-labelledby="alternatives-h" className="space-y-2">
          <h2 id="alternatives-h" className="text-xl font-semibold">Better-scoring alternatives that fit your profile</h2>
          <AlternativesList alternatives={result.alternatives} />
        </section>
      ) : null}

      {(result.evidence?.length ?? 0) > 0 ? (
        <section aria-labelledby="sources-h" className="space-y-2">
          <h2 id="sources-h" className="text-xl font-semibold">Sources</h2>
          <EvidenceList evidence={result.evidence} />
          <a className="text-sm underline" href={product.off_url} target="_blank" rel="noopener noreferrer">
            See this product on Open Food Facts (to check or correct the data)
          </a>
        </section>
      ) : null}

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
        <FeedbackButtons productCode={product.code} threadId={result.thread_id} requestId={requestId} />
        <Button variant="ghost" size="sm" onClick={copy}>
          <Copy aria-hidden className="size-4" /> {copied ? 'Copied' : 'Copy result'}
        </Button>
      </footer>
    </article>
  );
}
