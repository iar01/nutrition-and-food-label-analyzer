const E_NUMBER = /\b(E\s?\d{3,4}[a-i]?)\b/gi;

/** Show the ingredient list with E-numbers highlighted. */
export function IngredientText({ text }: { text: string }) {
  // split() with a capture group keeps the matches, which land at odd indexes.
  const parts = text.split(E_NUMBER);
  return (
    <p className="text-sm leading-relaxed text-foreground/90 font-normal">
      {parts.map((part, index) =>
        index % 2 === 1 ? (
          <mark
            key={index}
            className="rounded-md border border-amber-300/80 bg-amber-100 px-1.5 py-0.5 font-mono text-xs font-bold text-amber-950 dark:border-amber-800/60 dark:bg-amber-950/60 dark:text-amber-200"
          >
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        ),
      )}
    </p>
  );
}
