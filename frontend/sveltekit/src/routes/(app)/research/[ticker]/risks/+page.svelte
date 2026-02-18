<script lang="ts">
  import type { PageData } from '../$types';
  import type { RiskItem } from '$lib/types/research';

  let { data }: { data: PageData } = $props();

  const risks   = $derived(data.report.risks);
  const rating  = $derived(data.report.rating);
  const overview = $derived(data.report.overview);

  let expandedIdx = $state<number | null>(null);

  function toggleExpand(i: number) {
    expandedIdx = expandedIdx === i ? null : i;
  }

  const highRisks   = $derived(risks.filter(r => r.severity === 'high'));
  const medRisks    = $derived(risks.filter(r => r.severity === 'medium'));
  const lowRisks    = $derived(risks.filter(r => r.severity === 'low'));

  const severityConfig = {
    high:   { color: 'text-[var(--red)]',   dot: 'bg-[var(--red)]',   bg: 'bg-red-950/20 border-red-900/30',   label: 'High' },
    medium: { color: 'text-[var(--amber)]', dot: 'bg-[var(--amber)]', bg: 'bg-amber-950/20 border-amber-900/30', label: 'Medium' },
    low:    { color: 'text-[var(--green)]', dot: 'bg-[var(--green)]', bg: 'bg-green-950/10 border-green-900/20', label: 'Low' }
  } as const;

  const symbol = $derived(overview.market === 'CN' ? '¥' : overview.market === 'HK' ? 'HK$' : '$');

  // Upside/Downside calculation
  const upsidePct = $derived(((rating.targetPrice - overview.price) / overview.price) * 100);
  const bearDownsidePct = $derived(-35); // simplified worst case
</script>

