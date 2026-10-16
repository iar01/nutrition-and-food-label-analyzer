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
      <div className="flex size-24 sm:size-28 shrink-0 items-center justify-center rounded-xl border border-dashed border-border/80 bg-secondary/50 text-xs font-medium text-muted-foreground">
        No photo
      </div>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={`/api/v1/products/${code}/image`}
      alt=""
      width={112}
      height={112}
      className="size-24 sm:size-28 shrink-0 rounded-xl border border-border/80 bg-white object-contain p-1 shadow-2xs"
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
    <article className="space-y-6">
      {/* Product Hero Card */}
      <header className="flex flex-col gap-5 rounded-2xl border border-border/80 bg-card p-5 shadow-xs sm:flex-row sm:items-start sm:p-6">
        <ProductImage code={product.code} />
        <div className="min-w-0 flex-1 space-y-2.5">
          <div className="space-y-1">
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl leading-snug">
              {product.name ?? 'Unnamed product'}
            </h1>
            <p className="text-sm font-medium text-muted-foreground">
              {[product.brand, product.quantity].filter(Boolean).join(' · ') || 'Brand unknown'}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <NutriScoreBadge grade={product.nutriscore} />
            <NovaBadge group={product.nova_group} />
            {product.code ? (
              <span className="inline-flex items-center rounded-lg border border-border/80 bg-secondary/50 px-2.5 py-1 font-mono text-xs text-muted-foreground">
                {product.code}
              </span>
            ) : null}
          </div>
        </div>
      </header>

      {result.matched_by === 'image' && (result.candidates?.length ?? 0) > 1 ? (
        <section aria-label="Other possible matches" className="rounded-xl border border-border/80 bg-secondary/30 p-4 text-sm">
          <p className="font-semibold text-foreground">Matched from your photo. Not the right product?</p>
          <ul className="mt-2 space-y-1">
            {result.candidates!.slice(1).map((c) => (
              <li key={c.code}>
                <Link className="font-medium text-primary underline underline-offset-2 hover:opacity-80" href={`/check?barcode=${c.code}`}>
                  {c.name ?? c.code}
                  {c.brands ? ` (${c.brands})` : ''}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {/* Safety Verdict Shield */}
      <OverallBanner overall={verdicts.overall} />

      {/* Executive Summary */}
      {result.summary ? (
        <section aria-label="Summary" className="rounded-2xl border border-border/80 bg-card p-5 shadow-xs sm:p-6">
          <h2 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">Analysis Summary</h2>
          <p className="text-base leading-relaxed text-foreground">{result.summary}</p>
          {(result.tips?.length ?? 0) > 0 ? (
            <ul className="mt-3 space-y-1.5 border-t border-border/60 pt-3 text-sm text-muted-foreground">
              {result.tips?.map((tip) => (
                <li key={tip} className="flex items-start gap-2">
                  <span className="text-primary">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {/* Profile Breakdown */}
      {checks.length > 0 ? (
        <section aria-labelledby="profile-h" className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 id="profile-h" className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
              Your profile
            </h2>
            <Link href="/profile" className="text-xs font-semibold text-primary underline underline-offset-2">
              Edit rules
            </Link>
          </div>
          <ul className="space-y-2.5">
            {checks.map(({ kind, id, item }) => (
              <li key={`${kind}-${id}`} className="rounded-xl border border-border/80 bg-card p-4 shadow-2xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-semibold capitalize text-foreground">
                    {kind}: {id.replace(/_/g, ' ')}
                  </span>
                  <VerdictChip status={item.status} />
                </div>
                {item.reasons && item.reasons.length > 0 ? (
                  <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
                    {item.reasons.join(' ')}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {/* Nutrition Breakdown */}
      <section aria-labelledby="nutrition-h" className="space-y-3">
        <h2 id="nutrition-h" className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
          Nutrition
        </h2>
        <NutritionTable product={product} verdicts={verdicts} />
      </section>

      {/* Ingredients */}
      <section aria-labelledby="ingredients-h" className="space-y-3">
        <h2 id="ingredients-h" className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
          Ingredients
        </h2>
        <div className="rounded-xl border border-border/80 bg-card p-4 sm:p-5 shadow-2xs">
          {product.ingredients ? (
            <IngredientText text={product.ingredients} />
          ) : (
            <p className="rounded-lg border border-dashed border-border p-3 text-sm text-muted-foreground">
              The ingredient list is missing in the data. Check the physical pack.
            </p>
          )}
          {result.ingredients?.summary ? (
            <p className="mt-3 border-t border-border/60 pt-3 text-xs text-muted-foreground leading-relaxed">
              {result.ingredients.summary}
            </p>
          ) : null}
        </div>
      </section>

      {/* Additives */}
      {result.additives ? (
        <section aria-labelledby="additives-h" className="space-y-3">
          <h2 id="additives-h" className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
            Additives
          </h2>
          <AdditiveList additives={result.additives} />
        </section>
      ) : null}

      {/* Better Alternatives */}
      {(result.alternatives?.length ?? 0) > 0 ? (
        <section aria-labelledby="alternatives-h" className="space-y-3">
          <h2 id="alternatives-h" className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
            Better-scoring alternatives that fit your profile
          </h2>
          <AlternativesList alternatives={result.alternatives} />
        </section>
      ) : null}

      {/* Evidence & Sources */}
      {(result.evidence?.length ?? 0) > 0 ? (
        <section aria-labelledby="sources-h" className="space-y-3">
          <h2 id="sources-h" className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
            Sources
          </h2>
          <EvidenceList evidence={result.evidence} />
          {product.off_url ? (
            <a
              className="inline-block text-xs font-medium text-primary underline underline-offset-2 hover:opacity-80"
              href={product.off_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              See this product on Open Food Facts (to check or correct the data) ↗
            </a>
          ) : null}
        </section>
      ) : null}

      {/* Feedback & Actions */}
      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border/80 pt-5">
        <FeedbackButtons productCode={product.code} threadId={result.thread_id} requestId={requestId} />
        <Button variant="outline" size="sm" onClick={copy} className="font-medium text-xs">
          <Copy aria-hidden className="size-3.5" />
          {copied ? 'Copied' : 'Copy result'}
        </Button>
      </footer>
    </article>
  );
}
