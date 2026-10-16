import { toApiError } from './errors';
import type { AnalyzeResponse, ChatRequest, FeedbackIn, Profile } from './types';

export async function postChat(body: ChatRequest, signal: AbortSignal): Promise<Response> {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: { 'content-type': 'application/json', accept: 'text/event-stream' },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) throw await toApiError(response);
  return response;
}

export async function analyzeImage(image: Blob, profile: Profile, signal?: AbortSignal): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append('image', image, 'photo.jpg');
  form.append('profile', JSON.stringify(profile));
  // Do NOT set a content-type header: the browser adds the multipart boundary itself.
  const response = await fetch('/api/v1/analyze', { method: 'POST', body: form, signal });
  if (!response.ok) throw await toApiError(response);
  return (await response.json()) as AnalyzeResponse;
}

export async function sendFeedback(body: FeedbackIn): Promise<void> {
  const response = await fetch('/api/v1/feedback', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw await toApiError(response);
}
