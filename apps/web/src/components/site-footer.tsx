export function SiteFooter() {
  return (
    <footer className="border-t bg-muted/40">
      <div className="mx-auto max-w-3xl space-y-2 px-4 py-6 text-sm text-muted-foreground">
        <p>
          <strong className="font-medium text-foreground">General information, not medical advice.</strong>{' '}
          If you have an allergy, always read the pack.
        </p>
        <p>
          Product data and photos come from{' '}
          <a className="underline" href="https://world.openfoodfacts.org" rel="noopener noreferrer" target="_blank">
            Open Food Facts
          </a>{' '}
          contributors (data under ODbL, photos under CC BY-SA). The data is crowd-sourced and can contain mistakes.
        </p>
      </div>
    </footer>
  );
}
