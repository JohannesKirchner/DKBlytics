// Pure helpers for the Budget page: money formatting, SVG sankey/line/donut
// geometry, and a transformer from the `/api/budget/sankey` payload into a
// render-ready view (columns + colors).

const moneyFmt = new Intl.NumberFormat('de-DE', {
	style: 'currency',
	currency: 'EUR',
	maximumFractionDigits: 0
});
export const formatMoney = (v) => moneyFmt.format(v ?? 0);

export const MONTHS = [
	'Jan',
	'Feb',
	'Mar',
	'Apr',
	'May',
	'Jun',
	'Jul',
	'Aug',
	'Sep',
	'Oct',
	'Nov',
	'Dec'
];

// --- colors ----------------------------------------------------------------
const INCOME_PALETTE = ['#0d9488', '#0891b2', '#059669', '#14b8a6', '#22c55e', '#06b6d4'];
const EXPENSE_PALETTE = [
	'#6366f1',
	'#0ea5e9',
	'#f59e0b',
	'#ec4899',
	'#a855f7',
	'#ef4444',
	'#8b5cf6',
	'#f97316',
	'#84cc16',
	'#10b981'
];

// --- API payload -> render-ready view ---------------------------------------
// apiNodes: [{id, label, side, depth, group}], apiLinks: [{source, target, value}]
// Returns { nodes: [{id,label,side,depth,group,col,color,value}], links }.
export function buildSankeyView(apiNodes = [], apiLinks = []) {
	const valueOf = (id) => {
		let out = 0;
		let inn = 0;
		for (const l of apiLinks) {
			if (l.source === id) out += Number(l.value);
			if (l.target === id) inn += Number(l.value);
		}
		return Math.max(out, inn);
	};

	// assign a color per top-level (depth-1) category, separated by side
	const depth1 = apiNodes.filter((n) => n.group && n.group === n.id);
	const groupColor = {};
	let ii = 0;
	let ei = 0;
	for (const n of depth1) {
		if (n.side === 'income') groupColor[n.id] = INCOME_PALETTE[ii++ % INCOME_PALETTE.length];
		else groupColor[n.id] = EXPENSE_PALETTE[ei++ % EXPENSE_PALETTE.length];
	}

	const colorFor = (n) => {
		if (n.id === 'income') return '#0d9488';
		if (n.id === 'expenses') return '#475569';
		if (n.id === 'savings') return '#10b981';
		if (n.id === 'other_in' || n.id === 'other_out') return '#94a3b8';
		return groupColor[n.group] ?? '#94a3b8';
	};

	// column layout: income fans in toward [income], expenses fan out of [expenses]
	const incomeDepths = apiNodes
		.filter((n) => n.side === 'income' && n.id !== 'income' && n.id !== 'savings')
		.map((n) => n.depth);
	const expenseDepths = apiNodes
		.filter((n) => n.side === 'expense' && n.id !== 'expenses')
		.map((n) => n.depth);
	const incomeMax = incomeDepths.length ? Math.max(...incomeDepths) : 1;

	const colFor = (n) => {
		if (n.id === 'income') return incomeMax;
		if (n.id === 'expenses' || n.id === 'savings') return incomeMax + 1;
		if (n.side === 'income') return incomeMax - n.depth;
		return incomeMax + 1 + n.depth; // expense side
	};

	const nodes = apiNodes.map((n) => ({
		id: n.id,
		label: n.label,
		side: n.side,
		depth: n.depth,
		group: n.group,
		col: colFor(n),
		color: colorFor(n),
		value: valueOf(n.id)
	}));
	const links = apiLinks.map((l) => ({
		source: l.source,
		target: l.target,
		value: Number(l.value)
	}));
	return { nodes, links };
}

// Largest top-level expense category (fallback: largest income, else null).
export function pickDefaultNode(view) {
	const top = (side) =>
		view.nodes.filter((n) => n.side === side && n.depth === 1).sort((a, b) => b.value - a.value)[0];
	return top('expense') ?? top('income') ?? null;
}

// Map a node id to the category-series `category_id` query value (or null).
export function seriesCatIdFor(id) {
	if (!id) return null;
	if (id.startsWith('cat:')) return id.slice(4);
	if (id === 'other_in' || id === 'other_out') return 'uncategorized';
	return null; // synthetic core nodes have no single category series
}

