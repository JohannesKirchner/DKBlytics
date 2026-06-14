import { fail } from '@sveltejs/kit';

const SORTS = new Set(['date_desc', 'date_asc', 'amount_desc', 'amount_asc']);
const DATE_RX = /^\d{4}-\d{2}-\d{2}$/;
const SEEDED_ROOTS = new Set(['Einnahmen', 'Ausgaben']);

function validDate(s) {
  return typeof s === 'string' && DATE_RX.test(s);
}

// Flatten the category tree into a typeahead-friendly list. Each entry has
// { id, name, parent_path, kind } where:
//   - parent_path is the immediate parent's name (used to disambiguate
//     duplicate leaf names like two "Wohnen" entries under different parents)
//   - kind is 'income' or 'expense' derived from the root ancestor
// The two seeded roots (Einnahmen / Ausgaben) themselves are not assignable.
function flattenCategoryTree(roots) {
  const out = [];
  function walk(node, kind, parentName) {
    out.push({ id: node.id, name: node.name, parent_path: parentName, kind });
    for (const child of node.children ?? []) walk(child, kind, node.name);
  }
  for (const root of roots) {
    const kind = root.name === 'Einnahmen' ? 'income' : 'expense';
    for (const child of root.children ?? []) walk(child, kind, root.name);
  }
  return out;
}

async function errorMessage(res, fallback) {
  try {
    const data = await res.json();
    if (data?.detail) {
      return Array.isArray(data.detail) ? (data.detail[0]?.msg ?? fallback) : data.detail;
    }
  } catch {}
  return fallback;
}

export async function load({ fetch, url }) {
  const sp = url.searchParams;

  const limit = Number(sp.get('limit') ?? 15);
  const offset = Number(sp.get('offset') ?? 0);

  const q0 = (sp.get('q') ?? '').trim();
  const q = q0.length >= 2 ? q0 : null;

  const sort_by = SORTS.has(sp.get('sort_by')) ? sp.get('sort_by') : 'date_desc';
  const date_from = validDate(sp.get('date_from')) ? sp.get('date_from') : null;
  const date_to = validDate(sp.get('date_to')) ? sp.get('date_to') : null;

  const category = sp.get('category') === 'null' ? 'null' : (sp.get('category') || null);
  const account_id = sp.get('account_id') ?? null;

  const qs = new URLSearchParams({
    limit, offset, sort_by,
    ...(q ? { q } : {}),
    ...(date_from ? { date_from } : {}),
    ...(date_to ? { date_to } : {}),
    ...(account_id ? { account_id } : {}),
    ...(category != null ? { category } : {})
  }).toString();

  const [accRes, treeRes, txRes] = await Promise.all([
    fetch('/api/accounts/'),
    fetch('/api/categories/tree'),
    fetch(`/api/transactions/?${qs}`)
  ]);

  if (!accRes.ok || !treeRes.ok || !txRes.ok) throw new Error('Failed to load data');

  const [accounts, tree, transactions] = await Promise.all([
    accRes.json(),
    treeRes.json(),
    txRes.json()
  ]);

  const categories = flattenCategoryTree(tree);
  // For the existing category filter dropdown — keep the simple name list.
  const categoryNames = categories.map((c) => c.name);

  return {
    accounts: accounts.map((a) => ({ id: a.public_id, name: a.name })),
    categories,
    categoryNames,
    transactions,
    limit,
    offset,
    filters: { q, sort_by, date_from, date_to, account_id, category }
  };
}

export const actions = {
  // PUT /api/transactions/{id} — edit description (and entity if needed).
  async updateText({ request, fetch }) {
    const fd = await request.formData();
    const id = Number(fd.get('id'));
    const text = (fd.get('text') ?? '').toString();
    if (!id) return fail(400, { action: 'updateText', error: 'Missing id' });

    const res = await fetch(`/api/transactions/${id}`, {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!res.ok) {
      return fail(res.status, {
        action: 'updateText',
        error: await errorMessage(res, `Update failed (${res.status})`)
      });
    }
    return { success: true };
  },

  // POST /api/rules/ — assign a category by creating a rule. rule_mode picks
  // which schema is sent:
  //   - 'entity'        → { entity, category_id }
  //   - 'entity_text'   → { entity, text, category_id }
  //   - 'none'          → { transaction_id, category_id } (one-time)
  // The backend recalculates affected transactions automatically.
  async assignCategory({ request, fetch }) {
    const fd = await request.formData();
    const transaction_id = Number(fd.get('transaction_id'));
    const entity = (fd.get('entity') ?? '').toString();
    const text = (fd.get('text') ?? '').toString();
    const category_id = Number(fd.get('category_id'));
    const rule_mode = (fd.get('rule_mode') ?? 'entity').toString();

    if (!transaction_id) return fail(400, { action: 'assignCategory', error: 'Missing transaction id' });
    if (!category_id) return fail(400, { action: 'assignCategory', error: 'Pick a category first' });

    let body;
    if (rule_mode === 'entity') {
      if (!entity) return fail(400, { action: 'assignCategory', error: 'Entity is empty — use "one-time" instead' });
      body = { entity, category_id };
    } else if (rule_mode === 'entity_text') {
      if (!entity) return fail(400, { action: 'assignCategory', error: 'Entity is empty — use "one-time" instead' });
      if (!text) return fail(400, { action: 'assignCategory', error: 'Description is empty — pick another mode' });
      body = { entity, text, category_id };
    } else if (rule_mode === 'none') {
      body = { transaction_id, category_id };
    } else {
      return fail(400, { action: 'assignCategory', error: `Unknown rule mode "${rule_mode}"` });
    }

    const res = await fetch('/api/rules/', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      return fail(res.status, {
        action: 'assignCategory',
        error: await errorMessage(res, `Assign failed (${res.status})`)
      });
    }
    return { success: true };
  }
};
