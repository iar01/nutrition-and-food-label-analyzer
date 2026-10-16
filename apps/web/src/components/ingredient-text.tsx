const E_NUMBER = /\b(E\s?\d{3,4}[a-i]?)\b/gi;

/** Show the ingredient list with E-numbers highlighted. */
export function IngredientText({ text }: { text: string }) {
  // split() with a capture group keeps the matches, which land at odd indexes.
  const parts = text.split(E_NUMBER);
  return (
    <p className="text-sm leading-relaxed">
      {parts.map((part, index) =>
        index % 2 === 1 ? (
          <mark key={index} className="rounded bg-amber-200 px-1 text-amber-950">
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        ),
      )}
    </p>
  );
}
