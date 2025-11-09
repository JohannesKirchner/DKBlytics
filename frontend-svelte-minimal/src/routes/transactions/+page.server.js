import { fail, redirect } from '@sveltejs/kit';


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

  const category = sp.get('category') === 'null' ? 'null' : (sp.get('category') || null);
  const account_id = sp.get('account_id') ?? null;

  const qs = new URLSearchParams({
    limit, offset, sort_by,
    ...(q ? { q } : {}),
    ...(date_from ? { date_from } : {}),
    ...(date_to ? { date_to } : {}),
    ...(account_id ? { account_id } : {}),
    ...(category != null ? { category }: {})
  }).toString();

  const [accRes, catRes, txRes] = await Promise.all([
    fetch('/api/accounts/'),
    fetch('/api/categories/'),
    fetch(`/api/transactions/?${qs}`)
  ]);

  if (!accRes.ok || !txRes.ok || !catRes.ok) throw new Error('Failed to load data');

  const [accounts, categories, transactions] = await Promise.all(
    [accRes.json(), catRes.json(), txRes.json()]
  );

  return {
    accounts: accounts.map(a => ({ id: a.public_id, name: a.name })),
    categories: categories.map(c => c.name),
    transactions,
    limit, 
    offset,
    filters: { q, sort_by, date_from, date_to, account_id, category }
  };
}

function validDate(s) {
  return typeof s === 'string' && DATE_RX.test(s);
}

export const actions = {
  async createCategoryRule({ request, fetch }) {
    const fd = await request.formData();
    const rule_category = (fd.get('rule_category') || '').toString().trim();
    const rule_schema   = (fd.get('rule_schema') || '').toString().trim();
    let text          = (fd.get('text') || '').toString().trim();
    let entity        = (fd.get('entity') || '').toString().trim();
    let transactionId = (fd.get('transactionId') || '').toString().trim();

    console.log(fd)

    console.log(JSON.stringify({ transactionId, text, entity, rule_category }))

    if (rule_schema === "by-entity") {
      text = null;
      transactionId = null;
    } else if (rule_schema === "by-text") {
      transactionId = null;
    } else if (rule_schema === "by-transaction") {
      entity = null;
      text = null;
    }

    console.log(JSON.stringify({ transactionId, text, entity, rule_category }))

    const res = await fetch('/api/rules/', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ transactionId, text, entity, rule_category })
    });

    if (!res.ok) {
      let msg = `Creation of transaction rule failed (${res.status})`;
      try {
        const data = await res.json();
        if (data?.detail) msg = Array.isArray(data.detail) ? (data.detail[0]?.msg || msg) : data.detail;
      } catch {}
      return fail(res.status, { error: msg, values: { transactionId, text, entity, rule_category } });
    }

    throw redirect(303, '/transactions');
  }
}
