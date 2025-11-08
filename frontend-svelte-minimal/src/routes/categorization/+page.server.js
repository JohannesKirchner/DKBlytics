import { fail, redirect } from '@sveltejs/kit';

export async function load({ fetch }) {
  const catTreeRes = await fetch('/api/categories/tree');

  if (!catTreeRes.ok) throw new Error('Failed to load data');

  const categoryTree = await catTreeRes.json();

  return {categoryTree};
};

export const actions = {
  async createCategory({ request, fetch }) {
    const fd = await request.formData();
    const name = (fd.get('name') || '').toString().trim();
    const parent_input = (fd.get('parent_name') || '').toString().trim();
    const parent_name = parent_input === '' ? null : parent_input;

    if (!name) return fail(400, { error: 'Name is required', values: { name, parent_name: parent_input } });

    const res = await fetch('/api/categories/', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name, parent_name })
    });

    if (!res.ok) {
      let msg = `Create failed (${res.status})`;
      try {
        const data = await res.json();
        if (data?.detail) msg = Array.isArray(data.detail) ? (data.detail[0]?.msg || msg) : data.detail;
      } catch {}
      return fail(res.status, { error: msg, values: { name, parent_name: parent_input } });
    }

    throw redirect(303, '/categorization');
  },

  async deleteCategory({ request, fetch }) {
    const fd = await request.formData();
    const name = (fd.get('name') || '').toString().trim();
    if (!name) return fail(400, { error: 'Missing category name' });

    const res = await fetch(`/api/categories/${encodeURIComponent(name)}`, {
      method: 'DELETE'
    });

    if (!res.ok) {
      let msg = `Delete failed (${res.status})`;
      try {
        const data = await res.json();
        if (data?.detail) msg = data.detail;
      } catch {}
      return fail(res.status, { error: msg });
    }

    throw redirect(303, '/categorization');
  }
};
