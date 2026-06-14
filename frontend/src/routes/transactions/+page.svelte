<script>
  import { goto } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { tick } from 'svelte';

  let { data } = $props();

  // ---------- filter / pagination state (URL-synced) -----------------------
  let q = $state(data.filters.q ?? '');
  let sort_by = $state(data.filters.sort_by);
  let date_from = $state(data.filters.date_from ?? '');
  let date_to = $state(data.filters.date_to ?? '');
  let account_id = $state(data.filters.account_id ?? '');
  let category = $state(data.filters.category ?? '');
  let limit = $state(data.limit);
  let offset = $state(data.offset);

  function nav() {
    const sp = new URLSearchParams();
    sp.set('limit', String(limit));
    sp.set('offset', String(offset));
    if (q.trim().length >= 2) sp.set('q', q.trim());
    if (sort_by) sp.set('sort_by', sort_by);
    if (date_from) sp.set('date_from', date_from);
    if (date_to) sp.set('date_to', date_to);
    if (category) sp.set('category', category);
    if (account_id) sp.set('account_id', account_id);
    goto(`?${sp.toString()}`, { replaceState: true, noScroll: true, keepfocus: true });
  }

  let qTimer = null;
  $effect(() => {
    const changedQ = (data.filters.q ?? '') !== q;
    const changedWithoutQ = !(
      data.filters.sort_by === sort_by &&
      (data.filters.date_from ?? '') === date_from &&
      (data.filters.date_to ?? '') === date_to &&
      (data.filters.category ?? '') === category &&
      (data.filters.account_id ?? '') === account_id
    );
    const changedPagination = !(data.limit === limit && data.offset === offset);

    clearTimeout(qTimer);
    if (changedPagination) nav();
    if (changedWithoutQ && !changedQ) {
      offset = 0;
      nav();
    } else if (changedQ) {
      offset = 0;
      qTimer = setTimeout(() => {
        offset = 0;
        nav();
      }, 500);
    }
  });

  // ---------- category filter combobox ------------------------------------
  // Replaces the old <select>: a typeahead that still feeds the same
  // `category` value (''=all, 'null'=uncategorized, otherwise a category name).
  function categoryFilterLabel(val) {
    if (val === '' || val == null) return '';
    if (val === 'null') return 'Uncategorized';
    return val;
  }

  let catFilterQuery = $state(categoryFilterLabel(data.filters.category));
  let catFilterOpen = $state(false);
  let catFilterIdx = $state(0);

  const catFilterOptions = $derived([
    { value: '', label: 'All' },
    { value: 'null', label: 'Uncategorized' },
    ...Array.from(new Set(data.categoryNames)).map((c) => ({ value: c, label: c }))
  ]);

  let catFilterMatches = $derived.by(() => {
    const s = catFilterQuery.trim().toLowerCase();
    if (!s) return catFilterOptions;
    return catFilterOptions.filter((o) => o.label.toLowerCase().includes(s));
  });

  $effect(() => {
    catFilterMatches; // dependency
    if (catFilterIdx >= catFilterMatches.length) catFilterIdx = Math.max(0, catFilterMatches.length - 1);
  });

  function selectCategoryFilter(opt) {
    category = opt.value;
    catFilterQuery = opt.value === '' ? '' : opt.label;
    catFilterOpen = false;
  }

  function onCatFilterKey(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      catFilterOpen = true;
      if (catFilterIdx < catFilterMatches.length - 1) catFilterIdx += 1;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (catFilterIdx > 0) catFilterIdx -= 1;
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const opt = catFilterMatches[catFilterIdx];
      if (opt) selectCategoryFilter(opt);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      catFilterOpen = false;
      catFilterQuery = categoryFilterLabel(category);
    }
  }

  function onCatFilterBlur() {
    // Revert the text to the active selection if nothing new was picked.
    catFilterOpen = false;
    catFilterQuery = categoryFilterLabel(category);
  }

  // ---------- inline edit state -------------------------------------------
  let focusedRowId = $state(data.transactions.items[0]?.id ?? null);
  let editingDescId = $state(null);
  let editingCategoryId = $state(null);
  let descDraft = $state('');
  let catQuery = $state('');
  let selectedMatchIdx = $state(0);
  let ruleMode = $state('entity'); // 'entity' | 'entity_text' | 'none'
  let lastError = $state(null);

  // Refs for programmatic submit (Enter inside inputs).
  let descFormEl = $state(null);
  let catFormEl = $state(null);
  let catSearchEl = $state(null);

  // Re-sync focus if data reloads and current focused row disappeared.
  $effect(() => {
    if (
      focusedRowId != null &&
      !data.transactions.items.some((t) => t.id === focusedRowId)
    ) {
      focusedRowId = data.transactions.items[0]?.id ?? null;
    }
  });

  // ---------- typeahead matches -------------------------------------------
  let matches = $derived.by(() => {
    const q = catQuery.trim().toLowerCase();
    if (!q) return data.categories;
    return data.categories.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.parent_path ?? '').toLowerCase().includes(q)
    );
  });

  $effect(() => {
    // Keep selectedMatchIdx in range whenever matches changes.
    matches; // dependency
    if (selectedMatchIdx >= matches.length) selectedMatchIdx = Math.max(0, matches.length - 1);
  });

  const selectedMatch = $derived(matches[selectedMatchIdx] ?? null);

  // If editing the category of a row with no description, skip the
  // entity_text mode in the cycle.
  function nextRuleMode(current, txHasText) {
    const order = txHasText ? ['entity', 'entity_text', 'none'] : ['entity', 'none'];
    const idx = order.indexOf(current);
    return order[(idx + 1) % order.length];
  }

  function ruleModeLabel(mode) {
    if (mode === 'entity') return 'by entity';
    if (mode === 'entity_text') return 'by entity + text';
    return 'one-time';
  }

  // ---------- edit state management ---------------------------------------
  function enterDescEdit(tx) {
    cancelAllEdits();
    editingDescId = tx.id;
    descDraft = tx.text ?? '';
  }

  function enterCategoryEdit(tx) {
    cancelAllEdits();
    editingCategoryId = tx.id;
    catQuery = '';
    selectedMatchIdx = 0;
    ruleMode = 'entity';
    lastError = null;
  }

  function cancelAllEdits() {
    editingDescId = null;
    editingCategoryId = null;
    descDraft = '';
    catQuery = '';
    selectedMatchIdx = 0;
    lastError = null;
  }

  function nextUncategorized(currentId) {
    const items = data.transactions.items;
    const idx = items.findIndex((t) => t.id === currentId);
    for (let i = idx + 1; i < items.length; i++) if (items[i].category == null) return items[i];
    return null;
  }

  // ---------- keyboard navigation -----------------------------------------
  function onWindowKey(e) {
    const t = e.target;
    const inField = t instanceof Element && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA');
    if (inField) return; // let inputs handle their own keys

    const items = data.transactions.items;
    if (items.length === 0) return;
    const idx = items.findIndex((t) => t.id === focusedRowId);
    const focused = items[idx] ?? items[0];

    switch (e.key) {
      case 'j':
      case 'ArrowDown':
        if (idx < items.length - 1) focusedRowId = items[idx + 1].id;
        e.preventDefault();
        break;
      case 'k':
      case 'ArrowUp':
        if (idx > 0) focusedRowId = items[idx - 1].id;
        e.preventDefault();
        break;
      case 'd':
        if (focused) enterDescEdit(focused);
        e.preventDefault();
        break;
      case 'c':
        if (focused) enterCategoryEdit(focused);
        e.preventDefault();
        break;
      case 'u': {
        const next = items.find((t) => t.category == null);
        if (next) focusedRowId = next.id;
        e.preventDefault();
        break;
      }
      case ']':
      case 'ArrowRight':
        if (offset + limit < data.transactions.total) offset = offset + limit;
        e.preventDefault();
        break;
      case '[':
      case 'ArrowLeft':
        if (offset > 0) offset = Math.max(0, offset - limit);
        e.preventDefault();
        break;
      case 'Escape':
        cancelAllEdits();
        break;
    }
  }

  // ---------- description form --------------------------------------------
  function onDescKey(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      cancelAllEdits();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      descFormEl?.requestSubmit();
    }
  }

  function handleDescSubmit() {
    return async ({ update, result }) => {
      await update({ reset: false });
      if (result.type === 'success') {
        cancelAllEdits();
      } else if (result.type === 'failure') {
        lastError = result.data?.error ?? 'Update failed';
      }
    };
  }

  // ---------- category form -----------------------------------------------
  function onCatKey(e, tx) {
    if (e.key === 'Escape') {
      e.preventDefault();
      cancelAllEdits();
    } else if (e.key === 'Tab') {
      e.preventDefault();
      ruleMode = nextRuleMode(ruleMode, !!(tx.text && tx.text.trim()));
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (selectedMatchIdx < matches.length - 1) selectedMatchIdx += 1;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (selectedMatchIdx > 0) selectedMatchIdx -= 1;
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedMatch) catFormEl?.requestSubmit();
    }
  }

  function handleAssignSubmit() {
    const submittedTxId = editingCategoryId;
    return async ({ update, result }) => {
      await update({ reset: false });
      if (result.type === 'success') {
        const next = nextUncategorized(submittedTxId);
        if (next) {
          focusedRowId = next.id;
          await tick();
          enterCategoryEdit(next);
          await tick();
          catSearchEl?.focus();
        } else {
          cancelAllEdits();
        }
      } else if (result.type === 'failure') {
        lastError = result.data?.error ?? 'Assign failed';
      }
    };
  }

  // ---------- formatting helpers ------------------------------------------
  function amountColor(s) {
    return (s ?? '').toString().startsWith('-') ? 'text-rose-700' : 'text-emerald-700';
  }

  // Svelte action: focus (and select) an input when it mounts.
  function focusOnMount(node) {
    node.focus();
    node.select?.();
  }

  const uncategorizedCount = $derived(
    data.transactions.items.filter((t) => t.category == null).length
  );
