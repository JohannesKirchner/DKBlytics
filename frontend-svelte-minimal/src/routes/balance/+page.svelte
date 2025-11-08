<script>
  import { goto } from '$app/navigation';
  const { data } = $props();
  
  $effect(() => {
    if (limit === data.limit && offset === data.offset) return;
    const params = new URLSearchParams(location.search);
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    goto(`?${params.toString()}`, { replaceState: true, noScroll: true, keepfocus: true });
  });

  let limit = $state(data.limit);
  let offset = $state(data.offset);
</script>

<h1>Balance</h1>
<p>{data.accounts.length} accounts</p>
<ul>
    {#each data.accounts as a}
        <li>{a.name}, {a.balance}</li>
    {/each}
</ul>

<h2>Recent transactions</h2>
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


<div style="margin-top: 0.5rem;">
    <button onclick={() => offset = offset - limit} disabled={offset === 0}>Prev</button>
    <span style="margin: 0 0.5rem;">offset {offset}</span>
    <button onclick={() => offset = offset + limit}>Next</button>
</div>