import { error } from "@sveltejs/kit";
import { apiFetch } from "$lib/api";
import type { PageServerLoad } from "./$types";

function toISODateLocal(date: Date): string {
  const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return d.toISOString().slice(0, 10);
}

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    const accounts = await apiFetch(fetch, "/api/accounts/");

    const today = new Date();
    const start = new Date();
    start.setDate(today.getDate() - 29);
    const dateFrom = toISODateLocal(start);
    const dateTo = toISODateLocal(today);

    const txRes = await apiFetch(
      fetch,
      `/api/transactions/?limit=50&offset=0&date_from=${dateFrom}&date_to=${dateTo}`
    );
    const transactions = Array.isArray(txRes) ? txRes : txRes.items ?? [];
    const total = Array.isArray(txRes) ? txRes.length : txRes.total ?? transactions.length;

    return { accounts, transactions, total };
  } catch (e) {
    const message = e instanceof Error ? e.message : "Failed to load balance data";
    throw error(500, message);
  }
};
