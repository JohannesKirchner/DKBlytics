<script>
  import { enhance } from '$app/forms';

  let { data, form } = $props();

  const ROOTS = [
    { name: 'Einnahmen', kind: 'income' },
    { name: 'Ausgaben', kind: 'expense' }
  ];

  let columns = $derived(
    ROOTS.map(({ name, kind }) => {
      const root = data.tree.find((r) => r.name === name);
      return { name, kind, root };
    })
  );

  let selectedId = $state(null);
  let mode = $state('actions'); // 'actions' | 'rename' | 'add' | 'confirm-delete'
  let addingToParentId = $state(null);
  let lastError = $state(null);

  function focusOnMount(node) {
    node.focus();
    node.select?.();
  }

  function selectNode(id) {
    if (selectedId === id) {
      clearAll();
    } else {
      selectedId = id;
      mode = 'actions';
      addingToParentId = null;
      lastError = null;
    }
  }

  function clearAll() {
    selectedId = null;
    mode = 'actions';
    addingToParentId = null;
    lastError = null;
  }

  function startAddingTo(parentId) {
    clearAll();
    addingToParentId = parentId;
  }

  function handleSubmit() {
    return async ({ update, result }) => {
      await update({ reset: false });
      if (result.type === 'success') {
        clearAll();
      } else if (result.type === 'failure') {
        lastError = result.data?.error ?? 'Operation failed';
      }
    };
  }
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && clearAll()} />

