'use client';

import React from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface MarkdownTextProps {
  content: string;
  className?: string;
}

function renderInline(text: string): React.ReactNode {
  // Regex to split on **bold**, *italic*, and `code`
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return (
        <strong key={index} className="font-bold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length >= 2) {
      return (
        <em key={index} className="italic text-foreground">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return (
        <code key={index} className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-primary font-medium">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export function MarkdownText({ content, className = '' }: MarkdownTextProps) {
  if (!content) return null;

  // Separate any educational disclaimer lines from the main answer text
  const rawLines = content.split('\n');
  const mainLines: string[] = [];
  let hasNotice = false;

  for (const line of rawLines) {
    const trimmed = line.trim();
    const lower = trimmed.toLowerCase();
    if (
      lower.includes('educational & learning project') ||
      lower.includes('learning project notice') ||
      lower.includes('personal learning project') ||
      lower.includes('not health advice') ||
      lower.includes('not provide medical') ||
      lower.includes('always consult a qualified doctor') ||
      trimmed.startsWith('> ⚠️') ||
      trimmed.startsWith('⚠️') ||
      (trimmed.startsWith('>') && lower.includes('health advice'))
    ) {
      hasNotice = true;
    } else {
      mainLines.push(line);
    }
  }

  const mainText = mainLines.join('\n').trim();
  const paragraphs = mainText.split(/\n\s*\n/).filter(Boolean);

  return (
    <div className={`space-y-2.5 text-xs sm:text-sm leading-relaxed ${className}`}>
      {paragraphs.map((para, pIdx) => {
        const lines = para.split('\n').map((l) => l.trim());

        // Check if paragraph is a bulleted list
        const isList = lines.every((l) => l.startsWith('- ') || l.startsWith('* '));
        if (isList) {
          return (
            <ul key={pIdx} className="list-disc space-y-1.5 pl-4 text-foreground/90">
              {lines.map((l, lIdx) => (
                <li key={lIdx}>{renderInline(l.replace(/^[-*]\s+/, ''))}</li>
              ))}
            </ul>
          );
        }

        // Standard paragraph
        return (
          <p key={pIdx} className="text-foreground/90">
            {renderInline(para)}
          </p>
        );
      })}

      {hasNotice && (
        <aside
          role="note"
          aria-label="Educational Notice"
          className="mt-3 flex flex-wrap items-center justify-between gap-x-2.5 gap-y-1 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-[11px] text-amber-900 dark:text-amber-200"
        >
          <div className="flex items-center gap-1.5 min-w-0">
            <AlertTriangle className="size-3.5 shrink-0 text-amber-600 dark:text-amber-400" />
            <span className="truncate">
              <strong>Personal Learning Project:</strong> Not health advice. Check packaging.
            </span>
          </div>
          <Link
            href="/disclaimer"
            className="inline-flex shrink-0 items-center gap-1 font-semibold text-amber-800 underline underline-offset-2 hover:text-amber-950 dark:text-amber-300 dark:hover:text-amber-100 transition-colors"
          >
            <span>Full Disclaimer</span>
            <ArrowRight className="size-3" />
          </Link>
        </aside>
      )}
    </div>
  );
}
