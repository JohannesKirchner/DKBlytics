import { API_BASE } from "$lib/config";

function buildUrl(path: string): string {
  if (!path.startsWith("/")) {
    return `${API_BASE}/${path}`;
  }
  return `${API_BASE}${path}`;
}

export type FetchFn = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export async function apiFetch<T = unknown>(
  fetchFn: FetchFn,
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = buildUrl(path);
  const response = await fetchFn(url, options);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API request failed: ${response.status} ${response.statusText} - ${detail}`);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}
