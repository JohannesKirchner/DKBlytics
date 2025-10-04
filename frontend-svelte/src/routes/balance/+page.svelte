<script>
  export let data;
  const accounts = data.accounts ?? [];
  const transactions = data.transactions ?? [];
  const total = data.total ?? 0;

  console.log('[page] /data', data);

  const fmtEUR = (v) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' })
      .format(Number(v ?? 0));

  const rowText = (t) => t.entity ?? t.text ?? '';
  const rowCat  = (t) => t.category_name ?? t.category ?? '';
  const rowAcc  = (t) => t.account_name ?? t.account_id ?? '';
</script>

<h1 class="text-2xl font-bold p-4">Balance Overview</h1>

{#if accounts.length === 0}
  <p class="p-4 text-neutral-600">No accounts yet.</p>
{:else}
  <div class="overflow-x-auto">
    <table class="w-full border-collapse">
      <thead>
        <tr class="text-left text-sm text-neutral-600 border-b">
          <th class="py-2 px-3">Name</th>
          <th class="py-2 px-3">Holder</th>
          <th class="py-2 px-3 text-right">Balance</th>
        </tr>
      </thead>
      <tbody>
        {#each accounts as a}
          <tr class="border-b hover:bg-neutral-200">
            <td class="py-2 px-3">{a.name}</td>
            <td class="py-2 px-3">{a.holder_name}</td>
            <td class="py-2 px-3 text-right font-medium">{fmtEUR(a.balance)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

<h2 class="text-xl font-semibold mt-8 mb-2">Recent transactions (first 50)</h2>

{#if transactions.length === 0}
  <p class="text-neutral-600">No transactions in this period.</p>
{:else}
  <div class="overflow-x-auto">
    <table class="w-full border-collapse">
      <thead>
        <tr class="text-left text-sm text-neutral-600 border-b">
          <th class="py-2 px-3">Date</th>
          <th class="py-2 px-3">Account</th>
          <th class="py-2 px-3">Description</th>
          <th class="py-2 px-3">Category</th>
          <th class="py-2 px-3 text-right">Amount</th>
        </tr>
      </thead>
      <tbody>
        {#each transactions as t}
          <tr class="border-b hover:bg-neutral-50">
            <td class="py-2 px-3">{t.date}</td>
            <td class="py-2 px-3">{rowAcc(t)}</td>
            <td class="py-2 px-3">{rowText(t)}</td>
            <td class="py-2 px-3">{rowCat(t)}</td>
            <td class="py-2 px-3 text-right font-medium">{fmtEUR(t.amount)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  <p class="text-xs text-neutral-500 mt-2">Showing {transactions.length} of {total}.</p>
{/if}
