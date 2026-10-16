import Link from 'next/link';
import { Sparkles, ShieldCheck, HeartPulse, CheckCircle2 } from 'lucide-react';
import { HomeTabs } from '@/components/home-tabs';

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="space-y-3 pt-2 text-center sm:text-left">
        <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
          <Sparkles aria-hidden className="size-3.5" />
          <span>Food Label & Allergen Intelligence</span>
        </div>

        <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
          Is this food right for you?
        </h1>

        <p className="max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
          Scan a barcode, take a photo or search by name. We check ingredients against your specific allergens and diets.{' '}
          <Link
            href="/profile"
            className="font-medium text-primary underline underline-offset-4 decoration-primary/40 transition-colors hover:decoration-primary"
          >
            Set up your profile
          </Link>{' '}
          first for an instant personalised answer.
        </p>
      </section>

      {/* Main Interactive Hub */}
      <HomeTabs />

      {/* Trust & Methodology Features */}
      <section className="grid gap-4 pt-6 sm:grid-cols-3" aria-label="Key features">
        <div className="flex items-start gap-3 rounded-xl border border-border/70 bg-card p-4 shadow-2xs">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 aria-hidden className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Strict Rule Matching</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Direct allergen declaration and ingredient matching with clear certainty levels.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-xl border border-border/70 bg-card p-4 shadow-2xs">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-amber-500/10 text-amber-700 dark:text-amber-400">
            <HeartPulse aria-hidden className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Traffic-Light Nutrition</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              UK guidance ratings for sugars, salt, saturated fat, Nutri-Score, and NOVA processing.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-xl border border-border/70 bg-card p-4 shadow-2xs">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-700 dark:text-blue-400">
            <ShieldCheck aria-hidden className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">100% Private By Design</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Your dietary restrictions stay in your browser. No accounts or tracking.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
