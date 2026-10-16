import type { UiError } from './types';

export class ApiError extends Error {
  readonly info: UiError;

  constructor(info: UiError) {
    super(info.message);
    this.name = 'ApiError';
    this.info = info;
  }
}

const FRIENDLY: Record<string, string> = {
  unauthorized: 'The app is not configured correctly (API key). Please tell the site owner.',
  rate_limited: 'Too many requests. Please wait a moment and try again.',
  busy: 'The server is busy right now. Please try again in a few seconds.',
  upstream_unreachable: 'The analysis service is not reachable right now. Please try again shortly.',
  file_too_large: 'That image is too large.',
  unsupported_media_type: 'Please use a JPEG, PNG or WebP image.',
  invalid_image: 'That file does not look like a valid image.',
  not_found: 'We could not find that product in our data.',
  no_match: 'We could not match that photo to a product. Try the barcode instead.',
  image_search_disabled: 'Photo search is not available on this server. Try the barcode instead.',
};

export async function toApiError(response: Response): Promise<ApiError> {
  const requestId = response.headers.get('x-request-id');
  let code = `http_${response.status}`;
  let message = 'Something went wrong. Please try again.';
  try {
    const body = (await response.json()) as { error?: string; message?: string; detail?: unknown };
    if (typeof body.error === 'string') {
      code = body.error;
      message = FRIENDLY[code] ?? body.message ?? message;
    } else if (body.detail !== undefined) {
      code = 'invalid_request';
      message = 'Some of the information sent was not valid.'; // FastAPI's default 422 format
    }
  } catch {
    // The body was not JSON: keep the generic message.
  }
  if (response.status === 429) {
    const wait = response.headers.get('retry-after');
    message = wait ? `Too many requests. Please try again in ${wait} seconds.` : FRIENDLY.rate_limited;
  }
  return new ApiError({ code, message, requestId, status: response.status });
}

export function toUiError(err: unknown): UiError {
  if (err instanceof ApiError) return err.info;
  if (err instanceof TypeError) {
    // fetch() throws a TypeError when the network is down.
    return { code: 'network', message: 'No connection. Check your internet and try again.', requestId: null };
  }
  return { code: 'unknown', message: 'Something went wrong. Please try again.', requestId: null };
}
