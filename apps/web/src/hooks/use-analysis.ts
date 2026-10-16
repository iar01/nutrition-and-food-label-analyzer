'use client';

import { useCallback, useEffect, useReducer, useRef } from 'react';
import { postChat } from '@/lib/api/client';
import { toUiError } from '@/lib/api/errors';
import { readSse } from '@/lib/api/sse';
import { getCached, putCached } from '@/lib/cache';
import { looksLikeBarcode } from '@/lib/barcode';
import type { AnalysisResult, CandidateOut, ChatRequest, ChooseEvent, FinalEvent, Profile, Step, UiError } from '@/lib/api/types';

export type AnalysisState =
  | { phase: 'idle' }
  | { phase: 'running'; steps: Step[]; slow: boolean }
  | { phase: 'choosing'; steps: Step[]; question: string; candidates: CandidateOut[] }
  | { phase: 'done'; result: AnalysisResult; requestId: string | null }
  | { phase: 'error'; error: UiError };

type Action =
  | { type: 'start' }
  | { type: 'resume' }
  | { type: 'slow' }
  | { type: 'step'; step: Step }
  | { type: 'choose'; event: ChooseEvent }
  | { type: 'final'; result: AnalysisResult; requestId: string | null }
  | { type: 'cached'; result: AnalysisResult }
  | { type: 'failed'; error: UiError };

function reducer(state: AnalysisState, action: Action): AnalysisState {
  switch (action.type) {
    case 'start':
      return { phase: 'running', steps: [], slow: false };
    case 'resume':
      return { phase: 'running', steps: state.phase === 'choosing' ? state.steps : [], slow: false };
    case 'slow':
      return state.phase === 'running' ? { ...state, slow: true } : state;
    case 'step':
      return state.phase === 'running' ? { ...state, steps: [...state.steps, action.step] } : state;
    case 'choose':
      return {
        phase: 'choosing',
        steps: state.phase === 'running' ? state.steps : [],
        question: action.event.question,
        candidates: action.event.candidates,
      };
    case 'final':
      return { phase: 'done', result: action.result, requestId: action.requestId };
    case 'cached':
      return { phase: 'done', result: action.result, requestId: null };
    case 'failed':
      return { phase: 'error', error: action.error };
  }
}

export function useAnalysis(message: string | null, profileJson: string, enabled: boolean) {
  const [state, dispatch] = useReducer(reducer, { phase: 'idle' } as AnalysisState);
  const [attempt, retry] = useReducer((n: number) => n + 1, 0);
  const abortRef = useRef<AbortController | null>(null);
  const threadRef = useRef<string | null>(null);

  const stream = useCallback(
    async (request: ChatRequest, controller: AbortController) => {
      const response = await postChat(request, controller.signal);
      const requestId = response.headers.get('x-request-id');
      let finished = false;

      for await (const { event, data } of readSse(response)) {
        if (event === 'step') {
          dispatch({ type: 'step', step: data as Step });
        } else if (event === 'choose_product') {
          const choose = data as ChooseEvent;
          threadRef.current = choose.thread_id;
          dispatch({ type: 'choose', event: choose });
          finished = true;
        } else if (event === 'final') {
          const result = data as FinalEvent;
          putCached(result.product.code, profileJson, result);
          dispatch({ type: 'final', result, requestId });
          finished = true;
        } else if (event === 'error') {
          const err = data as { error: string; message: string };
          dispatch({ type: 'failed', error: { code: err.error, message: err.message, requestId } });
          finished = true;
        }
      }
      if (!finished) {
        dispatch({
          type: 'failed',
          error: { code: 'stream_ended', message: 'The connection ended before we got an answer. Please retry.', requestId },
        });
      }
    },
    [profileJson],
  );

  useEffect(() => {
    if (!enabled || !message) return;

    if (looksLikeBarcode(message)) {
      const cached = getCached(message, profileJson);
      if (cached) {
        dispatch({ type: 'cached', result: cached });
        return;
      }
    }

    const profile = JSON.parse(profileJson) as Profile;
    const controller = new AbortController();
    abortRef.current = controller;
    dispatch({ type: 'start' });
    const slowTimer = window.setTimeout(() => dispatch({ type: 'slow' }), 8000);

    stream({ message, profile }, controller)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) dispatch({ type: 'failed', error: toUiError(err) });
      })
      .finally(() => window.clearTimeout(slowTimer));

    return () => {
      controller.abort();
      window.clearTimeout(slowTimer);
    };
  }, [enabled, message, profileJson, attempt, stream]);

  const choose = useCallback(
    (code: string) => {
      const threadId = threadRef.current;
      if (!threadId) return;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      dispatch({ type: 'resume' });
      stream({ thread_id: threadId, resume_code: code }, controller).catch((err: unknown) => {
        if (!controller.signal.aborted) dispatch({ type: 'failed', error: toUiError(err) });
      });
    },
    [stream],
  );

  return { state, choose, retry: () => retry() };
}
