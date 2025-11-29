const DATE_RX = /^\d{4}-\d{2}-\d{2}$/;
const RANGE_VALUES = new Set(['30d', '3m', 'ytd', '12m', 'custom']);
const FISCAL_MONTH_START_DAY = 7;

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

  // --- fetch aggregated series from backend ----------------------------------
  const seriesParams = new URLSearchParams({
    date_from,
    date_to,
    granularity: 'daily'
  });
  if (account_id) seriesParams.set('account_id', account_id);

  const seriesRes = await fetch(`/api/balances/series?${seriesParams.toString()}`);
  if (!seriesRes.ok) throw new Error('Failed to load balance series');
  const seriesRaw = await seriesRes.json();
  const balanceSeries = Array.isArray(seriesRaw)
    ? seriesRaw.map((p) => ({
        date: p.date,
        value: Number(p.balance ?? 0)
      }))
    : [];

  const surplusParams = new URLSearchParams({
    date_from,
    date_to,
    granularity: 'fiscal_monthly'
  });
  if (account_id) surplusParams.set('account_id', account_id);

  const surplusRes = await fetch(`/api/balances/surplus?${surplusParams.toString()}`);
  if (!surplusRes.ok) throw new Error('Failed to load surplus data');
  const surplusRaw = await surplusRes.json();
  const monthlySurplus = Array.isArray(surplusRaw)
    ? surplusRaw.map((p) => {
        const range = fiscalRangeFromEnd(p.date, date_from);
        return {
          label: range.label,
          range: range.display,
          endDate: range.end,
          net: Number(p.delta ?? 0)
        };
      })
    : [];

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

function fiscalRangeFromEnd(endDateStr, minStartStr) {
  if (!endDateStr) {
    return {
      start: minStartStr || '',
      end: minStartStr || '',
      label: minStartStr || '',
      display: minStartStr || ''
    };
  }

  const end = parseYMD(endDateStr);
  const startCandidate = fiscalPeriodStart(end);
  const minStart = minStartStr ? parseYMD(minStartStr) : startCandidate;
  const start = startCandidate < minStart ? minStart : startCandidate;

  const startStr = toYMD(start);
  const endStr = toYMD(end);
  return {
    start: startStr,
    end: endStr,
    label: endStr,
    display: `${startStr} – ${endStr}`
  };
}

function fiscalPeriodStart(date) {
  const anchor = FISCAL_MONTH_START_DAY;
  if (date.getDate() >= anchor) {
    return new Date(date.getFullYear(), date.getMonth(), anchor);
  }
  const prevMonth = new Date(date.getFullYear(), date.getMonth(), 0);
  return new Date(prevMonth.getFullYear(), prevMonth.getMonth(), anchor);
}
