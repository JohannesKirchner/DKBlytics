<script>
  import { goto } from '$app/navigation';
  import { enhance } from '$app/forms';
  const { data, form } = $props();

  // side panel for categorization
  let selectedTransaction  = $state(null);
  let rule_schema   = $state('entity'); // 'entity', 'entity_text' or 'transaction'
  let rule_category = $state('');
  let rule_creating = $state(false);
  
  // local filter state and pagination from server
  let q          = $state(data.filters.q ?? '');
  let sort_by    = $state(data.filters.sort_by);
  let date_from  = $state(data.filters.date_from ?? '');
  let date_to    = $state(data.filters.date_to ?? '');
  let account_id = $state(data.filters.account_id ?? '');
  let category   = $state(data.filters.category ?? '')
  let limit      = $state(data.limit);
  let offset     = $state(data.offset);

  // goto page function with updated query
  function nav() {
    const sp = new URLSearchParams();
    sp.set('limit', String(limit));
    sp.set('offset', String(offset));
    if (q.trim().length >= 2) sp.set('q', q.trim());
    if (sort_by) sp.set('sort_by', sort_by);
    if (date_from) sp.set('date_from', date_from);
    if (date_to) sp.set('date_to', date_to);
    if (category) sp.set('category', category);
    if (account_id) sp.set('account_id', account_id);

    goto(`?${sp.toString()}`, { replaceState: true, noScroll: true, keepfocus: true });
  }

  // update transaction if any of the search params with state changes
  let qTimer = null;
  $effect(() => {
    // check for state changes from server
    const changedQ = (data.filters.q ?? '') !== q;
    const changedWithoutQ = !(
        data.filters.sort_by === sort_by &&
        (data.filters.date_from ?? '') === date_from &&
        (data.filters.date_to ?? '') === date_to &&
        (data.filters.category ?? '') === category &&
        (data.filters.account_id ?? '') === account_id
    )
    const changedPagination = !(
        data.limit === limit && 
        data.offset === offset
    )

    clearTimeout(qTimer);
    if (changedPagination) {
      // navigate pagination changes immediately
      nav();
    }
    if (changedWithoutQ && !changedQ) {
      // navigate any change that does not involve q immediately and reset pagination
      offset = 0;
      nav();
    }
    else if (changedQ) {
      // any change involving Q will be delayed by 500 ms to allow continous user typing
      offset = 0;
      qTimer = setTimeout(() => {offset = 0; nav()}, 500);
    } else {
      // prevent first time runs if nothing changed
      return;
    }
  })
</script>

