export async function load({ fetch, url }) {
  console.log(typeof url)
  console.log(url)

  const limit = Number(url.searchParams.get('limit') ?? 10);
  const offset = Number(url.searchParams.get('offset') ?? 0);

  const [accRes, txRes] = await Promise.all([
    fetch('/api/accounts/'),
    fetch(`/api/transactions/?limit=${limit}&offset=${offset}&sort_by=date_desc`)
  ]);

  const [accounts, transactions] = await Promise.all([
    accRes.json(),
    txRes.json()
  ])

  console.log(`Just fetched new transactions with limit ${limit} and offset ${offset}`)

  return { accounts, transactions, limit, offset };
}