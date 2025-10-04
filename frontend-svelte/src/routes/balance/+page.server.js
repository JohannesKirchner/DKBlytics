// src/routes/balance/+page.server.js
import { error } from '@sveltejs/kit';
import { apiFetch } from '$lib/api.js';

function toISODateLocal(date) {
  const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return d.toISOString().slice(0, 10);
}

export async function load({ fetch }) {
  try {
    // accounts
    const accounts = await apiFetch(fetch, '/api/accounts/');

    // last 30 days (inclusive)
    const today = new Date();
    const start = new Date();
    start.setDate(today.getDate() - 29);
    const date_from = toISODateLocal(start);
    const date_to = toISODateLocal(today);

    // transactions
    const txRes = await apiFetch(
      fetch,
      `/api/transactions/?limit=50&offset=0&date_from=${date_from}&date_to=${date_to}`
    );
    const transactions = Array.isArray(txRes) ? txRes : txRes.items ?? [];
    const total = Array.isArray(txRes) ? txRes.length : txRes.total ?? transactions.length;

    return { accounts, transactions, total };
  } catch (e) {
    throw error(500, e.message || 'Failed to load balance data');
  }
}
