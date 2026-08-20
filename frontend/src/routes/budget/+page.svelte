<script>
	import { goto } from '$app/navigation';
	import {
		formatMoney,
		MONTHS,
		buildSankeyView,
		pickDefaultNode,
		seriesCatIdFor,
		layoutSankey,
		linePath,
		donutSegments,
		yAxisTicks
	} from '$lib/budget.js';

	const { data } = $props();

	// --- period filters (URL-synced) ------------------------------------------
	let mode = $state(data.filters.mode);
	let year = $state(data.filters.year);
	let monthIdx = $state(data.filters.monthIdx);
	let account_id = $state(data.filters.account_id ?? '');

	$effect(() => {
		const f = data.filters;
		const changed =
			f.mode !== mode ||
			f.year !== year ||
			f.monthIdx !== monthIdx ||
			(f.account_id ?? '') !== (account_id || '');
		if (!changed) return;
		const sp = new URLSearchParams();
		sp.set('mode', mode);
		sp.set('year', String(year));
		if (mode === 'month') sp.set('month', String(monthIdx));
		if (account_id) sp.set('account_id', account_id);
		goto(`?${sp.toString()}`, { replaceState: true, noScroll: true, keepFocus: true });
	});

	// --- sankey view ----------------------------------------------------------
	const view = $derived(buildSankeyView(data.sankey.nodes, data.sankey.links));
	const monthsWithData = $derived(data.sankey.meta?.months_with_data ?? 0);
	const factor = $derived(mode === 'avgYear' ? (monthsWithData ? 1 / monthsWithData : 0) : 1);

	const periodLabel = $derived(
		mode === 'year'
			? `Total ${year}`
			: mode === 'month'
				? `${MONTHS[monthIdx]} ${year}`
				: `Ø / month · ${year}`
	);

	// --- selection (drives the time series) -----------------------------------
	let selected = $state(null);
	let seriesCatId = $state(null);
	let seriesLabel = $state('');
	let seriesColor = $state('#0d9488');
	let series = $state([]);

	function selectNode(id) {
		selected = id;
		const cid = seriesCatIdFor(id);
		if (cid) {
			const node = view.nodes.find((n) => n.id === id);
			seriesCatId = cid;
			seriesLabel = node?.label ?? '';
			seriesColor = node?.color ?? '#0d9488';
		}
	}

	// default selection when the view (re)loads and nothing valid is selected
	$effect(() => {
		const stillThere = selected && view.nodes.some((n) => n.id === selected);
		if (!stillThere) {
			const def = pickDefaultNode(view);
			if (def) selectNode(def.id);
		}
	});

	// fetch the full-history series whenever the selected category changes
	$effect(() => {
		if (!seriesCatId) return;
		const cid = seriesCatId;
		const params = new URLSearchParams({ category_id: cid, granularity: 'monthly' });
		if (account_id) params.set('account_id', account_id);
		fetch(`/api/budget/category-series?${params.toString()}`)
			.then((r) => (r.ok ? r.json() : []))
			.then((d) => {
				if (seriesCatId === cid) series = d.map((p) => ({ date: p.date, value: Number(p.value) }));
			})
			.catch(() => {});
	});

	// --- sankey geometry (measured to fill its panel) -------------------------
	const PADL = 98;
	const PADR = 130;
	const PADV = 14;
	let boxW = $state(0);
	let boxH = $state(0);

	const layout = $derived(
		boxW > 0 && boxH > 0 && view.nodes.length
			? layoutSankey(view.nodes, view.links, {
					width: boxW - PADL - PADR,
					height: boxH - PADV * 2,
					nodeWidth: 12,
					nodePad: 16
				})
			: { nodes: [], ribbons: [] }
	);

	function labelPos(n) {
		if (n.col === 0) return { x: n.x - 8, y: n.y + n.h / 2, anchor: 'end' };
		return { x: n.x + n.w + 7, y: n.y + n.h / 2, anchor: 'start' };
	}

	// --- selected headline value (period) -------------------------------------
	const selNode = $derived(view.nodes.find((n) => n.id === selected));
	const selValue = $derived((selNode?.value ?? 0) * factor);

	// --- time series geometry -------------------------------------------------
	const CH = 200;
	const CPAD = 10;
	const history = $derived(series.map((p) => p.value));
	const line = $derived(linePath(history, { width: 600, height: CH, pad: CPAD }));
	const yTicks = $derived(yAxisTicks(history, { height: CH, pad: CPAD }));
	const yearTicks = $derived.by(() => {
		const seen = new Set();
		const ticks = [];
		series.forEach((p, i) => {
			const y = p.date.slice(0, 4);
			if (!seen.has(y)) {
				seen.add(y);
				ticks.push({ year: Number(y), x: line.pts[i]?.[0] ?? 0 });
			}
		});
		return ticks;
	});

	// --- expense composition donut --------------------------------------------
	const expenseTop = $derived(
		view.nodes
			.filter((n) => n.side === 'expense' && n.depth === 1)
			.map((n) => ({ label: n.label, color: n.color, value: n.value * factor }))
			.sort((a, b) => b.value - a.value)
	);
	const donut = $derived(donutSegments(expenseTop, { radius: 80 }));
	const expensesTotal = $derived((data.sankey.totals?.expenses ?? 0) * factor);

	const hasData = $derived(view.nodes.length > 0);
