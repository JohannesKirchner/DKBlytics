import { API_BASE } from '$lib/config.js';

function buildUrl(path) {
  if (!path.startsWith('/')) {
    return `${API_BASE}/${path}`;
  }
  return `${API_BASE}${path}`;
}

export async function apiFetch(fetchFn, path, options = {}) {
  const url = buildUrl(path);
  const response = await fetchFn(url, options);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API request failed: ${response.status} ${response.statusText} - ${detail}`);
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return await response.json();
  }

  return await response.text();
}
