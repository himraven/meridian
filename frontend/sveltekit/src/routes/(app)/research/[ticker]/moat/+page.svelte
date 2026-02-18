<script lang="ts">
  import type { PageData } from '../$types';
  import MoatScoreCard from '$lib/components/research/MoatScoreCard.svelte';

  let { data }: { data: PageData } = $props();

  const moat     = $derived(data.report.moat);
  const rating   = $derived(data.report.rating);
  const overview = $derived(data.report.overview);

  const avgScore = $derived(moat.reduce((a, m) => a + m.score, 0) / moat.length);

  const moatColor = $derived(
    rating.moatScore >= 8 ? 'var(--green)' :
    rating.moatScore >= 6 ? 'var(--amber)' :
    'var(--red)'
  );

  const moatLabel = $derived(
    rating.moatScore >= 8.5 ? 'Wide Moat' :
    rating.moatScore >= 6.5 ? 'Narrow Moat' :
    'No Moat'
  );

  // Sorted factors by score
  const sortedFactors = $derived([...moat].sort((a, b) => b.score - a.score));

  // Durability assessment
  const durabilityText = $derived(
    rating.moatScore >= 8
      ? 'The competitive advantages appear durable and likely to persist over the next 10+ years. Core moat drivers are structural rather than cyclical.'
      : rating.moatScore >= 6
      ? 'The moat is real but faces meaningful competitive pressure in some areas. Monitor for erosion over the next 3-5 years.'
      : 'The competitive position is fragile and could deteriorate meaningfully within 5 years.'
  );
</script>

<div class="space-y-5">
  <h2 class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Economic Moat Analysis</h2>

  <!-- Overall Score Hero -->
  <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-6">
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-6">
      <!-- Big score circle -->
      <div class="relative flex-shrink-0">
        <svg width="120" height="120" viewBox="0 0 120 120" aria-hidden="true">
          <!-- Background circle -->
          <circle cx="60" cy="60" r="52" fill="none" stroke="#27272a" stroke-width="8" />
          <!-- Progress arc -->
          <circle
            cx="60" cy="60" r="52"
            fill="none"
            stroke={moatColor}
            stroke-width="8"
            stroke-linecap="round"
            stroke-dasharray="{rating.moatScore / 10 * 326.7} 326.7"
            transform="rotate(-90 60 60)"
          />
        </svg>
        <div class="absolute inset-0 flex flex-col items-center justify-center">
          <span class="text-3xl font-mono font-bold tabular-nums" style="color:{moatColor}">
            {rating.moatScore.toFixed(1)}
          </span>
          <span class="text-xs text-[var(--text-muted)] font-mono">/10</span>
        </div>
      </div>

      <!-- Description -->
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-2">
          <h3 class="text-lg font-semibold text-[var(--text-primary)]">{moatLabel}</h3>
          <span class="px-2 py-0.5 rounded text-xs font-mono bg-[var(--bg-elevated)] border border-[var(--border-default)]" style="color:{moatColor}">
            {overview.name}
          </span>
        </div>
        <p class="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">
          {durabilityText}
        </p>
        <!-- Factor score summary bar -->
        <div class="flex gap-1 items-center">
          {#each sortedFactors as factor}
            <div
              class="h-5 rounded transition-all hover:opacity-90"
              style="
                flex: {factor.score};
                background: {factor.score >= 8 ? '#22c55e22' : factor.score >= 6 ? '#f59e0b22' : '#ef444422'};
                border: 1px solid {factor.score >= 8 ? '#22c55e44' : factor.score >= 6 ? '#f59e0b44' : '#ef444444'};
              "
              title="{factor.name}: {factor.score.toFixed(1)}/10"
            ></div>
          {/each}
        </div>
        <p class="text-xs text-[var(--text-dimmed)] mt-1">{moat.length} moat factors analyzed</p>
      </div>
    </div>
  </div>

  <!-- Factor Cards Grid -->
  <section aria-labelledby="factors-heading">
    <h3 id="factors-heading" class="text-xs font-medium text-[var(--text-muted)] mb-3 uppercase tracking-wider font-mono">
      Factor Breakdown
    </h3>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {#each sortedFactors as factor}
        <MoatScoreCard {factor} />
      {/each}
    </div>
  </section>

  <!-- Durability + Threats -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <!-- Durability Assessment -->
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
      <h3 class="text-sm font-medium text-[var(--text-primary)] mb-3">Durability Assessment</h3>
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <span class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] w-24 shrink-0">Trend</span>
          <span class="text-sm text-[var(--green)] font-medium">Strengthening</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] w-24 shrink-0">Horizon</span>
          <span class="text-sm text-[var(--text-secondary)]">10+ years</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] w-24 shrink-0">Type</span>
          <span class="text-sm text-[var(--text-secondary)]">Structural (not cyclical)</span>
        </div>
        <div class="pt-2 border-t border-[var(--border-default)]">
          <p class="text-xs text-[var(--text-secondary)] leading-relaxed">{durabilityText}</p>
        </div>
      </div>
    </div>

    <!-- Key Threats -->
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
      <h3 class="text-sm font-medium text-[var(--text-primary)] mb-3">Key Threats to Moat</h3>
      <ul class="space-y-2">
        {#each data.report.risks.slice(0, 3) as risk}
          <li class="flex items-start gap-2">
            <span class="mt-0.5 text-xs shrink-0
              {risk.severity === 'high' ? 'text-[var(--red)]' :
               risk.severity === 'medium' ? 'text-[var(--amber)]' :
               'text-[var(--green)]'}">
              ●
            </span>
            <div>
              <p class="text-xs font-medium text-[var(--text-secondary)]">{risk.category}</p>
              <p class="text-xs text-[var(--text-muted)] leading-relaxed">{risk.description}</p>
            </div>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</div>
