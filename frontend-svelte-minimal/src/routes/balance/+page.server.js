const DATE_RX = /^\d{4}-\d{2}-\d{2}$/;
const RANGE_VALUES = new Set(['30d', '3m', 'ytd', '12m', 'custom']);

export async function load({ fetch, url }) {
  const sp = url.searchParams;

  // --- filters from query ----------------------------------------------------
  let range = sp.get('range') || '3m';
  if (!RANGE_VALUES.has(range)) range = '3m';

  let date_from = validDate(sp.get('date_from')) ? sp.get('date_from') : null;
  let date_to   = validDate(sp.get('date_to'))   ? sp.get('date_to')   : null;

  const today = new Date();
  const todayStr = toYMD(today);

  // derive dates from preset if not custom or custom incomplete
  if (range !== 'custom' || !date_from || !date_to) {
    ({ date_from, date_to } = derivePresetRange(range, today));
  }

  // clamp date_to to today (no future)
  if (date_to > todayStr) {
    date_to = todayStr;
  }

  // just in case: ensure from <= to
  if (date_from > date_to) {
    const tmp = date_from;
    date_from = date_to;
    date_to = tmp;
  }

  const account_id = sp.get('account_id') || null;

  // --- fetch accounts --------------------------------------------------------
  const accRes = await fetch('/api/accounts/');
  if (!accRes.ok) throw new Error('Failed to load accounts');

  const accountsRaw = await accRes.json();
  const accounts = accountsRaw.map((a) => ({
    id: a.public_id,
    name: a.name,
    // backend exposes balance as string; we keep a numeric version here
    balance: Number(a.balance ?? 0)
  }));

  const includedAccounts = account_id
    ? accounts.filter((a) => a.id === account_id)
    : accounts;

  const currentBalance = includedAccounts.reduce(
    (sum, a) => sum + (a.balance || 0),
    0
  );

  // --- fetch transactions for [date_from, today] -----------------------------
  // We always fetch up to "today" so we can back-calculate balances correctly,
  // even if the user chooses a date_to in the past.
  const chartEnd = todayStr;

  let allTx = [];
  const limit = 500;
  let offset = 0;

  const baseParams = new URLSearchParams({
    limit: String(limit),
    offset: '0',
    date_from,
    date_to: chartEnd
  });
  if (account_id) baseParams.set('account_id', account_id);

  while (true) {
    baseParams.set('offset', String(offset));
    const res = await fetch(`/api/transactions/?${baseParams.toString()}`);
    if (!res.ok) throw new Error('Failed to load transactions');

    const page = await res.json();
    const items = page.items ?? [];
    allTx = allTx.concat(items);

    const total = page.total ?? allTx.length;
    offset += limit;

    if (offset >= total || items.length < limit) break;
  }

  // --- build series ----------------------------------------------------------
  const { balanceSeries, monthlySurplus } = buildSeries({
    transactions: allTx,
    dateFrom: date_from,
    displayTo: date_to,
    chartEnd,
    currentBalance
  });

  return {
    accounts: accounts.map((a) => ({ id: a.id, name: a.name })), // no need to expose per-account balance here
    currentBalance,
    balanceSeries,
    monthlySurplus,
    filters: {
      account_id,
      range,
      date_from,
      date_to
    }
  };
}

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function validDate(s) {
  return typeof s === 'string' && DATE_RX.test(s);
}

