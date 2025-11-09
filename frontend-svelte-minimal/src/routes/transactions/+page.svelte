<script>
  import { goto } from '$app/navigation';
  const { data, form } = $props();

  // side panel for categorization
  let selectedTransaction  = $state(null);
  let rule_schema   = $state('entity'); // 'entity', 'entity_text' or 'transaction'
  let rule_category = $state('');
  
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
        (data.filters.account_id ?? '') === account_id &&
        data.limit === limit && 
        data.offset === offset
    )

    clearTimeout(qTimer);
    if (changedWithoutQ && !changedQ) {
        // navigate any change that does not involve q immediately
        nav();
    }
    else if (changedQ) {
        // any change involving Q will be delayed by 500 ms to allow continous user typing
        qTimer = setTimeout(() => {offset = 0; nav()}, 500);
    } else {
        // prevent first time runs if nothing changed
        return;
    }
  })
</script>

<div style="display:flex gap:.5rem flex-wrap:wrap align-items:end margin:.5rem 0 1rem">
  <label>Search
    <input
      value={q}
      oninput={(e) => q = e.currentTarget.value}
      placeholder="min 2 chars"
      style="padding:.25rem .5rem"
    />
  </label>

  <label>Category
    <select value={category} onchange={(e) => category = e.currentTarget.value}>
      <option value="">All</option>
      <option value="null" selected={data.filters.category === 'null'}>Uncategorized</option>
      {#each data.categories as c}
        <option value={c} selected={data.filters.category === c}>{c}</option>
      {/each}
    </select>
  </label>

  <label>Sort
    <select value={sort_by} onchange={(e) => sort_by = e.currentTarget.value}>
      <option value="date_desc">Date ↓</option>
      <option value="date_asc">Date ↑</option>
      <option value="amount_desc">Amount ↓</option>
      <option value="amount_asc">Amount ↑</option>
    </select>
  </label>

  <label>From
    <input type="date" value={date_from} oninput={(e) => date_from = e.currentTarget.value} />
  </label>

  <label>To
    <input type="date" value={date_to} oninput={(e) => date_to = e.currentTarget.value} />
  </label>

  <label>Account
    <select value={account_id} onchange={(e) => account_id = e.currentTarget.value}>
      <option value="">All</option>
      {#each data.accounts as a}
        <option value={a.id}>{a.name}</option>
      {/each}
    </select>
  </label>
</div>

<table class="w-full border-collapse text-sm">
    <thead>
        <tr class="border-b border-gray-500 text-left text-gray-800">
            <th>Date</th>
            <th>Account</th>
            <th>Sender/Recipient</th>
            <th>Description</th>
            <th>Category</th>
            <th>Amount</th>
        </tr>
    </thead>
    <tbody>
        {#each data.transactions.items as t}
            <tr class={`border-b border-gray-300 hover:bg-gray-100 cursor-pointer ${t.id === selectedTransaction?.id ? 'bg-gray-200' : ''}`} onclick={() => {selectedTransaction=t}}>
                <td class="px-2 py-1">{t.date}</td>
                <td class="px-2 py-1">{t.account_name}</td>
                <td class="px-2 py-1">{t.entity}</td>
                <td class="px-2 py-1">{t.text}</td>
                <td class="px-2 py-1">{t.category ?? "Uncategorized"}</td>
                <td class="px-2 py-1">{t.amount}</td>
            </tr>
        {/each}
    </tbody>
</table>

<div style="margin-top: 0.5rem p-2">
    <button class="p-2 bg-gray-100 font-bold border-1 rounded-lg" onclick={() => offset = offset - limit} disabled={offset === 0}>Prev</button>
    <button class="p-2 bg-gray-100 font-bold border-1 rounded-lg" onclick={() => offset = offset + limit}>Next</button>
</div>

<form method="POST" class="pt-5" action="?/createCategoryRule">
  <label>Category
    <select name="rule_category" value={rule_category} onchange={(e)=>rule_category=e.currentTarget.value}>
      {#each data.categories as c}
        <option value={c}>{c}</option>
      {/each}
    </select>
  </label>

  <label>Rule Schema
    <select name="rule_schema" value={rule_schema} onchange={(e)=>rule_schema=e.currentTarget.value}>
        <option value='by-entity'>by-entity</option>
        <option value='by-text'>by-text</option>
        <option value='by-transaction'>by-transaction</option>
    </select>
  </label>

  <input type="hidden" name="transactionId" value={selectedTransaction?.id} />
  <input type="hidden" name="entity" value={selectedTransaction?.entity ?? ''} />
  <input type="hidden" name="text" value={selectedTransaction?.text ?? ''} />

  <button type="submit">Create Rule</button>

  {#if form?.error}
    <p>{form.error}</p>
  {/if}
</form>
