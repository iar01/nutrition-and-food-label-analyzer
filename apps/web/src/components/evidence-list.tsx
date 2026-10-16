import { ExternalLink } from 'lucide-react';
import type { AnalysisOut } from '@/lib/api/types';

export function EvidenceList({ evidence }: { evidence: AnalysisOut['evidence'] }) {
  const items = evidence ?? [];
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item.id}>
          <details className="group rounded-xl border border-border/80 bg-card p-3.5 shadow-2xs transition-all open:ring-1 open:ring-primary/20">
            <summary className="cursor-pointer text-sm font-semibold text-foreground transition-colors group-hover:text-primary">
              {item.title}
            </summary>
            <div className="mt-2.5 border-t border-border/60 pt-2.5 text-xs leading-relaxed text-muted-foreground sm:text-sm">
              <p>{item.text}</p>
              {item.source_url ? (
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 font-medium text-primary underline underline-offset-2 hover:opacity-80"
                >
                  View source reference <ExternalLink aria-hidden className="size-3" />
                </a>
              ) : null}
            </div>
          </details>
        </li>
      ))}
    </ul>
  );
}