</script>

<div class="flex flex-col gap-4 bg-slate-50 p-4 text-slate-800" style="height: calc(100vh - 48px);">
	<!-- header -->
	<div class="flex items-center justify-between px-1">
		<div>
			<h1 class="text-2xl font-semibold tracking-tight text-slate-900">Budget</h1>
			<p class="text-sm text-slate-500">{periodLabel}</p>
		</div>
		<div class="flex items-center gap-3">
			<div class="flex rounded-xl border border-slate-200 bg-white p-1 text-sm shadow-sm">
				{#each [['year', 'Year'], ['avgYear', 'Ø / month'], ['month', 'Month']] as [m, label]}
					<button
						class="rounded-lg px-3 py-1 transition {mode === m
							? 'bg-slate-900 text-white'
							: 'text-slate-500 hover:text-slate-800'}"
						onclick={() => (mode = m)}>{label}</button
					>
				{/each}
			</div>
			{#if mode === 'month'}
				<select
					bind:value={monthIdx}
					class="rounded-xl border border-slate-200 bg-white px-3 py-[7px] text-sm shadow-sm focus:outline-none"
				>
					{#each MONTHS as mm, i}<option value={i}>{mm}</option>{/each}
				</select>
			{/if}
			<select
				bind:value={year}
				class="rounded-xl border border-slate-200 bg-white px-3 py-[7px] text-sm shadow-sm focus:outline-none"
			>
				{#each data.years as y}<option value={y}>{y}</option>{/each}
			</select>
			{#if data.accounts.length > 1}
				<select
					bind:value={account_id}
					class="rounded-xl border border-slate-200 bg-white px-3 py-[7px] text-sm shadow-sm focus:outline-none"
				>
					<option value="">All accounts</option>
					{#each data.accounts as a}<option value={a.id}>{a.name}</option>{/each}
				</select>
			{/if}
		</div>
	</div>

	<!-- body -->
	<div class="flex min-h-0 flex-1 gap-4">
		<!-- Sankey -->
		<section
			class="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
			style="flex: 0 0 55%; min-width: 0;"
		>
			<div class="mb-1 flex items-center justify-between px-1">
				<h2 class="text-sm font-semibold text-slate-900">Income → Expenses + Savings</h2>
				<span class="text-xs text-slate-400">hover any flow →</span>
			</div>
			<div class="min-h-0 w-full flex-1" bind:clientWidth={boxW} bind:clientHeight={boxH}>
				{#if !hasData}
					<div class="flex h-full items-center justify-center text-sm text-slate-400">
						No transactions in this period.
					</div>
				{:else}
					<svg width={boxW} height={boxH} class="block">
						<g transform="translate({PADL},{PADV})">
							{#each layout.ribbons as r}
								<path
									d={r.path}
									fill={r.color}
									fill-opacity={selected === r.source || selected === r.target ? 0.55 : 0.26}
									class="cursor-pointer transition-all"
									onmouseenter={() => selectNode(r.target)}
									role="presentation"
								/>
							{/each}
							{#each layout.nodes as n}
								{@const p = labelPos(n)}
								<rect
									x={n.x}
									y={n.y}
									width={n.w}
									height={Math.max(n.h, 1)}
									rx="2.5"
									fill={n.color}
									class="cursor-pointer"
									onmouseenter={() => selectNode(n.id)}
									role="presentation"
								/>
								<text
									x={p.x}
									y={p.y}
									text-anchor={p.anchor}
									dominant-baseline="middle"
									paint-order="stroke"
									stroke="white"
									stroke-width="3.5"
									class="fill-slate-600 text-[12px] {selected === n.id ? 'font-semibold' : ''}"
									>{n.label}</text
								>
							{/each}
						</g>
					</svg>
				{/if}
			</div>
		</section>

		<!-- right column -->
		<div class="flex min-h-0 flex-col gap-4" style="flex: 1 1 0; min-width: 0;">
			<!-- time series: full history -->
			<section
				class="flex min-h-0 flex-[2] flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
			>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="h-2.5 w-2.5 rounded-full" style="background:{seriesColor}"></span>
						<h2 class="text-sm font-semibold text-slate-900">
							{seriesLabel || 'Category'} over time
						</h2>
					</div>
					<span class="text-sm font-semibold text-slate-900">{formatMoney(selValue)}</span>
				</div>
				<p class="mb-1 text-xs text-slate-400">
					{#if series.length}full history since {series[0].date.slice(0, 7)}{:else}no history{/if}
				</p>
				{#if series.length}
					<div class="flex min-h-0 w-full flex-1 gap-2">
						<div class="flex shrink-0 flex-col" style="width: 52px;">
							<div class="relative min-h-0 flex-1">
								{#each yTicks as t}
									<span
										class="absolute right-0 -translate-y-1/2 text-[10px] tabular-nums text-slate-400"
										style="top:{t.topPct}%">{formatMoney(t.v)}</span
									>
								{/each}
							</div>
							<div class="mt-1 h-3"></div>
						</div>
						<div class="flex min-w-0 flex-1 flex-col">
							<div class="relative min-h-0 flex-1">
								<svg viewBox="0 0 600 {CH}" preserveAspectRatio="none" class="h-full w-full">
									{#each yTicks as t}
										<line
											x1="0"
											y1={t.yvb}
											x2="600"
											y2={t.yvb}
											stroke="#f1f5f9"
											stroke-width="1"
											vector-effect="non-scaling-stroke"
										/>
									{/each}
									{#each yearTicks as t}
										<line
											x1={t.x}
											y1="0"
											x2={t.x}
											y2={CH}
											stroke="#e2e8f0"
											stroke-width="1"
											stroke-dasharray="3 3"
											vector-effect="non-scaling-stroke"
										/>
									{/each}
									<path d={line.area} fill={seriesColor} fill-opacity="0.10" />
									<path
										d={line.d}
										fill="none"
										stroke={seriesColor}
										stroke-width="2"
										vector-effect="non-scaling-stroke"
									/>
								</svg>
							</div>
							<div class="relative mt-1 h-3 text-[10px] text-slate-400">
								{#each yearTicks as t}
									<span class="absolute -translate-x-1/2" style="left:{(t.x / 600) * 100}%"
										>{t.year}</span
									>
								{/each}
							</div>
						</div>
					</div>
				{:else}
					<div class="flex flex-1 items-center justify-center text-sm text-slate-400">
						Hover a category to see its history.
					</div>
				{/if}
			</section>

			<!-- expense composition -->
			<section
				class="flex min-h-0 flex-[3] flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
			>
				<h2 class="mb-2 text-sm font-semibold text-slate-900">Expense composition</h2>
				{#if expenseTop.length}
					<div class="flex min-h-0 flex-1 items-center gap-5">
						<svg
							viewBox="0 0 200 200"
							class="shrink-0 -rotate-90"
							style="height: 140px; width: 140px;"
						>
							{#each donut as s}
								<circle
									cx="100"
									cy="100"
									r="80"
									fill="none"
									stroke={s.color}
									stroke-width="28"
									stroke-dasharray="{s.dash} {s.gap}"
									stroke-dashoffset={s.offset}
								/>
							{/each}
							<text
								x="100"
								y="100"
								class="rotate-90 fill-slate-900 text-[12px] font-semibold"
								text-anchor="middle"
								dominant-baseline="middle"
								transform="rotate(90 100 100)">{formatMoney(expensesTotal)}</text
							>
						</svg>
						<ul class="min-w-0 flex-1 space-y-1.5 text-xs">
							{#each donut as s}
								<li class="flex items-center justify-between">
									<span class="flex items-center gap-2 truncate">
										<span class="h-2 w-2 shrink-0 rounded-full" style="background:{s.color}"></span>
										<span class="truncate">{s.label}</span>
									</span>
									<span class="shrink-0 tabular-nums text-slate-500"
										>{formatMoney(s.value)} · {Math.round(s.frac * 100)}%</span
									>
								</li>
							{/each}
						</ul>
					</div>
				{:else}
					<div class="flex flex-1 items-center justify-center text-sm text-slate-400">
						No expenses in this period.
					</div>
				{/if}
			</section>
		</div>
	</div>
</div>
