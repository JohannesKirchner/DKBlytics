// Throwaway mock data + tiny SVG chart helpers for the budget-page design mockups.
// Not wired to the backend — purely to evaluate the visual design.

export const YEARS = [2023, 2024, 2025];

// Average monthly flows (EUR). Full budget Sankey, 6 columns:
//   income subcats -> income cats -> [Income] -> [Expenses] -> expense cats -> expense subcats
//                                    [Income] -> [Savings]
// `side` lets the UI filter income vs. expense panels.
// "Savings" is NOT a category: it is the synthetic delta Income - Expenses.
// "Other" lumps all uncategorized spending.
export const NODES = [
  // --- income subcategories (col 0) ---
  { id: 'base_salary', col: 0, side: 'income', label: 'Base salary', color: '#0d9488' },
  { id: 'bonus', col: 0, side: 'income', label: 'Bonus', color: '#2dd4bf' },
  { id: 'proj_a', col: 0, side: 'income', label: 'Project A', color: '#0891b2' },
  { id: 'proj_b', col: 0, side: 'income', label: 'Project B', color: '#22d3ee' },
  { id: 'dividends', col: 0, side: 'income', label: 'Dividends', color: '#059669' },
  { id: 'interest', col: 0, side: 'income', label: 'Interest', color: '#34d399' },

  // --- income categories (col 1) ---
  { id: 'salary', col: 1, side: 'income', label: 'Salary', color: '#0d9488' },
  { id: 'freelance', col: 1, side: 'income', label: 'Freelance', color: '#0891b2' },
  { id: 'investments', col: 1, side: 'income', label: 'Investments', color: '#059669' },

  // --- Income total (col 2) ---
  { id: 'income', col: 2, side: 'center', label: 'Income', color: '#0d9488' },

  // --- Expenses total + Savings (col 3) ---
  { id: 'expenses', col: 3, side: 'center', label: 'Expenses', color: '#475569' },
  { id: 'savings', col: 3, side: 'income', label: 'Savings', color: '#10b981' },

  // --- expense categories (col 4) ---
  { id: 'housing', col: 4, side: 'expense', label: 'Housing', color: '#6366f1' },
  { id: 'food', col: 4, side: 'expense', label: 'Food', color: '#0ea5e9' },
  { id: 'transport', col: 4, side: 'expense', label: 'Transport', color: '#f59e0b' },
  { id: 'leisure', col: 4, side: 'expense', label: 'Leisure', color: '#ec4899' },
  { id: 'health', col: 4, side: 'expense', label: 'Insurance & Health', color: '#a855f7' },
  { id: 'other', col: 4, side: 'expense', label: 'Other', color: '#94a3b8' },

  // --- expense subcategories (col 5) ---
  { id: 'rent', col: 5, side: 'expense', label: 'Rent', color: '#6366f1' },
  { id: 'utilities', col: 5, side: 'expense', label: 'Utilities', color: '#818cf8' },
  { id: 'internet', col: 5, side: 'expense', label: 'Internet', color: '#a5b4fc' },
  { id: 'groceries', col: 5, side: 'expense', label: 'Groceries', color: '#0ea5e9' },
  { id: 'restaurants', col: 5, side: 'expense', label: 'Restaurants', color: '#38bdf8' },
  { id: 'fuel', col: 5, side: 'expense', label: 'Fuel', color: '#f59e0b' },
  { id: 'transit', col: 5, side: 'expense', label: 'Public transit', color: '#fbbf24' },
  { id: 'car_ins', col: 5, side: 'expense', label: 'Car insurance', color: '#fcd34d' },
  { id: 'subs', col: 5, side: 'expense', label: 'Subscriptions', color: '#ec4899' },
  { id: 'hobbies', col: 5, side: 'expense', label: 'Hobbies', color: '#f472b6' },
  { id: 'travel', col: 5, side: 'expense', label: 'Travel', color: '#f9a8d4' }
];

export const LINKS = [
  // income subcategories -> income categories
  { source: 'base_salary', target: 'salary', value: 3000 },
  { source: 'bonus', target: 'salary', value: 400 },
  { source: 'proj_a', target: 'freelance', value: 400 },
  { source: 'proj_b', target: 'freelance', value: 200 },
  { source: 'dividends', target: 'investments', value: 120 },
  { source: 'interest', target: 'investments', value: 80 },

  // income categories -> Income total
  { source: 'salary', target: 'income', value: 3400 },
  { source: 'freelance', target: 'income', value: 600 },
  { source: 'investments', target: 'income', value: 200 },

  // Income -> Expenses + Savings (core split)
  { source: 'income', target: 'expenses', value: 2850 },
  { source: 'income', target: 'savings', value: 1350 },

  // Expenses total -> expense categories
  { source: 'expenses', target: 'housing', value: 1350 },
  { source: 'expenses', target: 'food', value: 620 },
  { source: 'expenses', target: 'transport', value: 240 },
  { source: 'expenses', target: 'leisure', value: 310 },
  { source: 'expenses', target: 'health', value: 180 },
  { source: 'expenses', target: 'other', value: 150 },

  // expense categories -> expense subcategories
  { source: 'housing', target: 'rent', value: 1100 },
  { source: 'housing', target: 'utilities', value: 180 },
  { source: 'housing', target: 'internet', value: 70 },
  { source: 'food', target: 'groceries', value: 450 },
  { source: 'food', target: 'restaurants', value: 170 },
  { source: 'transport', target: 'fuel', value: 120 },
  { source: 'transport', target: 'transit', value: 60 },
  { source: 'transport', target: 'car_ins', value: 60 },
  { source: 'leisure', target: 'subs', value: 60 },
  { source: 'leisure', target: 'hobbies', value: 150 },
  { source: 'leisure', target: 'travel', value: 100 }
];

