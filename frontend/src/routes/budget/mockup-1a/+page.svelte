<script>
  import {
    NODES,
    LINKS,
    YEARS_AVAILABLE,
    HISTORY,
    TOTALS,
    EXPENSE_CATS,
    MONTHS,
    formatMoney,
    layoutSankey,
    linePath,
    donutSegments,
    fullSeriesFor,
    periodFactor,
    periodLabel,
    nodeById,
    valueOf,
    withValues
  } from '$lib/budgetMock.js';

  let mode = $state('avgYear'); // 'year' | 'avgYear' | 'month'
  let year = $state(2025);
  let monthIdx = $state(5);
  let selected = $state('food');

  // --- sankey (measured to fill its panel) ---------------------------------
  const PADL = 80;
  const PADR = 124;
  const PADV = 14;
  let boxW = $state(0);
  let boxH = $state(0);

  const layout = $derived(
    boxW > 0 && boxH > 0
      ? layoutSankey(NODES, LINKS, { width: boxW - PADL - PADR, height: boxH - PADV * 2, nodeWidth: 12, nodePad: 16 })
      : { nodes: [], ribbons: [] }
  );

  function labelPos(n) {
    if (n.col === 0) return { x: n.x - 8, y: n.y + n.h / 2, anchor: 'end' };
    return { x: n.x + n.w + 7, y: n.y + n.h / 2, anchor: 'start' };
  }

  // --- period scaling -------------------------------------------------------
  const factor = $derived(periodFactor(mode, year, monthIdx));
  const sel = $derived({ ...nodeById(selected), value: valueOf(selected) });
  const selPeriodValue = $derived(sel.value * factor);

  // --- time series: ALWAYS the full history since the earliest record -------
  const CH = 200; // chart viewBox height
  const CPAD = 10; // chart vertical padding (matches linePath)
  const history = $derived(fullSeriesFor(selected, sel.value));
  const line = $derived(linePath(history, { width: 600, height: CH, pad: CPAD }));
  const yearTicks = $derived(
    YEARS_AVAILABLE.map((y) => {
      const idx = HISTORY.findIndex((h) => h.year === y);
      return { year: y, x: line.pts[idx]?.[0] ?? 0 };
    })
  );

  // y-axis: nice rounded gridlines between the series min/max.
  function niceStep(raw) {
    const pow = Math.pow(10, Math.floor(Math.log10(raw)));
    const f = raw / pow;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * pow;
  }
  const yTicks = $derived.by(() => {
    const min = Math.min(...history);
    const max = Math.max(...history);
    const range = max - min || 1;
    const step = niceStep(range / 3) || 1;
    const ticks = [];
    for (let v = Math.ceil(min / step) * step; v <= max; v += step) {
      const yvb = CPAD + (1 - (v - min) / range) * (CH - CPAD * 2);
      ticks.push({ v, yvb, topPct: (yvb / CH) * 100 });
    }
    return ticks;
  });

  // --- composition (scaled to the selected period) --------------------------
  const expCats = $derived(withValues(EXPENSE_CATS).map((c) => ({ ...c, value: c.value * factor })));
  const donut = $derived(donutSegments(expCats, { radius: 80 }));
  const expensesTotal = $derived(TOTALS.expenses * factor);
</script>

