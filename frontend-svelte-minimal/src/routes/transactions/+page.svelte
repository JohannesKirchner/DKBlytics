<script>
  import { goto } from '$app/navigation';
  const { data } = $props();
  
  // local state mirrored from server
  let q          = $state(data.filters.q ?? '');
  let sort_by    = $state(data.filters.sort_by);
  let date_from  = $state(data.filters.date_from ?? '');
  let date_to    = $state(data.filters.date_to ?? '');
  let account_id = $state(data.filters.account_id ?? '');

  let limit = $state(data.limit);
  let offset = $state(data.offset);

  // navigation helper
  function nav() {
    const sp = new URLSearchParams();
    sp.set('limit', String(limit));
    sp.set('offset', String(offset));
    if (q.trim().length >= 2) sp.set('q', q.trim());
    if (sort_by) sp.set('sort_by', sort_by);
    if (date_from) sp.set('date_from', date_from);
    if (date_to) sp.set('date_to', date_to);
    if (account_id !== '' && account_id != null) sp.set('account_id', String(account_id));
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
        String(data.filters.account_id ?? '') === String(account_id) &&
        data.limit === limit && 
        data.offset === offset
    )

    clearTimeout(qTimer);
    if (changedWithoutQ && !changedQ) {
        // navigate any change that does not involve q immediately
        console.log("Updated non Q search params")
        nav();
    }
    else if (changedQ) {
        // any change involving Q will be delayed by 500 ms to allow continous user typing
        qTimer = setTimeout(() => {offset = 0; nav()}, 500);
        console.log("Set timer for qChange")
    } else {
        // prevent first time runs if nothing changed
        return;
    }
  })
</script>

<h1>Recent transactions</h1>
<div style="display:flex gap:.5rem flex-wrap:wrap align-items:end margin:.5rem 0 1rem">
  <label>Search
    <input
      value={q}
      oninput={(e) => q = e.currentTarget.value}
      placeholder="min 2 chars"
      style="padding:.25rem .5rem"
    />
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
    <select
      value={String(account_id)}
      onchange={(e) => { const v = e.currentTarget.value; account_id = v === '' ? '' : Number(v); }}
    >
      <option value="">All</option>
      {#each data.accounts as a}
        <option value={a.id}>{a.name}</option>
      {/each}
    </select>
  </label>
</div>

<table>
    <thead>
        <tr>
            <th>Date</th>
            <th>Account</th>
            <th>Entity</th>
            <th>Amount</th>
        </tr>
    </thead>
    <tbody>
        {#each data.transactions.items as t}
            <tr>
                <td>{t.date}</td>
                <td>{t.account_name}</td>
                <td>{t.entity}</td>
                <td>{t.amount}</td>
            </tr>
        {/each}
    </tbody>
</table>


<div style="margin-top: 0.5rem p-2">
    <button onclick={() => offset = offset - limit} disabled={offset === 0}>Prev</button>
    <button onclick={() => offset = offset + limit}>Next</button>
</div>