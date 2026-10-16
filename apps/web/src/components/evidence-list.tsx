import { ExternalLink } from 'lucide-react';
import type { AnalysisOut } from '@/lib/api/types';

export function EvidenceList({ evidence }: { evidence: AnalysisOut['evidence'] }) {
  const items = evidence ?? [];
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item.id}>
          <details className="rounded-md border p-3">
            <summary className="cursor-pointer font-medium">{item.title}</summary>
            <p className="mt-2 text-sm">{item.text}</p>
            {item.source_url ? (
              <a
                href={item.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-sm underline"
              >
                Source <ExternalLink aria-hidden className="size-3" />
              </a>
            ) : null}
          </details>
        </li>
      ))}
    </ul>
  );
}
