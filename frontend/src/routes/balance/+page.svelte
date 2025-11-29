<script>
  import { goto } from '$app/navigation';
  import { onMount, onDestroy } from 'svelte';

  const { data } = $props();

  // --- filter state (URL-synced) --------------------------------------------

  let account_id = $state(data.filters.account_id ?? '');
  let range      = $state(data.filters.range ?? '3m');
  let date_from  = $state(data.filters.date_from ?? '');
  let date_to    = $state(data.filters.date_to ?? '');

  // --- Chart.js runtime & canvas refs ---------------------------------------

  let mounted = $state(false);
  let ChartClass = $state(null); // Chart constructor from chart.js

  let balanceCanvas;
  let monthlyCanvas;

  let balanceChart;
  let monthlyChart;

  onMount(async () => {
    mounted = true;
    // client-only dynamic import avoids SSR issues
    const mod = await import('chart.js/auto');
    ChartClass = mod.default;
    createOrUpdateCharts();
  });

  onDestroy(() => {
    if (balanceChart) {
      balanceChart.destroy();
      balanceChart = undefined;
    }
    if (monthlyChart) {
      monthlyChart.destroy();
      monthlyChart = undefined;
    }
  });

  // --- formatting helpers ----------------------------------------------------

  const moneyFormatter = new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR'
  });

  function formatMoney(value) {
    return moneyFormatter.format(value ?? 0);
  }

  function accountLabel() {
    if (!account_id) return 'All accounts';
    const acc = data.accounts.find((a) => a.id === account_id);
    return acc ? acc.name : 'Selected account';
  }

  // --- navigation / URL sync -------------------------------------------------

  function nav() {
    const sp = new URLSearchParams();
    if (account_id) sp.set('account_id', account_id);
    if (range) sp.set('range', range);

    if (range === 'custom') {
      if (date_from) sp.set('date_from', date_from);
      if (date_to) sp.set('date_to', date_to);
    }

    const qs = sp.toString();
    goto(qs ? `?${qs}` : '?', {
      replaceState: true,
      noScroll: true,
      keepfocus: true
    });
  }

  // whenever filters differ from server data, navigate
  $effect(() => {
    const server = data.filters;

    const changed =
      (server.account_id ?? '') !== (account_id || '') ||
      (server.range ?? '3m') !== (range || '3m') ||
      (server.date_from ?? '') !== (date_from || '') ||
      (server.date_to ?? '') !== (date_to || '');

    if (!changed) return;
    nav();
  });

  // --- Chart creation / update ----------------------------------------------

  function createOrUpdateCharts() {
    if (!mounted || !ChartClass) return;

    createOrUpdateBalanceChart();
    createOrUpdateMonthlyChart();
  }

  function createOrUpdateBalanceChart() {
    if (!balanceCanvas) return;

    const labels = data.balanceSeries.map((p) => p.date);
    const values = data.balanceSeries.map((p) => p.value);

    const config = {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Balance',
            data: values,
            tension: 0.25,
            borderWidth: 2,
            borderColor: '#0f766e',
            backgroundColor: 'rgba(15, 118, 110, 0.08)',
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Date'
            },
            grid: {
              display: true,
              color: '#e2e8f0'
            },
            ticks: {
              maxTicksLimit: 6
            }
          },
          y: {
            title: {
              display: true,
              text: 'Balance'
            },
            grid: {
              display: true,
              color: '#e2e8f0'
            },
            ticks: {
              callback: (value) => formatMoney(value)
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const v = ctx.parsed.y ?? 0;
                return `Balance: ${formatMoney(v)}`;
              }
            }
          }
        }
      }
    };

    if (balanceChart) {
      balanceChart.data.labels = labels;
      balanceChart.data.datasets[0].data = values;
      balanceChart.update();
    } else {
      const ctx = balanceCanvas.getContext('2d');
      balanceChart = new ChartClass(ctx, config);
    }
  }

  function createOrUpdateMonthlyChart() {
    if (!monthlyCanvas) return;

    const labels = data.monthlySurplus.map((m) => m.label);
    const values = data.monthlySurplus.map((m) => m.net);

    const config = {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Surplus (fiscal month)',
            data: values,
            backgroundColor: (ctx) => {
              const v = ctx.raw ?? 0;
              return v >= 0 ? 'rgba(34, 197, 94, 0.85)' : 'rgba(244, 63, 94, 0.85)';
            },
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: {
              display: true,
              text: 'Fiscal period'
            },
            grid: {
              display: false
            }
          },
          y: {
            title: {
              display: true,
              text: 'Surplus'
            },
            grid: {
              display: true,
              color: '#e2e8f0'
            },
            ticks: {
              callback: (value) => formatMoney(value)
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              title: (items) => {
                const first = items[0];
                if (!first) return '';
                const idx = first.dataIndex ?? 0;
                return data.monthlySurplus[idx]?.range ?? first.label;
              },
              label: (ctx) => {
                const v = ctx.parsed.y ?? 0;
                return `Surplus: ${formatMoney(v)}`;
              }
            }
          }
        }
      }
    };

    if (monthlyChart) {
      monthlyChart.data.labels = labels;
      monthlyChart.data.datasets[0].data = values;
      monthlyChart.update();
    } else {
      const ctx = monthlyCanvas.getContext('2d');
      monthlyChart = new ChartClass(ctx, config);
    }
  }

  // Recreate/update charts whenever new data comes in (e.g. navigation)
  $effect(() => {
    // data.* comes from the server; when the route reloads, component remounts,
    // but this also covers the case where props change without remount.
    if (!mounted || !ChartClass) return;
    createOrUpdateCharts();
  });