</script>

<svelte:window onkeydown={onWindowKey} />

<div class="mt-8 mx-10 flex flex-col gap-6">
  <!-- Filter bar (unchanged from the previous design) -->
  <div class="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm">
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
        Search
        <input
          class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-normal text-slate-900 placeholder:text-slate-400 shadow-sm transition focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
          bind:value={q}
          placeholder="min 2 chars"
        />
      </label>

      <label class="relative flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
        Category
        <input
          class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-normal normal-case tracking-normal text-slate-900 placeholder:text-slate-400 shadow-sm transition focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
          bind:value={catFilterQuery}
          onfocus={() => {
            catFilterOpen = true;
            catFilterIdx = 0;
          }}
          oninput={() => {
            catFilterOpen = true;
          }}
          onkeydown={onCatFilterKey}
          onblur={onCatFilterBlur}
          placeholder="All categories"
        />
        {#if catFilterOpen && catFilterMatches.length > 0}
          <ul
            class="absolute left-0 right-0 top-full z-20 mt-1 max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
          >
            {#each catFilterMatches.slice(0, 50) as opt, i (opt.value)}
              <li
                class="cursor-pointer px-3 py-1.5 text-sm font-normal normal-case tracking-normal {i ===
                catFilterIdx
                  ? 'bg-blue-50 text-slate-900'
                  : 'text-slate-700 hover:bg-slate-50'}"
                onmousedown={(e) => {
                  e.preventDefault();
                  selectCategoryFilter(opt);
                }}
              >
                {opt.label}
              </li>
            {/each}
          </ul>
        {/if}
      </label>

      <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
        Sort
        <select
          class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
          bind:value={sort_by}
        >
          <option value="date_desc">Date ↓</option>
          <option value="date_asc">Date ↑</option>
          <option value="amount_desc">Amount ↓</option>
          <option value="amount_asc">Amount ↑</option>
        </select>
      </label>

      <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
        From
        <input
          class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
          type="date"
          bind:value={date_from}
        />
      </label>

      <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
        To
        <input
          class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
          type="date"
          bind:value={date_to}
        />
      </label>

      <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
        Account
        <select
          class="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-500 focus:outline-none"
          bind:value={account_id}
        >
          <option value="">All</option>
          {#each data.accounts as a}
            <option value={a.id}>{a.name}</option>
          {/each}
        </select>
      </label>
    </div>
  </div>

  <!-- Context strip -->
  <div class="flex items-center justify-between text-xs text-slate-500">
    <div>
      Click any cell to edit. <kbd class="rounded border border-slate-300 bg-white px-1">↵</kbd> save ·
      <kbd class="rounded border border-slate-300 bg-white px-1">Tab</kbd> cycle rule ·
      <kbd class="rounded border border-slate-300 bg-white px-1">Esc</kbd> cancel ·
      <kbd class="rounded border border-slate-300 bg-white px-1">j</kbd>/<kbd class="rounded border border-slate-300 bg-white px-1">k</kbd>
      row · <kbd class="rounded border border-slate-300 bg-white px-1">d</kbd> desc ·
      <kbd class="rounded border border-slate-300 bg-white px-1">c</kbd> category ·
      <kbd class="rounded border border-slate-300 bg-white px-1">u</kbd> next uncategorized ·
      <kbd class="rounded border border-slate-300 bg-white px-1">←</kbd>/<kbd class="rounded border border-slate-300 bg-white px-1">→</kbd>
      page
    </div>
    <div><strong>{uncategorizedCount}</strong> uncategorized on this page</div>
  </div>

  {#if lastError}
    <div class="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800" role="alert">
      {lastError}
    </div>
  {/if}

  <!-- Table -->
  <table class="w-full table-fixed border-separate border-spacing-0 rounded-2xl bg-white text-sm shadow-sm">
    <thead class="bg-slate-100 text-left text-xs font-bold uppercase tracking-wide text-slate-600">
      <tr>
        <th class="w-24 px-4 py-2.5 border-b border-slate-200 rounded-tl-2xl">Date</th>
        <th class="w-24 px-4 py-2.5 border-b border-slate-200">Account</th>
        <th class="w-40 px-4 py-2.5 border-b border-slate-200">Sender/Recipient</th>
        <th class="px-4 py-2.5 border-b border-slate-200">Description</th>
        <th class="w-56 px-4 py-2.5 border-b border-slate-200">Category</th>
        <th class="w-28 px-4 py-2.5 border-b border-slate-200 text-right rounded-tr-2xl">Amount</th>
      </tr>
    </thead>
    <tbody>
      {#each data.transactions.items as t, i (t.id)}
        {@const inDesc = editingDescId === t.id}
        {@const inCat = editingCategoryId === t.id}
        {@const isFocused = focusedRowId === t.id}
        {@const isLast = i === data.transactions.items.length - 1}
        <tr
          class="border-b border-slate-100 {inDesc || inCat
            ? 'bg-blue-50/50'
            : isFocused
              ? 'bg-slate-50'
              : 'hover:bg-slate-50'}"
        >
          <td class="whitespace-nowrap px-4 py-2 text-slate-700 border-b border-slate-100 {isLast ? 'rounded-bl-2xl' : ''}">{t.date}</td>
          <td class="truncate px-4 py-2 text-slate-700 border-b border-slate-100">{t.account_name}</td>
          <td class="truncate px-4 py-2 text-slate-900 border-b border-slate-100">{t.entity}</td>

          <!-- Description cell -->
          <td class="px-4 py-2 border-b border-slate-100">
            {#if inDesc}
              <form
                bind:this={descFormEl}
                method="POST"
                action="?/updateText"
                use:enhance={handleDescSubmit}
                class="relative"
              >
                <input type="hidden" name="id" value={t.id} />
                <input
                  name="text"
                  class="w-full rounded-md border border-blue-400 bg-white px-2 py-1 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                  bind:value={descDraft}
                  onkeydown={onDescKey}
                  use:focusOnMount
                  placeholder="add a note…"
                />
              </form>
            {:else if t.text}
              <button
                class="block w-full truncate text-left text-xs text-slate-500 hover:text-slate-900"
                onclick={() => enterDescEdit(t)}
              >
                {t.text}
              </button>
            {:else}
              <button
                class="text-xs italic text-slate-400 hover:text-slate-700"
                onclick={() => enterDescEdit(t)}
              >
                + add note
              </button>
            {/if}
          </td>

          <!-- Category cell -->
          <td class="px-4 py-2 border-b border-slate-100">
            {#if inCat}
              <form
                bind:this={catFormEl}
                method="POST"
                action="?/assignCategory"
                use:enhance={handleAssignSubmit}
                class="relative"
              >
                <input type="hidden" name="transaction_id" value={t.id} />
                <input type="hidden" name="entity" value={t.entity ?? ''} />
                <input type="hidden" name="text" value={t.text ?? ''} />
                <input type="hidden" name="category_id" value={selectedMatch?.id ?? ''} />
                <input type="hidden" name="rule_mode" value={ruleMode} />

                <input
                  bind:this={catSearchEl}
                  bind:value={catQuery}
                  onkeydown={(e) => onCatKey(e, t)}
                  use:focusOnMount
                  class="w-full rounded-md border border-blue-400 bg-white px-2.5 py-1 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder="type to filter…"
                />

                <div class="absolute z-10 mt-1 w-[28rem] rounded-md border border-slate-200 bg-white shadow-lg">
                  <div class="border-b border-slate-100 px-2.5 py-1.5 text-[11px] text-slate-500">
                    {matches.length} match{matches.length === 1 ? '' : 'es'} · ↑↓ navigate · ↵ assign
                  </div>
                  <ul class="max-h-64 overflow-y-auto py-1">
                    {#each matches.slice(0, 8) as m, i (m.id)}
                      <li
                        class="flex items-center justify-between px-2.5 py-1 text-sm cursor-pointer {i ===
                        selectedMatchIdx
                          ? 'bg-blue-50'
                          : 'hover:bg-slate-50'}"
                        onmousedown={(e) => {
                          e.preventDefault();
                          selectedMatchIdx = i;
                          catFormEl?.requestSubmit();
                        }}
                      >
                        <span class="flex items-center gap-2 min-w-0">
                          <span
                            class="inline-block w-1.5 h-1.5 rounded-full {m.kind === 'income'
                              ? 'bg-emerald-500'
                              : 'bg-rose-500'}"
                          ></span>
                          <span class="font-medium text-slate-900 truncate">{m.name}</span>
                        </span>
                        <span class="text-[11px] text-slate-400 ml-3 shrink-0">{m.parent_path}</span>
                      </li>
                    {/each}
                    {#if matches.length === 0}
                      <li class="px-2.5 py-2 text-xs italic text-slate-400">no match</li>
                    {/if}
                  </ul>

                  <!-- Rule schema cycle footer -->
                  <div class="border-t border-slate-100 bg-slate-50/60 px-2.5 py-2 text-xs">
                    <div class="mb-1.5 flex items-center justify-between">
                      <span class="text-[11px] uppercase tracking-wider text-slate-500">On ↵ also save…</span>
                      <span class="text-[10px] text-slate-400">
                        <kbd class="rounded border border-slate-300 bg-white px-1">Tab</kbd> to cycle
                      </span>
                    </div>
                    <div class="flex gap-1">
                      <span
                        class="rounded-md border px-2 py-0.5 text-xs {ruleMode === 'entity'
                          ? 'border-slate-900 bg-slate-900 text-white'
                          : 'border-slate-200 bg-white text-slate-600'}"
                      >
                        by entity
                      </span>
                      {#if t.text && t.text.trim()}
                        <span
                          class="rounded-md border px-2 py-0.5 text-xs {ruleMode === 'entity_text'
                            ? 'border-slate-900 bg-slate-900 text-white'
                            : 'border-slate-200 bg-white text-slate-600'}"
                        >
                          by entity + text
                        </span>
                      {/if}
                      <span
                        class="rounded-md border px-2 py-0.5 text-xs {ruleMode === 'none'
                          ? 'border-slate-900 bg-slate-900 text-white'
                          : 'border-slate-200 bg-white text-slate-600'}"
                      >
                        one-time
                      </span>
                    </div>
                    <div class="mt-1.5 text-[11px] text-slate-500">
                      {#if ruleMode === 'entity'}
                        Future transactions from <strong class="text-slate-700">"{t.entity}"</strong> auto-categorize.
                      {:else if ruleMode === 'entity_text'}
                        Future transactions from <strong class="text-slate-700">"{t.entity}"</strong> with description
                        <strong class="text-slate-700">"{t.text}"</strong> auto-categorize.
                      {:else}
                        No rule — just this transaction.
                      {/if}
                    </div>
                  </div>
                </div>
              </form>
            {:else if t.category}
              <button
                class="rounded-md px-2 py-0.5 text-sm text-slate-700 hover:bg-slate-100"
                onclick={() => enterCategoryEdit(t)}
              >
                {t.category}
              </button>
            {:else}
              <button
                class="rounded-md px-2 py-0.5 text-sm italic text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                onclick={() => enterCategoryEdit(t)}
              >
                + assign…
              </button>
            {/if}
          </td>

          <td class="px-4 py-2 text-right font-semibold border-b border-slate-100 {amountColor(t.amount)} {isLast ? 'rounded-br-2xl' : ''}">
            {t.amount}
          </td>
        </tr>
      {/each}
      {#if data.transactions.items.length === 0}
        <tr>
          <td colspan="6" class="px-4 py-8 text-center text-slate-400 italic">No transactions match the current filters.</td>
        </tr>
      {/if}
    </tbody>
  </table>

  <!-- Pagination -->
  <div class="mt-2 flex items-center justify-end gap-3">
    <button
      class="inline-flex items-center rounded-full border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-300"
      onclick={() => (offset = Math.max(0, offset - limit))}
      disabled={offset === 0}
    >
      Prev
    </button>

    <p class="text-sm text-gray-600 whitespace-nowrap">
      Page <span class="font-semibold">{Math.floor(offset / limit) + 1}</span>
      of <span class="font-semibold">{Math.max(1, Math.ceil(data.transactions.total / limit))}</span>
      <span class="text-gray-400 mx-1">•</span>
      <span class="text-gray-500">({data.transactions.total} total)</span>
    </p>

    <button
      class="inline-flex items-center rounded-full border border-slate-900/80 bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-200"
      onclick={() => (offset = offset + limit)}
      disabled={offset + limit >= data.transactions.total}
    >
      Next
    </button>
  </div>
</div>

