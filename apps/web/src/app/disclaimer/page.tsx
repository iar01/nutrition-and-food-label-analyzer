import Link from 'next/link';
import { AlertTriangle, ArrowLeft, GraduationCap, ShieldAlert, HeartPulse, CheckCircle2 } from 'lucide-react';
import { buttonVariants } from '@/components/ui/button';
import { cn } from 'cn';

export const metadata = {
  title: 'Educational Disclaimer | LabelLens',
  description: 'Important legal and health disclaimer for the LabelLens learning project.',
};

export default function DisclaimerPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-8 py-6">
      {/* Header */}
      <div className="space-y-3">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-primary"
        >
          <ArrowLeft className="size-3.5" />
          <span>Back to Home</span>
        </Link>

        <div className="flex items-center gap-2">
          <div className="flex size-10 items-center justify-center rounded-xl bg-amber-500/15 text-amber-700 dark:text-amber-400 ring-1 ring-amber-500/30">
            <AlertTriangle className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">
              Educational Project Disclaimer
            </h1>
            <p className="text-xs text-muted-foreground sm:text-sm">
              Please read this notice carefully before using LabelLens.
            </p>
          </div>
        </div>
      </div>

      {/* Main Notice Box */}
      <section className="rounded-2xl border-2 border-amber-500/40 bg-gradient-to-r from-amber-500/15 via-amber-500/10 to-orange-500/15 p-5 sm:p-6 shadow-xs">
        <div className="flex items-start gap-3.5">
          <GraduationCap className="size-6 shrink-0 text-amber-700 dark:text-amber-400 mt-0.5" />
          <div className="space-y-2">
            <h2 className="text-base font-bold text-amber-950 dark:text-amber-100">
              Personal Learning & Demonstration Project
            </h2>
            <p className="text-xs sm:text-sm leading-relaxed text-amber-900/90 dark:text-amber-200/90">
              LabelLens is an open-source, non-commercial software engineering learning project designed to explore
              modern web development, local AI retrieval, and food label parsing. It is <strong>NOT</strong> an
              authorized medical, healthcare, or regulatory diagnostic system.
            </p>
          </div>
        </div>
      </section>

      {/* Detailed Sections */}
      <div className="space-y-6 text-sm leading-relaxed text-foreground/90">
        <article className="space-y-2.5 rounded-xl border border-border/80 bg-card p-5 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-foreground">
            <HeartPulse className="size-4.5 text-red-500" />
            <h3>1. Not Medical, Clinical, or Health Advice</h3>
          </div>
          <p className="text-xs text-muted-foreground sm:text-sm">
            Nothing provided by LabelLens—including traffic-light nutrition ratings, allergen checks, ingredient
            summaries, additive explanations, or AI chatbot responses—constitutes medical diagnosis, dietary
            treatment, health consultation, or medical advice. Never ignore professional medical advice or delay seeking
            it because of something you have read on this application.
          </p>
        </article>

        <article className="space-y-2.5 rounded-xl border border-border/80 bg-card p-5 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-foreground">
            <ShieldAlert className="size-4.5 text-amber-500" />
            <h3>2. Always Read Physical Product Packaging</h3>
          </div>
          <p className="text-xs text-muted-foreground sm:text-sm">
            Product formulations, manufacturing facilities, allergen cross-contamination warnings, and ingredients
            frequently change without notice. Food database records may be incomplete, outdated, or inaccurate. If you
            have allergies, food intolerances, celiac disease, or specific dietary health requirements, <strong>always
            read the physical packaging label directly</strong> before consuming any product.
          </p>
        </article>

        <article className="space-y-2.5 rounded-xl border border-border/80 bg-card p-5 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-foreground">
            <CheckCircle2 className="size-4.5 text-emerald-500" />
            <h3>3. Crowd-Sourced Data Sources (Open Food Facts)</h3>
          </div>
          <p className="text-xs text-muted-foreground sm:text-sm">
            Product data and nutrition facts are retrieved from the Open Food Facts public database under the Open
            Database License (ODbL). Open Food Facts is a community crowd-sourced platform and neither Open Food Facts
            nor the creators of LabelLens warrant the accuracy, completeness, or reliability of any product listing.
          </p>
        </article>
      </div>

      <div className="pt-2 text-center sm:text-left">
        <Link
          href="/"
          className={cn(buttonVariants({ variant: 'outline', size: 'default' }), 'rounded-xl')}
        >
          <ArrowLeft className="size-4" />
          <span>Return to LabelLens</span>
        </Link>
      </div>
    </div>
  );
}
