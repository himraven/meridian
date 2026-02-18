<script lang="ts">
  import type { MoatFactor } from '$lib/types/research';

  interface Props {
    factor: MoatFactor;
  }

  let { factor }: Props = $props();

  let expanded = $state(false);

  const barColor = $derived(
    factor.score >= 8 ? 'var(--green)' :
    factor.score >= 6 ? 'var(--amber)' :
    'var(--red)'
  );

  const scoreLabel = $derived(
    factor.score >= 8.5 ? 'Exceptional' :
    factor.score >= 7.0 ? 'Strong' :
    factor.score >= 5.0 ? 'Moderate' :
    'Weak'
  );
</script>

<div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 hover:border-[var(--border-hover)] transition-colors">
  <!-- Header -->
  <div class="flex items-start justify-between mb-2">
    <h4 class="text-sm font-medium text-[var(--text-primary)]">{factor.name}</h4>
    <div class="text-right shrink-0 ml-2">
      <span class="text-lg font-mono font-bold tabular-nums" style="color:{barColor}">{factor.score.toFixed(1)}</span>
      <span class="text-xs text-[var(--text-muted)] font-mono">/10</span>
    </div>
  </div>

  <!-- Score bar -->
  <div class="w-full h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden mb-2">
    <div
      class="h-full rounded-full transition-all"
      style="width:{factor.score * 10}%; background:{barColor}"
    ></div>
  </div>

  <p class="text-xs text-[var(--text-muted)] mb-2">{factor.description}</p>

  <!-- Expand button -->
  <button
    onclick={() => { expanded = !expanded; }}
    class="flex items-center gap-1 text-xs text-[var(--text-dimmed)] hover:text-[var(--text-muted)] transition-colors"
    aria-expanded={expanded}
    aria-label="Toggle evidence for {factor.name}"
  >
    <svg
      class="w-3 h-3 transition-transform {expanded ? 'rotate-180' : ''}"
      fill="none" stroke="currentColor" viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
    </svg>
    Evidence
  </button>

  {#if expanded}
    <ul class="mt-2 space-y-1 pl-3 border-l-2 border-[var(--border-default)]">
      {#each factor.evidence as item}
        <li class="text-xs text-[var(--text-secondary)] leading-relaxed">{item}</li>
      {/each}
    </ul>
  {/if}
</div>
