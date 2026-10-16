import type { components } from './schema';

type S = components['schemas'];

export type AnalysisOut = S['AnalysisOut'];
export type AnalyzeResponse = S['AnalyzeResponse'];
export type ProductSummary = S['ProductSummary'];
export type Verdicts = S['Verdicts'];
export type VerdictItem = S['VerdictItem'];
export type CandidateOut = S['CandidateOut'];
export type SearchResponse = S['SearchResponse'];
export type Profile = S['Profile'];
export type ChatRequest = S['ChatRequest'];
export type FeedbackIn = S['FeedbackIn'];

/** What the UI renders: an analysis, plus extras that only some endpoints return. */
export type AnalysisResult = AnalysisOut &
  Partial<Pick<AnalyzeResponse, 'candidates' | 'matched_by' | 'thread_id' | 'request_id'>>;

// Server-Sent Events are not described by OpenAPI, so these shapes are written by hand.
// Keep them in sync with api/runner.py (chat_events).
export interface Step {
  node: string;
  label: string;
}
export interface ChooseEvent {
  thread_id: string;
  question: string;
  candidates: CandidateOut[];
}
export type FinalEvent = AnalysisOut & { thread_id: string };

export interface UiError {
  code: string;
  message: string;
  requestId: string | null;
  status?: number;
}