export const INCOME_CATS = NODES.filter((n) => n.col === 1);
export const EXPENSE_CATS = NODES.filter((n) => n.col === 4);

export const TOTALS = {
  income: 4200,
  expenses: 2850,
  saved: 1350,
  savingsRate: 0.32
};

const moneyFmt = new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0
});
export const formatMoney = (v) => moneyFmt.format(v ?? 0);

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Years for which we hold (mock) data. Earliest record = 2023-01.
export const YEARS_AVAILABLE = [2023, 2024, 2025];

// Full monthly timeline since the earliest record (for the "over time" panel,
// which always spans all data regardless of the selected period).
export const HISTORY = YEARS_AVAILABLE.flatMap((year) =>
  MONTHS.map((label, monthIdx) => ({ year, monthIdx, label }))
);

// Deterministic pseudo-random monthly series so each category gets a stable wobble.
export function seriesFor(id, base) {
  let seed = [...id].reduce((s, c) => s + c.charCodeAt(0), 0) + 7;
  const rnd = () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
  return MONTHS.map(() => Math.round(base * (0.72 + rnd() * 0.56)));
}

// One value per HISTORY entry, with a gentle upward trend across the years.
export function fullSeriesFor(id, base) {
  let seed = [...id].reduce((s, c) => s + c.charCodeAt(0), 0) + 11;
  const rnd = () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
  return HISTORY.map((_, idx) => {
    const trend = 1 + (idx / HISTORY.length) * 0.18;
    return Math.round(base * trend * (0.75 + rnd() * 0.5));
  });
}

// Deterministic per-(year, month) scaling factor (~0.85–1.15) used so the
// "month" period looks distinct from the yearly average.
export function monthScale(year, monthIdx) {
  let seed = (year * 12 + monthIdx) * 7 + 3;
  seed = (seed * 9301 + 49297) % 233280;
  return 0.85 + (seed / 233280) * 0.3;
}

// Multiplier applied to the (monthly-average) base values for a given period mode.
//   'year'    -> sum over 12 months           (× 12)
//   'avgYear' -> monthly average within a year (× 1)
//   'month'   -> a single month               (× monthScale)
export function periodFactor(mode, year, monthIdx) {
  if (mode === 'year') return 12;
  if (mode === 'month') return monthScale(year, monthIdx);
  return 1;
}

export function periodLabel(mode, year, monthIdx) {
  if (mode === 'year') return `Total ${year}`;
  if (mode === 'month') return `${MONTHS[monthIdx]} ${year}`;
  return `Ø / month · ${year}`;
}

export function nodeById(id) {
  return NODES.find((n) => n.id === id);
}

// Average monthly value of a node = max(inflow, outflow).
export function valueOf(id) {
  const out = LINKS.filter((l) => l.source === id).reduce((s, l) => s + l.value, 0);
  const inn = LINKS.filter((l) => l.target === id).reduce((s, l) => s + l.value, 0);
  return Math.max(out, inn);
}

export const withValues = (list) => list.map((n) => ({ ...n, value: valueOf(n.id) }));

// --- minimal sankey layout (no deps) --------------------------------------
// nodes: [{id, col, label, color}], links: [{source, target, value}]
export function layoutSankey(nodes, links, { width, height, nodeWidth = 13, nodePad = 16 }) {
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

  // single global value->pixel scale, driven by the busiest column
  let scale = Infinity;
  for (const k of colKeys) {
    const arr = cols.get(k);
    const total = arr.reduce((s, n) => s + n.value, 0);
    const avail = height - nodePad * (arr.length - 1);
    scale = Math.min(scale, avail / total);
  }

  const colCount = colKeys.length;
  const xOf = (i) => (colCount === 1 ? 0 : (i / (colCount - 1)) * (width - nodeWidth));

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
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = (width - pad * 2) / (values.length - 1);
  const pts = values.map((v, i) => [pad + i * stepX, pad + (1 - (v - min) / range) * (height - pad * 2)]);

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
  const total = data.reduce((s, d) => s + d.value, 0);
  const C = 2 * Math.PI * radius;
  let acc = 0;
  return data.map((d) => {
    const frac = d.value / total;
    const seg = {
      ...d,
      frac,
      dash: frac * C,
      gap: C - frac * C,
      offset: -acc * C
    };
    acc += frac;
    return seg;
  });
}
