<script lang="ts">
  import type { Account } from '$lib/types/accounts';
  import type { Transaction } from '$lib/types/transactions';

  export let data: {
    accounts: Account[];
    items: Transaction[];
    total: number;
    filters: { account: string; from: string; to: string; q: string; limit: number; offset: number; view: 'uncategorized' };
  };

  // helpers
  const fmtEUR = (v: string | number) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(Number(v ?? 0));

  const displayText = (t: Transaction) => t.entity ?? t.text ?? '';
  const displayAcc  = (t: Transaction) => t.account_name ?? t.account_id ?? '';

  let startIdx = 0;
  let endIdx = 0;
  $: startIdx = data.filters.offset + 1;
  $: endIdx = Math.min(data.filters.offset + data.filters.limit, data.total);

  function nextOffset(): number {
    const n = data.filters.offset + data.filters.limit;
    return n >= data.total ? data.filters.offset : n;
  }
  function prevOffset(): number {
    const p = data.filters.offset - data.filters.limit;
    return p < 0 ? 0 : p;
  }
  function linkWithOffset(off: number): string {
    const qs = new URLSearchParams();
    if (data.filters.account !== 'all') qs.set('account', data.filters.account);
    if (data.filters.from) qs.set('from', data.filters.from);
    if (data.filters.to)   qs.set('to', data.filters.to);
    if (data.filters.q)    qs.set('q', data.filters.q);
    if (data.filters.limit !== 50) qs.set('limit', String(data.filters.limit));
    if (off) qs.set('offset', String(off));
    const q = qs.toString();
    return q ? `/transactions?${q}` : `/transactions`;
  }
</script>

<p class="text-xs text-neutral-600 mb-2">
  Inbox items: {data.items?.length ?? 0} / total: {data.total ?? 0}
</p>

<h1 class="text-2xl font-bold mb-3">Transactions</h1>

<!-- Grid: 1 column on mobile; 2 columns on large screens -->
<div class="grid lg:grid-cols-[minmax(0,1fr)_24rem] gap-4">
  <!-- LEFT: Inbox / table area -->
  <section class="col-span-1 rounded-lg border bg-white">
    <!-- sticky toolbar for filters; stays at top of this card when it overflows -->
    <header class="sticky top-0 z-10 border-b bg-white/95 backdrop-blur p-3">
        <div class="flex items-center justify-between text-sm">
            <div class="text-neutral-600">Uncategorized in range</div>
            <div class="text-neutral-500">
            Showing {data.total ? `${startIdx}–${endIdx}` : 0} of {data.total}
            </div>
        </div>
    </header>

    <!-- scrollable content if it grows tall -->
    <div class="p-3 lg:max-h-[70vh] lg:overflow-y-auto">
      <div class="p-0">
        {#if data.items.length === 0}
            <div class="p-4 text-neutral-500">🎉 Nothing to categorize here. Try widening the date range.</div>
        {:else}
            <div class="overflow-x-auto">
            <table class="w-full border-collapse text-sm">
                <thead>
                <tr class="text-left text-neutral-600 border-b">
                    <th class="py-2 px-3">Date</th>
                    <th class="py-2 px-3">Account</th>
                    <th class="py-2 px-3">Entity / Text</th>
                    <th class="py-2 px-3">Category</th>
                    <th class="py-2 px-3 text-right">Amount</th>
                </tr>
                </thead>
                <tbody>
                {#each data.items as t (t.id ?? t.public_id ?? `${t.account_id}-${t.date}-${t.amount}-${displayText(t)}`)}
                    <tr class="border-b hover:bg-neutral-50">
                    <td class="py-2 px-3">{t.date}</td>
                    <td class="py-2 px-3">{displayAcc(t)}</td>
                    <td class="py-2 px-3">
                        <div class="font-medium">{displayText(t) || '—'}</div>
                        {#if t.text && t.entity && t.text !== t.entity}
                        <div class="text-xs text-neutral-500 truncate">{t.text}</div>
                        {/if}
                    </td>
                    <td class="py-2 px-3">
                        <span class="inline-block rounded bg-neutral-100 px-2 py-0.5 text-xs">
                        {t.category_name ?? t.category ?? '—'}
                        </span>
                    </td>
                    <td class="py-2 px-3 text-right font-medium">{fmtEUR(t.amount)}</td>
                    </tr>
                {/each}
                </tbody>
            </table>
            </div>

            <!-- PAGINATION -->
            <div class="flex items-center justify-between p-3 text-sm">
            <a
                href={linkWithOffset(prevOffset())}
                class="px-3 py-1.5 rounded border hover:bg-neutral-50"
                aria-disabled={data.filters.offset === 0}
                class:opacity-50={data.filters.offset === 0}
                class:pointer-events-none={data.filters.offset === 0}
            >
                ← Prev
            </a>

            <div class="text-neutral-500">{startIdx}–{endIdx} of {data.total}</div>

            <a
                href={linkWithOffset(nextOffset())}
                class="px-3 py-1.5 rounded border hover:bg-neutral-50"
                aria-disabled={endIdx >= data.total}
                class:opacity-50={endIdx >= data.total}
                class:pointer-events-none={endIdx >= data.total}
            >
                Next →
            </a>
            </div>
        {/if}
        </div>
    </div>
  </section>

  <!-- RIGHT: Inspector drawer/panel -->
  <aside class="col-span-1 rounded-lg border bg-white p-3 lg:sticky lg:top-2 h-fit">
    <div class="text-neutral-500">
      Inspector goes here (select a row to see details)
    </div>
    <!-- later: header, facts, "why", rule builder -->
  </aside>
</div>