<div class="min-h-screen bg-white text-slate-900">
  <div class="max-w-5xl mx-auto px-6 pt-8 pb-16">
    {#if lastError}
      <div class="mb-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800" role="alert">
        {lastError}
      </div>
    {/if}

    <div class="grid grid-cols-1 items-start gap-8 md:grid-cols-2 md:gap-12">
      {#each columns as col (col.name)}
        <section>
          <div class="mb-3 border-b border-slate-100 pb-2">
            <span
              class="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider {col.kind ===
              'income'
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-rose-50 text-rose-700'}"
            >
              {col.name}
            </span>
          </div>

          {#if col.root}
            <ul class="tree">
              {#each col.root.children as cat, i (cat.id)}
                {@render row(cat, col.kind, 1, i === col.root.children.length - 1)}
              {/each}
            </ul>

            {#if addingToParentId === col.root.id}
              <form
                method="POST"
                action="?/create"
                use:enhance={handleSubmit}
                class="mt-3 inline-flex max-w-full flex-wrap items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2 py-1.5 shadow-sm"
              >
                <input type="hidden" name="parent_id" value={col.root.id} />
                <input
                  name="name"
                  use:focusOnMount
                  placeholder={`new ${col.name.toLowerCase()} category…`}
                  onkeydown={(e) => e.key === 'Escape' && clearAll()}
                  class="min-w-32 flex-1 rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
                />
                <button
                  type="submit"
                  class="rounded border border-slate-900 bg-slate-900 px-2.5 py-1 text-xs text-white hover:bg-slate-800"
                  >add</button
                >
                <button
                  type="button"
                  onclick={clearAll}
                  class="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
                  >cancel</button
                >
              </form>
            {:else}
              <button
                type="button"
                onclick={() => startAddingTo(col.root.id)}
                class="mt-3 rounded-md border border-dashed px-2.5 py-1 text-xs {col.kind ===
                'income'
                  ? 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                  : 'border-rose-200 text-rose-700 hover:bg-rose-50'}"
              >
                + add to {col.name.toLowerCase()}
              </button>
            {/if}
          {:else}
            <p class="text-sm text-slate-400">Root category “{col.name}” is missing.</p>
          {/if}
        </section>
      {/each}
    </div>
  </div>
</div>

{#snippet row(n, kind, depth, isLast)}
  {@const isSelected = selectedId === n.id}
  {@const hasChildren = n.children?.length > 0}
  <li class="row depth-{depth}" class:last={isLast}>
    <button
      type="button"
      class="-ml-2 inline-flex items-center gap-2 rounded px-2 py-0.5 text-left hover:bg-slate-50 {isSelected
        ? 'bg-blue-50 ring-1 ring-blue-200'
        : ''}"
      onclick={() => selectNode(n.id)}
    >
      <span class="bullet kind-{kind} depth-{depth}"></span>
      <span
        class={depth === 1
          ? 'text-base font-semibold text-slate-900'
          : depth === 2
            ? 'text-sm font-medium text-slate-800'
            : 'text-sm text-slate-600'}
      >
        {n.name}
      </span>
    </button>

    {#if isSelected}
      <div class="my-2 inline-flex max-w-full flex-wrap items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2 py-1.5 shadow-sm">

        {#if mode === 'actions'}
          <button
            type="button"
            onclick={() => (mode = 'rename')}
            class="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
            >Rename</button
          >
          <button
            type="button"
            onclick={() => (mode = 'add')}
            class="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
            >+ Subcategory</button
          >
          <button
            type="button"
            onclick={() => (mode = 'confirm-delete')}
            class="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-rose-700 hover:border-rose-200 hover:bg-rose-50"
            >Delete</button
          >
        {:else if mode === 'rename'}
          <form
            method="POST"
            action="?/rename"
            use:enhance={handleSubmit}
            class="inline-flex flex-wrap items-center gap-1.5"
          >
            <input type="hidden" name="id" value={n.id} />
            <input
              name="name"
              use:focusOnMount
              value={n.name}
              onkeydown={(e) => e.key === 'Escape' && (mode = 'actions')}
              class="min-w-32 flex-1 rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
            />
            <button
              type="submit"
              class="rounded border border-slate-900 bg-slate-900 px-2.5 py-1 text-xs text-white hover:bg-slate-800"
              >save</button
            >
            <button
              type="button"
              onclick={() => (mode = 'actions')}
              class="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
              >cancel</button
            >
          </form>
        {:else if mode === 'add'}
          <form
            method="POST"
            action="?/create"
            use:enhance={handleSubmit}
            class="inline-flex flex-wrap items-center gap-1.5"
          >
            <input type="hidden" name="parent_id" value={n.id} />
            <input
              name="name"
              use:focusOnMount
              placeholder="new subcategory…"
              onkeydown={(e) => e.key === 'Escape' && (mode = 'actions')}
              class="min-w-32 flex-1 rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
            />
            <button
              type="submit"
              class="rounded border border-slate-900 bg-slate-900 px-2.5 py-1 text-xs text-white hover:bg-slate-800"
              >add</button
            >
            <button
              type="button"
              onclick={() => (mode = 'actions')}
              class="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
              >cancel</button
            >
          </form>
        {:else if mode === 'confirm-delete'}
          <form
            method="POST"
            action="?/delete"
            use:enhance={handleSubmit}
            class="inline-flex flex-wrap items-center gap-1.5"
          >
            <input type="hidden" name="id" value={n.id} />
            <span class="px-1 text-xs text-slate-600">
              delete <strong class="font-medium text-slate-900">{n.name}</strong>?
            </span>
            <button
              type="submit"
              class="rounded border border-rose-600 bg-rose-600 px-2.5 py-1 text-xs text-white hover:bg-rose-700"
              >yes</button
            >
            <button
              type="button"
              onclick={() => (mode = 'actions')}
              class="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 hover:bg-slate-50"
              >no</button
            >
          </form>
        {/if}
      </div>
    {/if}

    {#if hasChildren}
      <ul class="children">
        {#each n.children as child, i (child.id)}
          {@render row(child, kind, depth + 1, i === n.children.length - 1)}
        {/each}
      </ul>
    {/if}
  </li>
{/snippet}

<style>
  /* Tree connectors — kept in scoped CSS because Tailwind can't express the
   ::before / ::after trunk-and-twig pattern (with masking on the last sibling). */
  .tree,
  .children {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .children {
    margin-top: 0.2rem;
    margin-left: 0.225rem;
  }

  .row {
    position: relative;
    padding: 0.15rem 0 0.15rem 1.25rem;
  }
  .row.depth-1 {
    padding-left: 0;
    margin-top: 0.5rem;
  }
  .row.depth-1:first-child {
    margin-top: 0;
  }
  .row.depth-1 > .children {
    margin-left: 0.6rem;
  }

  .row.depth-2::before,
  .row.depth-3::before,
  .row.depth-4::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    border-left: 1.5px solid #e2e8f0;
  }
  .row.depth-2::after,
  .row.depth-3::after,
  .row.depth-4::after {
    content: '';
    position: absolute;
    left: 0;
    top: 0.85rem;
    width: 0.9rem;
    border-top: 1.5px solid #e2e8f0;
  }
  .row.last.depth-2::before,
  .row.last.depth-3::before,
  .row.last.depth-4::before {
    bottom: auto;
    height: 0.85rem;
  }

  /* Bullets — depth-based sizing/opacity. */
  .bullet {
    display: inline-block;
    flex-shrink: 0;
    border-radius: 9999px;
  }
  .bullet.depth-1 {
    width: 0.5rem;
    height: 0.5rem;
  }
  .bullet.depth-2 {
    width: 0.45rem;
    height: 0.45rem;
    opacity: 0.7;
  }
  .bullet.depth-3,
  .bullet.depth-4 {
    width: 0.35rem;
    height: 0.35rem;
    opacity: 0.5;
  }
  .bullet.kind-income {
    background: #059669;
  }
  .bullet.kind-expense {
    background: #e11d48;
  }
</style>
