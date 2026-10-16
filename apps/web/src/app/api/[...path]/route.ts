import type { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

const API_URL = process.env.LABELLENS_API_URL ?? 'http://127.0.0.1:8000';
const API_KEY = process.env.LABELLENS_API_KEY ?? '';

// Only these endpoints may be reached through the proxy.
const ALLOWED: { method: string; pattern: RegExp }[] = [
  { method: 'GET', pattern: /^v1\/products\/\d{8,14}$/ },
  { method: 'GET', pattern: /^v1\/products\/\d{8,14}\/image$/ },
  { method: 'GET', pattern: /^v1\/search$/ },
  { method: 'POST', pattern: /^v1\/analyze$/ },
  { method: 'POST', pattern: /^v1\/chat$/ },
  { method: 'POST', pattern: /^v1\/feedback$/ },
  { method: 'GET', pattern: /^ready$/ },
];

const FORWARD_REQUEST_HEADERS = ['content-type', 'accept', 'x-request-id'];
const FORWARD_RESPONSE_HEADERS = ['content-type', 'cache-control', 'x-request-id', 'retry-after'];

function errorBody(error: string, message: string, status: number): Response {
  return Response.json({ error, message, request_id: '-' }, { status });
}

async function handle(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await params;
  const joined = path.join('/');

  if (!ALLOWED.some((rule) => rule.method === request.method && rule.pattern.test(joined))) {
    return errorBody('not_found', 'Unknown endpoint.', 404);
  }

  const headers = new Headers();
  for (const name of FORWARD_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (API_KEY) headers.set('x-api-key', API_KEY);

  const hasBody = request.method !== 'GET' && request.method !== 'HEAD';

  try {
    const upstream = await fetch(`${API_URL}/${joined}${request.nextUrl.search}`, {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      signal: request.signal,
      cache: 'no-store',
      // Node requires this when the body is a stream.
      duplex: 'half',
    } as RequestInit & { duplex: 'half' });

    const responseHeaders = new Headers();
    for (const name of FORWARD_RESPONSE_HEADERS) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    // Stream the body straight through: do not read it into memory.
    return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return errorBody('upstream_unreachable', 'The analysis service is not reachable right now.', 502);
  }
}

export { handle as GET, handle as POST };
