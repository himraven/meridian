<script lang="ts">
  interface Props {
    metric: string;
    current: number;
    fiveYearAvg: number;
    industryAvg: number;
    percentile: number;
    unit?: string;
  }

  let { metric, current, fiveYearAvg, industryAvg, percentile, unit = 'x' }: Props = $props();

  // percentile 0 = very cheap, 100 = very expensive
  const gaugeColor = $derived(
    percentile <= 30 ? 'var(--green)' :
    percentile <= 60 ? 'var(--amber)' :
    'var(--red)'
  );

  const gaugeLabel = $derived(
    percentile <= 30 ? 'Cheap' :
    percentile <= 60 ? 'Fair' :
    'Expensive'
  );

  const vsAvg = $derived(((current - fiveYearAvg) / fiveYearAvg) * 100);
  const vsIndustry = $derived(((current - industryAvg) / industryAvg) * 100);
</script>

<div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 hover:border-[var(--border-hover)] transition-colors">
  <!-- Header -->
  <div class="flex items-center justify-between mb-3">
    <span class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">{metric}</span>
    <span class="text-xs font-mono font-semibold" style="color:{gaugeColor}">{gaugeLabel}</span>
  </div>

  <!-- Current value -->
  <p class="text-2xl font-mono font-semibold text-[var(--text-primary)] tabular-nums mb-3">
    {current.toFixed(1)}{unit}
  </p>

  <!-- Percentile bar -->
  <div class="mb-3">
    <div class="flex justify-between text-[10px] font-mono text-[var(--text-dimmed)] mb-1">
      <span>Cheap</span>
      <span>{percentile}th pct.</span>
      <span>Exp.</span>
    </div>
    <div class="relative w-full h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
      <!-- Color gradient track -->
      <div class="absolute inset-0 rounded-full" style="background: linear-gradient(to right, #22c55e, #f59e0b 50%, #ef4444)"></div>
      <!-- Indicator needle -->
      <div
        class="absolute top-0 w-2.5 h-1.5 bg-white rounded-full shadow"
        style="left: calc({percentile}% - 5px)"
      ></div>
    </div>
  </div>

  <!-- Comparisons -->
  <div class="space-y-1.5 pt-2 border-t border-[var(--border-default)]">
    <div class="flex justify-between text-xs">
      <span class="text-[var(--text-muted)]">5yr avg</span>
      <span class="font-mono tabular-nums text-[var(--text-secondary)]">
        {fiveYearAvg.toFixed(1)}{unit}
        <span class="{vsAvg < 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'} ml-1">
          {vsAvg < 0 ? '' : '+'}{vsAvg.toFixed(0)}%
        </span>
      </span>
    </div>
    <div class="flex justify-between text-xs">
      <span class="text-[var(--text-muted)]">Industry</span>
      <span class="font-mono tabular-nums text-[var(--text-secondary)]">
        {industryAvg.toFixed(1)}{unit}
        <span class="{vsIndustry < 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'} ml-1">
          {vsIndustry < 0 ? '' : '+'}{vsIndustry.toFixed(0)}%
        </span>
      </span>
    </div>
  </div>
</div>
