<script lang="ts">
  import type { PageData } from '../$types';
  import FinancialChart from '$lib/components/research/FinancialChart.svelte';

  let { data }: { data: PageData } = $props();

  const financials = $derived(data.report.financials);
  const market = $derived(data.report.overview.market);

  const symbol = $derived(market === 'CN' ? '¥' : market === 'HK' ? 'HK$' : '$');

  const years = $derived(financials.map(f => f.year));

  function fmtB(v: number): string {
    if (v >= 1e12) return `${(v / 1e12).toFixed(1)}T`;
    if (v >= 1e9)  return `${(v / 1e9).toFixed(1)}B`;
    return `${(v / 1e6).toFixed(0)}M`;
  }

  function fmtPct(v: number): string {
    return v.toFixed(1) + '%';
  }

  const revenueData  = $derived(financials.map(f => parseFloat((f.revenue  / 1e9).toFixed(1))));
  const netIncData   = $derived(financials.map(f => parseFloat((f.netIncome / 1e9).toFixed(1))));
  const ocfData      = $derived(financials.map(f => parseFloat((f.operatingCashFlow / 1e9).toFixed(1))));
  const fcfData      = $derived(financials.map(f => parseFloat((f.freeCashFlow / 1e9).toFixed(1))));
  const roeData      = $derived(financials.map(f => parseFloat(f.roe.toFixed(1))));
  const debtData     = $derived(financials.map(f => parseFloat(f.debtToEquity.toFixed(2))));
  const currentData  = $derived(financials.map(f => parseFloat(f.currentRatio.toFixed(2))));

  // Piotroski-like health score (simplified, 0-9)
  const latest = $derived(financials[financials.length - 1]);
  const prev   = $derived(financials[financials.length - 2]);

  const pScore = $derived((() => {
    let score = 0;
    if (latest.netIncome > 0) score++;
    if (latest.operatingCashFlow > 0) score++;
    if (latest.roe > prev.roe) score++;
    if (latest.operatingCashFlow > latest.netIncome) score++;
    if (latest.debtToEquity < prev.debtToEquity) score++;
    if (latest.currentRatio > prev.currentRatio) score++;
    if (latest.revenue > prev.revenue) score++;
    if (latest.netIncome > prev.netIncome) score++;
    if (latest.freeCashFlow > 0) score++;
    return score;
  })());

  const pScoreLabel = $derived(
    pScore >= 7 ? 'Strong' :
    pScore >= 5 ? 'Moderate' :
    'Weak'
  );

  const pScoreColor = $derived(
    pScore >= 7 ? 'var(--green)' :
    pScore >= 5 ? 'var(--amber)' :
    'var(--red)'
  );

  const ratioRows = $derived([
    {
      label: 'Return on Equity',
      key: 'roe',
      unit: '%',
      values: financials.map(f => f.roe),
      format: (v: number) => v.toFixed(1) + '%',
      isGoodHigh: true
    },
    {
      label: 'Debt / Equity',
      key: 'de',
      unit: 'x',
      values: financials.map(f => f.debtToEquity),
      format: (v: number) => v.toFixed(2) + 'x',
      isGoodHigh: false
    },
    {
      label: 'Current Ratio',
      key: 'cr',
      unit: 'x',
      values: financials.map(f => f.currentRatio),
      format: (v: number) => v.toFixed(2) + 'x',
      isGoodHigh: true
    },
    {
      label: 'EPS',
      key: 'eps',
      unit: symbol,
      values: financials.map(f => f.eps),
      format: (v: number) => symbol + v.toFixed(2),
      isGoodHigh: true
    }
  ]);

  function getTrend(values: number[], idx: number): 'up' | 'down' | 'flat' {
    if (idx === 0) return 'flat';
    const diff = values[idx] - values[idx - 1];
    if (Math.abs(diff) < 0.001) return 'flat';
    return diff > 0 ? 'up' : 'down';
  }

  function trendColor(trend: 'up' | 'down' | 'flat', isGoodHigh: boolean): string {
    if (trend === 'flat') return 'text-[var(--text-muted)]';
    if (trend === 'up') return isGoodHigh ? 'text-[var(--green)]' : 'text-[var(--red)]';
    return isGoodHigh ? 'text-[var(--red)]' : 'text-[var(--green)]';
  }
