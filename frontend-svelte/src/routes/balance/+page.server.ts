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

    let items: unknown[] = [];
    let total = 0;

    if (Array.isArray(txRes)) {
      items = txRes;
      total = txRes.length;
    } else if (txRes && typeof txRes === "object") {
      const data = txRes as { items?: unknown[]; total?: number };
      if (Array.isArray(data.items)) {
        items = data.items;
      }
      total = typeof data.total === "number" ? data.total : items.length;
    }

    return { accounts, items, total };
  } catch (e) {
    const message = e instanceof Error ? e.message : "Failed to load balance data";
    throw error(500, message);
  }
};
