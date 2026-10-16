import { ShieldCheck, Info } from 'lucide-react';

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border/80 bg-card/60 backdrop-blur-xs">
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8 text-xs leading-relaxed text-muted-foreground sm:px-6">
        <div className="flex items-start gap-3 rounded-lg border border-border/70 bg-secondary/40 p-3.5 text-foreground/80">
          <Info aria-hidden className="mt-0.5 size-4 shrink-0 text-primary" />
          <p>
            <strong className="font-semibold text-foreground">General information, not medical advice.</strong> If you
            have an allergy, always read the physical pack. Formulations and factory lines change without notice.
          </p>
        </div>

        <div className="flex flex-col items-center justify-between gap-3 text-center sm:flex-row sm:text-left">
          <p>
            Product data and photos come from{' '}
            <a
              className="font-medium text-foreground underline underline-offset-2 transition-colors hover:text-primary"
              href="https://world.openfoodfacts.org"
              rel="noopener noreferrer"
              target="_blank"
            >
              Open Food Facts
            </a>{' '}
            contributors (ODbL / CC BY-SA).
          </p>
          <div className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <ShieldCheck aria-hidden className="size-3.5 text-primary" />
            <span>Zero cloud profile storage</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