</script>

<div class="space-y-5">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <h2 class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Financial Performance</h2>
    <span class="text-xs text-[var(--text-dimmed)] font-mono">{symbol}B = billions</span>
  </div>

  <!-- Charts Row 1 -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <FinancialChart
      title="Revenue & Net Income"
      {years}
      series={[
        { name: 'Revenue', type: 'bar', data: revenueData, color: '#3f3f46' },
        { name: 'Net Income', type: 'line', data: netIncData, color: '#22c55e', yAxisIndex: 1 }
      ]}
      formatLeft={(v) => `${v}B`}
      formatRight={(v) => `${v}B`}
      hasRightAxis={true}
    />
    <FinancialChart
      title="Cash Flow Quality"
      {years}
      series={[
        { name: 'Operating CF', type: 'bar', data: ocfData, color: '#22c55e' },
        { name: 'Free CF', type: 'bar', data: fcfData, color: '#3b82f6' },
        { name: 'Net Income', type: 'line', data: netIncData, color: '#f59e0b' }
      ]}
      formatLeft={(v) => `${v}B`}
    />
  </div>

  <!-- Charts Row 2 -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <FinancialChart
      title="Return on Equity (%)"
      {years}
      series={[
        { name: 'ROE', type: 'bar', data: roeData, color: '#22c55e' }
      ]}
      formatLeft={fmtPct}
    />
    <FinancialChart
      title="Leverage & Liquidity"
      {years}
      series={[
        { name: 'Debt/Equity', type: 'bar', data: debtData, color: '#ef4444', yAxisIndex: 0 },
        { name: 'Current Ratio', type: 'line', data: currentData, color: '#22c55e', yAxisIndex: 1 }
      ]}
      formatLeft={(v) => v.toFixed(2) + 'x'}
      formatRight={(v) => v.toFixed(2) + 'x'}
      hasRightAxis={true}
    />
  </div>

  <!-- Financial Health Score -->
  <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
    <div class="flex items-start justify-between mb-4">
      <div>
        <h3 class="text-sm font-medium text-[var(--text-primary)]">Financial Health Score</h3>
        <p class="text-xs text-[var(--text-muted)] mt-0.5">Based on Piotroski F-Score criteria (9 factors)</p>
      </div>
      <div class="text-right">
        <span class="text-3xl font-mono font-bold tabular-nums" style="color:{pScoreColor}">{pScore}</span>
        <span class="text-base text-[var(--text-muted)] font-mono">/9</span>
        <p class="text-xs font-mono font-semibold mt-0.5" style="color:{pScoreColor}">{pScoreLabel}</p>
      </div>
    </div>
    <!-- Score bar -->
    <div class="w-full h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all"
        style="width:{(pScore/9)*100}%; background:{pScoreColor}"
      ></div>
    </div>
    <div class="flex justify-between mt-1">
      <span class="text-[10px] font-mono text-[var(--text-dimmed)]">Weak 0</span>
      <span class="text-[10px] font-mono text-[var(--text-dimmed)]">Strong 9</span>
    </div>
  </div>

  <!-- Key Ratios Table -->
  <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl overflow-hidden">
    <div class="px-5 py-4 border-b border-[var(--border-default)]">
      <h3 class="text-sm font-medium text-[var(--text-primary)]">Key Ratios by Year</h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr>
            <th class="text-left px-5 py-3 text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] border-b border-[var(--border-default)]">
              Metric
            </th>
            {#each years as year}
              <th class="text-right px-4 py-3 text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] border-b border-[var(--border-default)]">
                {year}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each ratioRows as row}
            <tr class="border-b border-[var(--border-default)] hover:bg-[var(--bg-elevated)] transition-colors">
              <td class="px-5 py-3 text-sm text-[var(--text-secondary)]">{row.label}</td>
              {#each row.values as val, i}
                {@const trend = getTrend(row.values, i)}
                <td class="px-4 py-3 text-right font-mono text-sm tabular-nums">
                  <span class={trendColor(trend, row.isGoodHigh)}>
                    {row.format(val)}
                    {#if trend !== 'flat'}
                      <span class="text-xs ml-0.5">{trend === 'up' ? '▲' : '▼'}</span>
                    {/if}
                  </span>
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
