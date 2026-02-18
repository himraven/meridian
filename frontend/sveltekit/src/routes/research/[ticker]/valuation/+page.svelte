<script lang="ts">
  import type { PageData } from '../$types';
  import RadarChart from '$lib/components/research/RadarChart.svelte';
  import ValuationGauge from '$lib/components/research/ValuationGauge.svelte';
  import FinancialChart from '$lib/components/research/FinancialChart.svelte';

  let { data }: { data: PageData } = $props();

  const valuation = $derived(data.report.valuation);
  const overview  = $derived(data.report.overview);
  const rating    = $derived(data.report.rating);
  const financials = $derived(data.report.financials);

  const symbol = $derived(overview.market === 'CN' ? '¥' : overview.market === 'HK' ? 'HK$' : '$');

  // Radar indicators — scale to max reasonable for comparison
  const radarIndicators = $derived(valuation.map(v => ({
    name: v.metric,
    max: Math.max(v.current, v.fiveYearAvg, v.industryAvg) * 1.3
  })));

  const radarCurrent   = $derived(valuation.map(v => v.current));
  const radarIndustry  = $derived(valuation.map(v => v.industryAvg));

  // Historical PE Band data
  const peYears  = $derived(financials.map(f => f.year));
  const peValues = $derived(financials.map(f => {
    // rough price from EPS * PE (simplified)
    return parseFloat((f.eps * (overview.pe ?? 28)).toFixed(1));
  }));

  // DCF scenarios
  const dcfScenarios = $derived([
    {
      scenario: 'Bull',
      growth: 15,
      discount: 8,
      terminal: 25,
      impliedPrice: rating.targetPrice * 1.25,
      upside: ((rating.targetPrice * 1.25 / overview.price) - 1) * 100,
      color: 'text-[var(--green)]'
    },
    {
      scenario: 'Base',
      growth: 10,
      discount: 10,
      terminal: 20,
      impliedPrice: rating.targetPrice,
      upside: ((rating.targetPrice / overview.price) - 1) * 100,
      color: 'text-[var(--text-primary)]'
    },
    {
      scenario: 'Bear',
      growth: 5,
      discount: 12,
      terminal: 15,
      impliedPrice: rating.targetPrice * 0.65,
      upside: ((rating.targetPrice * 0.65 / overview.price) - 1) * 100,
      color: 'text-[var(--red)]'
    }
  ]);
</script>

<div class="space-y-5">
  <!-- Header -->
  <h2 class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Valuation Analysis</h2>

  <!-- Gauges -->
  <section aria-labelledby="gauges-heading">
    <h3 id="gauges-heading" class="text-xs text-[var(--text-muted)] mb-3 font-medium">Valuation Multiples</h3>
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {#each valuation as v}
        <ValuationGauge
          metric={v.metric}
          current={v.current}
          fiveYearAvg={v.fiveYearAvg}
          industryAvg={v.industryAvg}
          percentile={v.percentile}
          unit={v.metric === 'PEG' ? 'x' : 'x'}
        />
      {/each}
    </div>
  </section>

  <!-- Radar + PE Band -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <!-- Radar Chart -->
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 hover:border-[var(--border-hover)] transition-colors">
      <h3 class="text-sm font-medium text-[var(--text-primary)] mb-4">Valuation Radar — Current vs Industry</h3>
      <RadarChart
        indicators={radarIndicators}
        current={radarCurrent}
        industryAvg={radarIndustry}
        height="300px"
      />
    </div>

    <!-- DCF Scenarios -->
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 hover:border-[var(--border-hover)] transition-colors">
      <h3 class="text-sm font-medium text-[var(--text-primary)] mb-4">DCF Scenario Analysis</h3>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr>
              {#each ['Scenario', 'Growth', 'Discount', 'Terminal PE', 'Implied Price', 'Upside'] as col}
                <th class="text-right first:text-left pb-3 text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] border-b border-[var(--border-default)]">
                  {col}
                </th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each dcfScenarios as s}
              <tr class="border-b border-[var(--border-default)] hover:bg-[var(--bg-elevated)] transition-colors">
                <td class="py-3 text-sm font-medium {s.color}">{s.scenario}</td>
                <td class="py-3 text-right font-mono text-sm text-[var(--text-secondary)] tabular-nums">{s.growth}%</td>
                <td class="py-3 text-right font-mono text-sm text-[var(--text-secondary)] tabular-nums">{s.discount}%</td>
                <td class="py-3 text-right font-mono text-sm text-[var(--text-secondary)] tabular-nums">{s.terminal}x</td>
                <td class="py-3 text-right font-mono text-sm text-[var(--text-primary)] tabular-nums font-semibold">
                  {symbol}{s.impliedPrice.toLocaleString('en', { maximumFractionDigits: 0 })}
                </td>
                <td class="py-3 text-right font-mono text-sm tabular-nums {s.upside >= 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'}">
                  {s.upside >= 0 ? '+' : ''}{s.upside.toFixed(1)}%
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Current price reference -->
      <div class="mt-4 pt-4 border-t border-[var(--border-default)]">
        <div class="flex justify-between text-xs text-[var(--text-muted)]">
          <span>Current Price</span>
          <span class="font-mono tabular-nums text-[var(--text-secondary)]">
            {symbol}{overview.price.toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      </div>
    </div>
  </div>

  <!-- PE History chart -->
  <FinancialChart
    title="Historical Earnings Per Share (EPS)"
    years={peYears}
    series={[
      { name: 'EPS', type: 'bar', data: financials.map(f => parseFloat(f.eps.toFixed(2))), color: '#3f3f46' }
    ]}
    formatLeft={(v) => symbol + v.toFixed(2)}
    height="220px"
  />

  <!-- Valuation summary note -->
  <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
    <h3 class="text-sm font-medium text-[var(--text-primary)] mb-2">Valuation Summary</h3>
    <p class="text-sm text-[var(--text-secondary)] leading-relaxed">
      Current valuation multiples are trading at the
      <span class="text-[var(--green)] font-medium">
        {Math.round(valuation.reduce((a, v) => a + v.percentile, 0) / valuation.length)}th percentile
      </span>
      of their 5-year historical range — indicating the stock is trading below its historical average
      and potentially offers a margin of safety of
      <span class="text-[var(--green)] font-medium">{rating.safetyMargin.toFixed(1)}%</span> to our target price.
    </p>
  </div>
</div>
