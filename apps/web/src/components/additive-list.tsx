import type { AnalysisOut } from '@/lib/api/types';

export function AdditiveList({ additives }: { additives: NonNullable<AnalysisOut['additives']> }) {
  const notes = additives.notes ?? [];
  const missing = additives.missing ?? [];
  if (notes.length === 0 && missing.length === 0) {
    return <p className="text-sm text-muted-foreground">No additives are listed for this product.</p>;
  }
  return (
    <ul className="space-y-3">
      {notes.map((note) => (
        <li key={note.e_number} className="rounded-md border p-3">
          <p className="font-medium">{note.e_number}</p>
          <p className="text-sm">{note.explanation}</p>
          {note.relevant_to_user ? <p className="mt-1 text-sm font-medium">{note.relevant_to_user}</p> : null}
        </li>
      ))}
      {missing.map((code) => (
        <li key={code} className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{code}</span>: we have no explanation for this additive yet.
        </li>
      ))}
    </ul>
  );
}