<div class="flex flex-col gap-4 bg-slate-50 p-4 text-slate-800" style="height: calc(100vh - 48px);">
  <!-- header -->
  <div class="flex items-center justify-between px-1">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight text-slate-900">Budget</h1>
      <p class="text-sm text-slate-500">{periodLabel(mode, year, monthIdx)}</p>
    </div>
    <div class="flex items-center gap-3">
      <div class="flex rounded-xl border border-slate-200 bg-white p-1 text-sm shadow-sm">
        {#each [['year', 'Year'], ['avgYear', 'Ø / month'], ['month', 'Month']] as [m, label]}
          <button
            class="rounded-lg px-3 py-1 transition {mode === m ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-800'}"
            onclick={() => (mode = m)}>{label}</button>
        {/each}
      </div>
      {#if mode === 'month'}
        <select
          bind:value={monthIdx}
          class="rounded-xl border border-slate-200 bg-white px-3 py-[7px] text-sm shadow-sm focus:outline-none">
          {#each MONTHS as mm, i}<option value={i}>{mm}</option>{/each}
        </select>
      {/if}
      <div class="flex rounded-xl border border-slate-200 bg-white p-1 text-sm shadow-sm">
        {#each YEARS_AVAILABLE as y}
          <button
            class="rounded-lg px-3 py-1 transition {year === y ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-800'}"
            onclick={() => (year = y)}>{y}</button>
        {/each}
      </div>
    </div>
  </div>

  <!-- body -->
  <div class="flex min-h-0 flex-1 gap-4">
    <!-- Sankey -->
    <section class="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm" style="flex: 0 0 55%; min-width: 0;">
      <div class="mb-1 flex items-center justify-between px-1">
        <h2 class="text-sm font-semibold text-slate-900">Income → Expenses + Savings</h2>
        <span class="text-xs text-slate-400">hover any flow →</span>
      </div>
      <div class="min-h-0 w-full flex-1" bind:clientWidth={boxW} bind:clientHeight={boxH}>
        <svg width={boxW} height={boxH} class="block">
          <g transform="translate({PADL},{PADV})">
            {#each layout.ribbons as r}
              <path d={r.path} fill={r.color}
                fill-opacity={selected === r.source || selected === r.target ? 0.55 : 0.26}
                class="cursor-pointer transition-all" onmouseenter={() => (selected = r.target)} role="presentation" />
            {/each}
            {#each layout.nodes as n}
              {@const p = labelPos(n)}
              <rect x={n.x} y={n.y} width={n.w} height={Math.max(n.h, 1)} rx="2.5" fill={n.color}
                class="cursor-pointer" onmouseenter={() => (selected = n.id)} role="presentation" />
              <text x={p.x} y={p.y} text-anchor={p.anchor} dominant-baseline="middle" paint-order="stroke"
                stroke="white" stroke-width="3.5"
                class="fill-slate-600 text-[12px] {selected === n.id ? 'font-semibold' : ''}">{n.label}</text>
            {/each}
          </g>
        </svg>
      </div>
    </section>

    <!-- right column -->
    <div class="flex min-h-0 flex-col gap-4" style="flex: 1 1 0; min-width: 0;">
      <!-- time series: full history -->
      <section class="flex min-h-0 flex-[2] flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="h-2.5 w-2.5 rounded-full" style="background:{sel.color}"></span>
            <h2 class="text-sm font-semibold text-slate-900">{sel.label} over time</h2>
          </div>
          <span class="text-sm font-semibold text-slate-900">{formatMoney(selPeriodValue)}</span>
        </div>
        <p class="mb-1 text-xs text-slate-400">
          full history since {MONTHS[HISTORY[0].monthIdx]} {HISTORY[0].year}
        </p>
        <div class="flex min-h-0 w-full flex-1 gap-2">
          <!-- y axis (mirrors chart height so labels align with gridlines) -->
          <div class="flex shrink-0 flex-col" style="width: 52px;">
            <div class="relative min-h-0 flex-1">
              {#each yTicks as t}
                <span class="absolute right-0 -translate-y-1/2 text-[10px] tabular-nums text-slate-400"
                  style="top:{t.topPct}%">{formatMoney(t.v)}</span>
              {/each}
            </div>
            <div class="mt-1 h-3"></div>
          </div>
          <!-- chart -->
          <div class="flex min-w-0 flex-1 flex-col">
            <div class="relative min-h-0 flex-1">
              <svg viewBox="0 0 600 {CH}" preserveAspectRatio="none" class="h-full w-full">
                {#each yTicks as t}
                  <line x1="0" y1={t.yvb} x2="600" y2={t.yvb} stroke="#f1f5f9" stroke-width="1" vector-effect="non-scaling-stroke" />
                {/each}
                {#each yearTicks as t}
                  <line x1={t.x} y1="0" x2={t.x} y2={CH} stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3" vector-effect="non-scaling-stroke" />
                {/each}
                <path d={line.area} fill={sel.color} fill-opacity="0.10" />
                <path d={line.d} fill="none" stroke={sel.color} stroke-width="2" vector-effect="non-scaling-stroke" />
              </svg>
            </div>
            <div class="relative mt-1 h-3 text-[10px] text-slate-400">
              {#each yearTicks as t}
                <span class="absolute -translate-x-1/2" style="left:{(t.x / 600) * 100}%">{t.year}</span>
              {/each}
            </div>
          </div>
        </div>
      </section>

      <!-- expense composition: large pie filling the panel -->
      <section class="flex min-h-0 flex-[3] flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 class="mb-2 text-sm font-semibold text-slate-900">Expense composition</h2>
        <div class="flex min-h-0 flex-1 items-center gap-5">
          <svg viewBox="0 0 200 200" class="shrink-0 -rotate-90" style="height: 140px; width: 140px;">
            {#each donut as s}
              <circle cx="100" cy="100" r="80" fill="none" stroke={s.color} stroke-width="28"
                stroke-dasharray="{s.dash} {s.gap}" stroke-dashoffset={s.offset} />
            {/each}
            <text x="100" y="100" class="rotate-90 fill-slate-900 text-[16px] font-semibold" text-anchor="middle"
              dominant-baseline="middle" transform="rotate(90 100 100)">{formatMoney(expensesTotal)}</text>
          </svg>
          <ul class="min-w-0 flex-1 space-y-2 text-sm">
            {#each donut as s}
              <li class="flex items-center justify-between">
                <span class="flex items-center gap-2">
                  <span class="h-2.5 w-2.5 rounded-full" style="background:{s.color}"></span>{s.label}
                </span>
                <span class="tabular-nums text-slate-500">{formatMoney(s.value)} · {Math.round(s.frac * 100)}%</span>
              </li>
            {/each}
          </ul>
        </div>
      </section>
    </div>
  </div>
</div>
