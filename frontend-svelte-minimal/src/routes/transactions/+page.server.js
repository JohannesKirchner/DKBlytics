const SORTS = new Set(['date_desc', 'date_asc', 'amount_desc', 'amount_asc']);
const DATE_RX = /^\d{4}-\d{2}-\d{2}$/;

export async function load({ fetch, url }) {
  const sp = url.searchParams;

  const limit  = Number(sp.get('limit') ?? 20);
  const offset = Number(sp.get('offset') ?? 0);

  const q0 = (sp.get('q') ?? '').trim();
  const q  = q0.length >= 2 ? q0 : null;

  const sort_by = SORTS.has(sp.get('sort_by')) ? sp.get('sort_by') : 'date_desc';

  const date_from = validDate(sp.get('date_from')) ? sp.get('date_from') : null;
  const date_to   = validDate(sp.get('date_to'))   ? sp.get('date_to')   : null;

  const category = sp.get('category');
  const account_id = sp.get('account_id') ?? null;

  const qs = new URLSearchParams({
    limit, offset, sort_by,
    ...(q ? { q } : {}),
    ...(date_from ? { date_from } : {}),
    ...(date_to ? { date_to } : {}),
    ...(account_id ? { account_id } : {}),
    ...(category ? { category }: {})
  }).toString();

  const [accRes, txRes] = await Promise.all([
    fetch('/api/accounts/'),
    fetch(`/api/transactions/?${qs}`)
  ]);

  if (!accRes.ok || !txRes.ok) throw new Error('Failed to load data');

  const [accounts, transactions] = await Promise.all([accRes.json(), txRes.json()]);

  return {
    accounts: accounts.map(a => ({ id: a.id, name: a.name })),
    transactions,
    limit, 
    offset,
    filters: { q, sort_by, date_from, date_to, account_id }
  };
}

function validDate(s) {
  return typeof s === 'string' && DATE_RX.test(s);
}