<div class="space-y-5">
  <h2 class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Risk Assessment</h2>

  <!-- Risk Summary -->
  <div class="grid grid-cols-3 gap-3">
    <div class="bg-red-950/20 border border-red-900/30 rounded-xl p-4 text-center">
      <p class="text-2xl font-mono font-bold text-[var(--red)]">{highRisks.length}</p>
      <p class="text-xs font-mono uppercase tracking-wider text-red-400 mt-0.5">High Risk</p>
    </div>
    <div class="bg-amber-950/20 border border-amber-900/30 rounded-xl p-4 text-center">
      <p class="text-2xl font-mono font-bold text-[var(--amber)]">{medRisks.length}</p>
      <p class="text-xs font-mono uppercase tracking-wider text-amber-400 mt-0.5">Medium Risk</p>
    </div>
    <div class="bg-green-950/10 border border-green-900/20 rounded-xl p-4 text-center">
      <p class="text-2xl font-mono font-bold text-[var(--green)]">{lowRisks.length}</p>
      <p class="text-xs font-mono uppercase tracking-wider text-green-400 mt-0.5">Low Risk</p>
    </div>
  </div>

  <!-- Risk Cards -->
  <section aria-labelledby="risk-cards-heading">
    <h3 id="risk-cards-heading" class="text-xs font-medium text-[var(--text-muted)] mb-3 uppercase tracking-wider font-mono">
      Risk Factors
    </h3>
    <div class="space-y-2">
      {#each risks as risk, i}
        {@const cfg = severityConfig[risk.severity]}
        <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl overflow-hidden hover:border-[var(--border-hover)] transition-colors">
          <!-- Header row (always visible) -->
          <button
            class="w-full flex items-center gap-3 p-4 text-left"
            onclick={() => toggleExpand(i)}
            aria-expanded={expandedIdx === i}
            aria-label="Toggle risk details: {risk.category}"
          >
            <span class="w-2 h-2 rounded-full shrink-0 {cfg.dot}"></span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-medium text-[var(--text-primary)]">{risk.category}</span>
                <span class="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded {cfg.color} bg-[var(--bg-elevated)]">
                  {cfg.label}
                </span>
              </div>
              <p class="text-xs text-[var(--text-muted)] mt-0.5 truncate">{risk.description}</p>
            </div>
            <svg
              class="w-4 h-4 text-[var(--text-dimmed)] shrink-0 transition-transform {expandedIdx === i ? 'rotate-180' : ''}"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {#if expandedIdx === i}
            <div class="px-4 pb-4 border-t border-[var(--border-default)] space-y-3 pt-3">
              <!-- Full description -->
              <div>
                <p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">Description</p>
                <p class="text-sm text-[var(--text-secondary)] leading-relaxed">{risk.description}</p>
              </div>

              <!-- Bear case argument -->
              <div class="bg-red-950/10 border border-red-900/20 rounded-lg p-3">
                <p class="text-[11px] font-mono uppercase tracking-wider text-red-400 mb-1">Bear Case</p>
                <p class="text-xs text-[var(--text-secondary)] leading-relaxed">{risk.bearishArgument}</p>
              </div>

              <!-- Monitor trigger -->
              <div class="bg-amber-950/10 border border-amber-900/20 rounded-lg p-3">
                <p class="text-[11px] font-mono uppercase tracking-wider text-amber-400 mb-1">Monitor Trigger</p>
                <p class="text-xs text-[var(--text-secondary)] leading-relaxed">{risk.monitorTrigger}</p>
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </section>

  <!-- Short Thesis -->
  <section aria-labelledby="bear-thesis-heading">
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
      <h3 id="bear-thesis-heading" class="text-sm font-medium text-[var(--red)] mb-3">
        If You Were Shorting This Stock…
      </h3>
      <p class="text-xs text-[var(--text-muted)] mb-3">The strongest bearish arguments:</p>
      <ul class="space-y-2">
        {#each risks.filter(r => r.severity !== 'low') as risk}
          <li class="flex items-start gap-2">
            <span class="text-[var(--red)] mt-0.5 text-xs shrink-0">✕</span>
            <p class="text-xs text-[var(--text-secondary)] leading-relaxed">{risk.bearishArgument}</p>
          </li>
        {/each}
      </ul>
    </div>
  </section>

  <!-- Risk vs Reward -->
  <section aria-labelledby="risk-reward-heading">
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
      <h3 id="risk-reward-heading" class="text-sm font-medium text-[var(--text-primary)] mb-4">Risk vs. Reward</h3>
      <div class="space-y-3">
        <!-- Upside -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-[var(--text-muted)]">Upside to Target</span>
            <span class="font-mono text-[var(--green)] tabular-nums">+{upsidePct.toFixed(1)}%</span>
          </div>
          <div class="w-full h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
            <div
              class="h-full bg-[var(--green)] rounded-full"
              style="width: {Math.min(upsidePct, 100)}%"
            ></div>
          </div>
        </div>

        <!-- Downside -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-[var(--text-muted)]">Bear Case Downside</span>
            <span class="font-mono text-[var(--red)] tabular-nums">{bearDownsidePct}%</span>
          </div>
          <div class="w-full h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
            <div
              class="h-full bg-[var(--red)] rounded-full"
              style="width: {Math.min(Math.abs(bearDownsidePct), 100)}%"
            ></div>
          </div>
        </div>

        <!-- Ratio -->
        <div class="pt-2 border-t border-[var(--border-default)]">
          <div class="flex justify-between items-center">
            <span class="text-xs text-[var(--text-muted)]">Risk/Reward Ratio</span>
            <span class="text-sm font-mono font-semibold text-[var(--text-primary)] tabular-nums">
              1 : {(upsidePct / Math.abs(bearDownsidePct)).toFixed(1)}
            </span>
          </div>
          <p class="text-xs text-[var(--text-muted)] mt-1">
            {upsidePct / Math.abs(bearDownsidePct) >= 1.5
              ? 'Favorable asymmetry — upside significantly outweighs downside risk.'
              : 'Moderate asymmetry — risk and reward roughly balanced.'}
          </p>
        </div>
      </div>
    </div>
  </section>
</div>
