import type { AnalysisResult } from '@/lib/api/types';

const PREFIX = 'labellens.analysis.v1.';
const MAX_AGE_MS = 10 * 60 * 1000;

interface Entry {
  savedAt: number;
  profileKey: string;
  result: AnalysisResult;
}

/** Remember an analysis for this tab only (sessionStorage is cleared when the tab closes). */
export function putCached(code: string, key: string, result: AnalysisResult): void {
  try {
    const entry: Entry = { savedAt: Date.now(), profileKey: key, result };
    window.sessionStorage.setItem(PREFIX + code, JSON.stringify(entry));
  } catch {
    // Storage full or blocked: we just lose the speed-up.
  }
}

export function getCached(code: string, key: string): AnalysisResult | null {
  try {
    const raw = window.sessionStorage.getItem(PREFIX + code);
    if (!raw) return null;
    const entry = JSON.parse(raw) as Entry;
    const fresh = Date.now() - entry.savedAt < MAX_AGE_MS;
    return fresh && entry.profileKey === key ? entry.result : null; // a different profile means a different answer
  } catch {
    return null;
  }
}