<div class="mb-6 rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm">
  <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      Search
      <input
        class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-normal text-slate-900 placeholder:text-slate-400 shadow-sm transition focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
        value={q}
        oninput={(e) => q = e.currentTarget.value}
        placeholder="min 2 chars"
      />
    </label>

    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      Category
      <select
        class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
        value={category}
        onchange={(e) => category = e.currentTarget.value}
      >
        <option value="">All</option>
        <option value="null" selected={data.filters.category === 'null'}>Uncategorized</option>
        {#each data.categories as c}
          <option value={c} selected={data.filters.category === c}>{c}</option>
        {/each}
      </select>
    </label>

    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      Sort
      <select
        class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
        value={sort_by}
        onchange={(e) => sort_by = e.currentTarget.value}
      >
        <option value="date_desc">Date ↓</option>
        <option value="date_asc">Date ↑</option>
        <option value="amount_desc">Amount ↓</option>
        <option value="amount_asc">Amount ↑</option>
      </select>
    </label>

    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      From
      <input
        class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
        type="date"
        value={date_from}
        oninput={(e) => date_from = e.currentTarget.value}
      />
    </label>

    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      To
      <input
        class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
        type="date"
        value={date_to}
        oninput={(e) => date_to = e.currentTarget.value}
      />
    </label>

    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      Account
      <select
        class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
        value={account_id}
        onchange={(e) => account_id = e.currentTarget.value}
      >
        <option value="">All</option>
        {#each data.accounts as a}
          <option value={a.id}>{a.name}</option>
        {/each}
      </select>
    </label>
  </div>
</div>

<table class="w-full table-fixed border-separate border-spacing-x-2 border-spacing-y-0 overflow-hidden rounded-2xl bg-white text-sm shadow-sm">
  <thead class="bg-slate-50 text-left text-xs font-bold uppercase tracking-wide text-slate-600">
    <tr>
      <th class="w-10 px-5 py-3">Date</th>
      <th class="w-10 px-5 py-3">Account</th>
      <th class="w-30 px-5 py-3">Sender/Recipient</th>
      <th class="w-60 px-5 py-3">Description</th>
      <th class="w-16 px-5 py-3">Category</th>
      <th class="w-10 px-5 py-3 text-right">Amount</th>
    </tr>
  </thead>
  <tbody>
    {#each data.transactions.items as t}
      <tr
        class={`border-b border-slate-100 transition hover:bg-slate-50 ${t.id === selectedTransaction?.id ? 'bg-slate-100' : ''}`}
        onclick={() => {selectedTransaction=t}}
      >
        <td class="whitespace-nowrap px-5 py-3 text-slate-700">{t.date}</td>
        <td class="px-5 py-3 text-slate-700">{t.account_name}</td>
        <td class="truncate px-5 py-3 text-slate-900">{t.entity}</td>
        <td class="truncate px-5 py-3 text-xs text-slate-500">{t.text}</td>
        <td class="px-5 py-3 text-slate-700">{t.category ?? "Uncategorized"}</td>
        <td class="px-5 py-3 text-right font-semibold text-slate-900">{t.amount}</td>
      </tr>
    {/each}
  </tbody>
</table>

<div class="mt-4 py-2 px-6 border pt-4 rounded-xl">
  <div class="flex flex-row justify-between items-center gap-4">
    <div class="flex items-center justify-start">
      <form
        method="POST"
        action="?/createCategoryRule"
        use:enhance={() => {
          rule_creating = true;
          return async ({ update }) => {await update(); rule_creating = false;};
        }}
      >
        <div class="flex flex-row gap-8">
          <label class="flex w-full flex-col text-xs font-bold uppercase tracking-wide text-slate-500 sm:flex-1">
            Category
            <select
              class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
              name="rule_category"
              value={rule_category}
              onchange={(e)=>rule_category=e.currentTarget.value}
            >
              {#each data.categories as c}
                <option value={c}>{c}</option>
              {/each}
            </select>
          </label>

          <label class="flex w-full flex-col text-xs font-bold uppercase tracking-wide text-slate-500 sm:flex-1">
            Rule Schema
            <select
              class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
              name="rule_schema"
              value={rule_schema}
              onchange={(e)=>rule_schema=e.currentTarget.value}
            >
              <option value='by-entity'>by-entity</option>
              <option value='by-text'>by-text</option>
              <option value='by-transaction'>by-transaction</option>
            </select>
          </label>

          <button
            type="submit"
            class="inline-flex items-center justify-center rounded-full border border-slate-900/80 bg-slate-900 px-5 py-2 my-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-200 disabled:text-slate-500"
            class:opacity-70={rule_creating}
            disabled={selectedTransaction == null}
          >
            {rule_creating ? 'Applying…' : 'Create Rule'}
          </button>
        </div>

        <input type="hidden" name="transactionId" value={selectedTransaction?.id} />
        <input type="hidden" name="entity" value={selectedTransaction?.entity ?? ''} />
        <input type="hidden" name="text" value={selectedTransaction?.text ?? ''} />

        {#if form?.error}
          <p class="w-full rounded-xl border border-rose-100 bg-rose-50 px-4 py-2 text-sm text-rose-700 lg:col-span-2">{form.error}</p>
        {/if}
      </form>
    </div>
    
    <div class="flex items-center justify-end gap-3">
      <button
        class="inline-flex items-center rounded-full border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-300"
        onclick={() => offset = offset - limit}
        disabled={offset === 0}
      >
        Prev
      </button>

      <p class="text-sm text-gray-600 whitespace-nowrap">
        Page <span class="font-semibold">{Math.floor(offset / limit) + 1}</span>
        of <span class="font-semibold">{Math.ceil(data.transactions.total / limit)}</span>
        <span class="text-gray-400 mx-1">•</span>
        <span class="text-gray-500">({data.transactions.total} total)</span>
      </p>
      
      <button
        class="inline-flex items-center rounded-full border border-slate-900/80 bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-200"
        onclick={() => offset = offset + limit}
        disabled={offset + limit > data.transactions.total}
      >
        Next
      </button>
    </div>
  </div>
</div>