// --- minimal sankey layout (no deps) ---------------------------------------
export function layoutSankey(nodes, links, { width, height, nodeWidth = 12, nodePad = 16 }) {
	const byId = new Map(nodes.map((n) => [n.id, { ...n }]));

	const valueOf = (id) => {
		const out = links.filter((l) => l.source === id).reduce((s, l) => s + l.value, 0);
		const inn = links.filter((l) => l.target === id).reduce((s, l) => s + l.value, 0);
		return Math.max(out, inn);
	};
	for (const n of byId.values()) n.value = valueOf(n.id);

	const cols = new Map();
	for (const n of byId.values()) {
		if (!cols.has(n.col)) cols.set(n.col, []);
		cols.get(n.col).push(n);
	}
	const colKeys = [...cols.keys()].sort((a, b) => a - b);

	let scale = Infinity;
	for (const k of colKeys) {
		const arr = cols.get(k);
		const total = arr.reduce((s, n) => s + n.value, 0);
		const avail = height - nodePad * (arr.length - 1);
		if (total > 0) scale = Math.min(scale, avail / total);
	}
	if (!Number.isFinite(scale)) scale = 0;

	const colCount = colKeys.length;
	const xOf = (i) => (colCount <= 1 ? 0 : (i / (colCount - 1)) * (width - nodeWidth));

	colKeys.forEach((k, ci) => {
		const arr = cols.get(k);
		const totalH = arr.reduce((s, n) => s + n.value * scale, 0) + nodePad * (arr.length - 1);
		let y = (height - totalH) / 2;
		const x = xOf(ci);
		for (const n of arr) {
			n.x = x;
			n.y = y;
			n.h = n.value * scale;
			n.w = nodeWidth;
			n._sy = y;
			n._ty = y;
			y += n.h + nodePad;
		}
	});

	const ribbons = links.map((l) => {
		const s = byId.get(l.source);
		const t = byId.get(l.target);
		const w = l.value * scale;
		const sy0 = s._sy;
		s._sy += w;
		const ty0 = t._ty;
		t._ty += w;
		const x0 = s.x + s.w;
		const x1 = t.x;
		const mx = (x0 + x1) / 2;
		const path =
			`M ${x0} ${sy0} C ${mx} ${sy0}, ${mx} ${ty0}, ${x1} ${ty0}` +
			` L ${x1} ${ty0 + w} C ${mx} ${ty0 + w}, ${mx} ${sy0 + w}, ${x0} ${sy0 + w} Z`;
		return { path, color: t.color || s.color, value: l.value, source: l.source, target: l.target };
	});

	return { nodes: [...byId.values()], ribbons };
}

// --- smooth line / area path ----------------------------------------------
export function linePath(values, { width, height, pad = 6 }) {
	if (!values.length) return { d: '', area: '', pts: [] };
	const min = Math.min(...values);
	const max = Math.max(...values);
	const range = max - min || 1;
	const stepX = values.length > 1 ? (width - pad * 2) / (values.length - 1) : 0;
	const pts = values.map((v, i) => [
		pad + i * stepX,
		pad + (1 - (v - min) / range) * (height - pad * 2)
	]);

	let d = `M ${pts[0][0]} ${pts[0][1]}`;
	for (let i = 1; i < pts.length; i++) {
		const [x, y] = pts[i];
		const [px, py] = pts[i - 1];
		const cx = (px + x) / 2;
		d += ` C ${cx} ${py}, ${cx} ${y}, ${x} ${y}`;
	}
	const area = `${d} L ${pts[pts.length - 1][0]} ${height - pad} L ${pts[0][0]} ${height - pad} Z`;
	return { d, area, pts };
}

// --- donut segments --------------------------------------------------------
export function donutSegments(data, { radius = 56 }) {
	const total = data.reduce((s, d) => s + d.value, 0) || 1;
	const C = 2 * Math.PI * radius;
	let acc = 0;
	return data.map((d) => {
		const frac = d.value / total;
		const seg = { ...d, frac, dash: frac * C, gap: C - frac * C, offset: -acc * C };
		acc += frac;
		return seg;
	});
}

// --- y-axis nice ticks -----------------------------------------------------
function niceStep(raw) {
	if (raw <= 0) return 1;
	const pow = Math.pow(10, Math.floor(Math.log10(raw)));
	const f = raw / pow;
	return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * pow;
}

export function yAxisTicks(values, { height, pad }) {
	if (!values.length) return [];
	const min = Math.min(...values);
	const max = Math.max(...values);
	const range = max - min || 1;
	const step = niceStep(range / 3) || 1;
	const ticks = [];
	for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) {
		const yvb = pad + (1 - (v - min) / range) * (height - pad * 2);
		ticks.push({ v, yvb, topPct: (yvb / height) * 100 });
	}
	return ticks;
}
