import { error } from "@sveltejs/kit";
import { apiFetch } from "$lib/api";
import type { Account } from '$lib/types/accounts';
import type { Transaction } from '$lib/types/transactions';
import type { PageServerLoad } from "./$types";

function toISODateLocal(date: Date): string {
  const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return d.toISOString().slice(0, 10);
}

function todayISO(): string {
  return toISODateLocal(new Date());
}

function isoNDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return toISODateLocal(d);
}

type Filters = {
  account: string;
  from: string;
  to: string;
  q: string;
  limit: number;
  offset: number;
  view: 'uncategorized';
};

type LoadData = {
  accounts: Account[];
  items: Transaction[];
  total: number;
  filters: Filters;
};

export const load: PageServerLoad = async ({ url }) => {
  try {
    const account = url.searchParams.get('account') ?? 'all';
    const from    = url.searchParams.get('from')    ?? isoNDaysAgo(29);
    const to      = url.searchParams.get('to')      ?? todayISO();
    const q       = url.searchParams.get('q')       ?? '';
    const limit   = Number(url.searchParams.get('limit')  ?? 50);
    const offset  = Number(url.searchParams.get('offset') ?? 0);

    const accounts = await apiFetch(fetch, '/api/accounts/') as Account[];

    const qs = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
      date_from: from,
      date_to: to,
      category: 'null' // inbox = uncategorized
    });
    if (account !== 'all') qs.set('account_id', account);
    if (q) qs.set('q', q);

    const res = await apiFetch(fetch, `/api/transactions/?${qs.toString()}`) as unknown;
    const items: Transaction[] = Array.isArray(res) ? (res as any) : ((res as any).items ?? []);
    const total: number = Array.isArray(res) ? (res as any).length : ((res as any).total ?? items.length);

    return {
      accounts,
      items,
      total,
      filters: { account, from, to, q, limit, offset, view: 'uncategorized' }
    } satisfies LoadData;
  } catch (e: any) {
    throw error(500, e.message || 'Failed to load transactions');
  }
};