</script>

<!-- Header -->
<div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
  <div>
    <h1 class="text-xl font-semibold text-slate-900">Balances</h1>
    <p class="text-sm text-slate-500">
      Account balances and monthly surplus over time.
    </p>
  </div>
</div>

<!-- Filters -->
<div class="mb-6 rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm">
  <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <!-- Account selector -->
    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      Account
      <select
        class="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition hover:bg-white focus:border-slate-400 focus:bg-white focus:ring-2 focus:ring-slate-200"
        bind:value={account_id}
      >
        <option value=''>All accounts</option>
        {#each data.accounts as acc}
          <option value={acc.id}>{acc.name}</option>
        {/each}
      </select>
    </label>

    <!-- Range selector -->
    <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
      Range
      <select
        class="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition hover:bg-white focus:border-slate-400 focus:bg-white focus:ring-2 focus:ring-slate-200"
        bind:value={range}
      >
        <option value="30d">Last 30 days</option>
        <option value="3m">Last 3 months</option>
        <option value="ytd">Year to date</option>
        <option value="12m">Last 12 months</option>
        <option value="custom">Custom</option>
      </select>
    </label>

    <!-- Custom dates (visible only when range=custom) -->
    {#if range === 'custom'}
      <div class="grid grid-cols-2 gap-3 sm:col-span-2 lg:col-span-1">
        <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
          From
          <input
            type="date"
            class="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition hover:bg-white focus:border-slate-400 focus:bg-white focus:ring-2 focus:ring-slate-200"
            bind:value={date_from}
          />
        </label>
        <label class="flex flex-col text-xs font-semibold uppercase tracking-wide text-slate-500">
          To
          <input
            type="date"
            class="mt-1 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition hover:bg-white focus:border-slate-400 focus:bg-white focus:ring-2 focus:ring-slate-200"
            bind:value={date_to}
          />
        </label>
      </div>
    {/if}
  </div>
</div>

<!-- Summary card -->
<div class="mb-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  <div class="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Current balance
        </p>
        <p class="mt-1 text-2xl font-semibold text-slate-900">
          {formatMoney(data.currentBalance)}
        </p>
        <p class="mt-1 text-xs text-slate-500">
          {accountLabel()}
        </p>
      </div>
    </div>
  </div>
</div>

<!-- Charts -->
<div class="space-y-6">
  <!-- Balance over time -->
  <div class="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm">
    <div class="mb-3 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold text-slate-900">Balance over time</h2>
        <p class="text-xs text-slate-500">
          {data.filters.date_from} – {data.filters.date_to} · {accountLabel()}
        </p>
      </div>
    </div>

    {#if data.balanceSeries.length === 0}
      <div class="py-8 text-center text-sm text-slate-500">
        No balance data for this time frame.
      </div>
    {:else if !mounted || !ChartClass}
      <div class="py-8 text-center text-sm text-slate-500">
        Loading chart…
      </div>
    {:else}
      <div class="h-64">
        <canvas bind:this={balanceCanvas}></canvas>
      </div>
    {/if}
  </div>

  <!-- Monthly surplus -->
  <div class="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm">
    <div class="mb-3 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold text-slate-900">Monthly surplus</h2>
        <p class="text-xs text-slate-500">
          Net of all transactions per fiscal month (7th–6th).
        </p>
      </div>
    </div>

    {#if data.monthlySurplus.length === 0}
      <div class="py-8 text-center text-sm text-slate-500">
        No transactions in this time frame.
      </div>
    {:else if !mounted || !ChartClass}
      <div class="py-8 text-center text-sm text-slate-500">
        Loading chart…
      </div>
    {:else}
      <div class="h-64">
        <canvas bind:this={monthlyCanvas}></canvas>
      </div>

      <div class="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
        {#each data.monthlySurplus as m}
          <span class="rounded-full bg-slate-100 px-2 py-1">
            {m.range}: {formatMoney(m.net)}
          </span>
        {/each}
      </div>
    {/if}
  </div>
</div>