function toYMD(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function parseYMD(s) {
  const [y, m, d] = s.split('-').map(Number);
  return new Date(y, m - 1, d);
}

function addDays(date, days) {
  const d = new Date(date.getTime());
  d.setDate(d.getDate() + days);
  return d;
}

function addMonths(date, months) {
  const d = new Date(date.getTime());
  d.setMonth(d.getMonth() + months);
  return d;
}

function derivePresetRange(range, today) {
  // default: 3 months
  if (!RANGE_VALUES.has(range) || range === 'custom') {
    range = '3m';
  }

  let from;
  const end = new Date(today.getFullYear(), today.getMonth(), today.getDate()); // strip time

  if (range === '30d') {
    from = addDays(end, -30);
  } else if (range === '3m') {
    from = addMonths(end, -3);
  } else if (range === '12m') {
    from = addMonths(end, -12);
  } else if (range === 'ytd') {
    from = new Date(end.getFullYear(), 0, 1);
  } else {
    from = addMonths(end, -3);
  }

  return {
    date_from: toYMD(from),
    date_to: toYMD(end)
  };
}

function buildSeries({ transactions, dateFrom, displayTo, chartEnd, currentBalance }) {
  const netByDate = new Map();    // YYYY-MM-DD -> sum(amount)
  const monthlyNet = new Map();   // periodKey (YYYY-MM) -> sum(amount)

  for (const tx of transactions) {
    const d = tx.date;
    if (d < dateFrom || d > chartEnd) continue;

    const amount = Number(tx.amount ?? 0);

    // daily net (for balance curve)
    netByDate.set(d, (netByDate.get(d) || 0) + amount);

    // salary-style period: 16th -> 15th
    const pKey = salaryPeriodKey(d);
    monthlyNet.set(pKey, (monthlyNet.get(pKey) || 0) + amount);
  }

  // --- daily balance series (same as before) ---
  const startDate = parseYMD(dateFrom);
  const endDate = parseYMD(chartEnd);

  const allDates = [];
  for (let d = startDate; d <= endDate; d = addDays(d, 1)) {
    allDates.push(toYMD(d));
  }

  let B = currentBalance;
  const fullSeries = new Array(allDates.length);

  for (let i = allDates.length - 1; i >= 0; i--) {
    const day = allDates[i];
    fullSeries[i] = { date: day, value: B };

    const delta = netByDate.get(day) || 0;
    B -= delta;
  }

  // expose only up to user's selected end date (already clamped)
  const balanceSeries = fullSeries.filter((p) => p.date <= displayTo);

  // --- salary-style "months" (16th -> 15th) ---
  const periodKeys = buildSalaryPeriodKeys(dateFrom, displayTo);
  const monthlySurplus = periodKeys.map((key) => ({
    month: key,
    net: monthlyNet.get(key) || 0
  }));

  return { balanceSeries, monthlySurplus };
}

function buildMonthKeys(dateFrom, dateTo) {
  const start = parseYMD(dateFrom);
  const end = parseYMD(dateTo);

  const firstMonthStart = new Date(start.getFullYear(), start.getMonth(), 1);
  const lastMonthStart = new Date(end.getFullYear(), end.getMonth(), 1);

  const months = [];
  for (let d = firstMonthStart; d <= lastMonthStart; d = addMonths(d, 1)) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    months.push(`${y}-${m}`);
  }
  return months;
}

function salaryPeriodKey(dateStr) {
  // dateStr: 'YYYY-MM-DD'
  const [year, month, day] = dateStr.split('-').map(Number);
  if (day >= 16) {
    // belongs to period starting this month
    return `${year}-${String(month).padStart(2, '0')}`;
  }

  // belongs to previous month
  if (month === 1) {
    return `${year - 1}-12`;
  }
  return `${year}-${String(month - 1).padStart(2, '0')}`;
}

function buildSalaryPeriodKeys(dateFrom, dateTo) {
  const firstKey = salaryPeriodKey(dateFrom);
  const lastKey = salaryPeriodKey(dateTo);

  let [sy, sm] = firstKey.split('-').map(Number);
  const [ey, em] = lastKey.split('-').map(Number);

  const keys = [];
  while (sy < ey || (sy === ey && sm <= em)) {
    keys.push(`${sy}-${String(sm).padStart(2, '0')}`);
    sm += 1;
    if (sm > 12) {
      sm = 1;
      sy += 1;
    }
  }
  return keys;
}
