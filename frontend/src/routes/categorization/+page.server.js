import { fail } from '@sveltejs/kit';

export async function load({ fetch }) {
  const res = await fetch('/api/categories/tree');
  if (!res.ok) throw new Error('Failed to load category tree');
  const tree = await res.json();
  return { tree };
}

async function errorMessage(res, fallback) {
  try {
    const data = await res.json();
    if (data?.detail) {
      return Array.isArray(data.detail) ? data.detail[0]?.msg ?? fallback : data.detail;
    }
  } catch {}
  return fallback;
}

export const actions = {
  async create({ request, fetch }) {
    const fd = await request.formData();
    const name = (fd.get('name') ?? '').toString().trim();
    const parent_id_raw = fd.get('parent_id');
    const parent_id = parent_id_raw ? Number(parent_id_raw) : null;
    if (!name) return fail(400, { action: 'create', error: 'Name is required' });

    const body = parent_id == null ? { name } : { name, parent_id };
    const res = await fetch('/api/categories/', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      return fail(res.status, {
        action: 'create',
        error: await errorMessage(res, `Create failed (${res.status})`)
      });
    }
    return { success: true };
  },

  async rename({ request, fetch }) {
    const fd = await request.formData();
    const id = Number(fd.get('id'));
    const name = (fd.get('name') ?? '').toString().trim();
    if (!id) return fail(400, { action: 'rename', error: 'Missing id' });
    if (!name) return fail(400, { action: 'rename', error: 'Name is required' });

    const res = await fetch(`/api/categories/${id}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (!res.ok) {
      return fail(res.status, {
        action: 'rename',
        error: await errorMessage(res, `Rename failed (${res.status})`)
      });
    }
    return { success: true };
  },

  async delete({ request, fetch }) {
    const fd = await request.formData();
    const id = Number(fd.get('id'));
    if (!id) return fail(400, { action: 'delete', error: 'Missing id' });

    const res = await fetch(`/api/categories/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      return fail(res.status, {
        action: 'delete',
        error: await errorMessage(res, `Delete failed (${res.status})`)
      });
    }
    return { success: true };
  }
};
