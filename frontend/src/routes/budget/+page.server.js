const MODES = new Set(['year', 'avgYear', 'month']);

export async function load({ fetch, url }) {
	const sp = url.searchParams;

	let mode = sp.get('mode') || 'avgYear';
	if (!MODES.has(mode)) mode = 'avgYear';

	const account_id = sp.get('account_id') || null;

	// --- accounts --------------------------------------------------------------
	const accRes = await fetch('/api/accounts/');
	if (!accRes.ok) throw new Error('Failed to load accounts');
	const accounts = (await accRes.json()).map((a) => ({ id: a.public_id, name: a.name }));

	// --- available years (from the full-history span) --------------------------
	const spanParams = new URLSearchParams({ category_id: 'uncategorized' });
	if (account_id) spanParams.set('account_id', account_id);
	const spanRes = await fetch(`/api/budget/category-series?${spanParams.toString()}`);
	const span = spanRes.ok ? await spanRes.json() : [];
	const years = [...new Set(span.map((p) => Number(p.date.slice(0, 4))))].sort((a, b) => a - b);
	const latestYear = years.length ? years[years.length - 1] : new Date().getFullYear();

	let year = Number(sp.get('year'));
	if (!Number.isFinite(year) || (years.length && !years.includes(year))) year = latestYear;

	let monthIdx = sp.get('month') != null ? Number(sp.get('month')) : 5;
	if (!Number.isInteger(monthIdx) || monthIdx < 0 || monthIdx > 11) monthIdx = 5;

	// --- sankey for the selected period ---------------------------------------
	const { from, to } = rangeFor(mode, year, monthIdx);
	const sankeyParams = new URLSearchParams({ date_from: from, date_to: to });
	if (account_id) sankeyParams.set('account_id', account_id);
	const sankeyRes = await fetch(`/api/budget/sankey?${sankeyParams.toString()}`);
	if (!sankeyRes.ok) throw new Error('Failed to load budget sankey');
	const sankey = await sankeyRes.json();

	return {
		accounts,
		years: years.length ? years : [latestYear],
		sankey,
		filters: { mode, year, monthIdx, account_id }
	};
}

function rangeFor(mode, year, monthIdx) {
	if (mode === 'month') {
		const mm = String(monthIdx + 1).padStart(2, '0');
		const lastDay = new Date(year, monthIdx + 1, 0).getDate();
		return { from: `${year}-${mm}-01`, to: `${year}-${mm}-${String(lastDay).padStart(2, '0')}` };
	}
	// year + avgYear both query the full calendar year
	return { from: `${year}-01-01`, to: `${year}-12-31` };
}
