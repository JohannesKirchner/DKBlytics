export async function apiFetch(fetchFn, path, options = {}) {
  // use the fetch given by SvelteKit if available, otherwise the global one
  const f = fetchFn || fetch;

  const res = await f(path, options);
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return res.json();
}