<script lang="ts">
  import type { PageData } from '../$types';
  import Timeline from '$lib/components/research/Timeline.svelte';

  let { data }: { data: PageData } = $props();

  const catalysts = $derived(data.report.catalysts);
  const overview  = $derived(data.report.overview);

  const symbol = $derived(overview.market === 'CN' ? '¥' : overview.market === 'HK' ? 'HK$' : '$');

  const positive = $derived(catalysts.filter(c => c.impact === 'positive'));
  const negative = $derived(catalysts.filter(c => c.impact === 'negative'));

  // Probability-weighted expected value (simplified)
  const expectedImpact = $derived(
    catalysts.reduce((sum, c) => {
      const sign = c.impact === 'positive' ? 1 : c.impact === 'negative' ? -1 : 0;
      return sum + sign * (c.probability / 100) * 5; // 5% base impact per event
    }, 0)
  );

  // Monitoring checklist
  const checklistItems = $derived(catalysts.map(c => ({
    label: c.event,
    date: c.date,
    checked: false
  })));

  let checkedItems = $state<Set<number>>(new Set());

  function toggleCheck(i: number) {
    const next = new Set(checkedItems);
    if (next.has(i)) next.delete(i);
    else next.add(i);
    checkedItems = next;
  }

  function formatDate(dateStr: string): string {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
</script>

<div class="space-y-5">
  <h2 class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Upcoming Catalysts</h2>

  <!-- Summary stats -->
  <div class="grid grid-cols-3 gap-3">
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 text-center hover:border-[var(--border-hover)] transition-colors">
      <p class="text-2xl font-mono font-bold text-[var(--green)]">{positive.length}</p>
      <p class="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mt-0.5">Positive</p>
    </div>
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 text-center hover:border-[var(--border-hover)] transition-colors">
      <p class="text-2xl font-mono font-bold text-[var(--red)]">{negative.length}</p>
      <p class="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mt-0.5">Negative</p>
    </div>
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 text-center hover:border-[var(--border-hover)] transition-colors">
      <p class="text-2xl font-mono font-bold tabular-nums {expectedImpact >= 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'}">
        {expectedImpact >= 0 ? '+' : ''}{expectedImpact.toFixed(1)}%
      </p>
      <p class="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mt-0.5">Expected Impact</p>
    </div>
  </div>

  <!-- Main layout: Timeline + Impact Cards -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
    <!-- Timeline -->
    <section aria-labelledby="timeline-heading">
      <h3 id="timeline-heading" class="text-xs font-medium text-[var(--text-muted)] mb-3 uppercase tracking-wider font-mono">
        Event Timeline
      </h3>
      <Timeline events={catalysts} />
    </section>

    <!-- Impact Cards -->
    <section aria-labelledby="impact-heading">
      <h3 id="impact-heading" class="text-xs font-medium text-[var(--text-muted)] mb-3 uppercase tracking-wider font-mono">
        Impact Assessment
      </h3>
      <div class="space-y-3">
        {#each catalysts as c}
          {@const pWeighted = (c.probability / 100) * 5}
          <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 hover:border-[var(--border-hover)] transition-colors">
            <div class="flex items-start justify-between gap-2 mb-2">
              <p class="text-sm font-medium text-[var(--text-primary)]">{c.event}</p>
              <span class="text-xs font-mono text-[var(--text-muted)] shrink-0">{c.probability}% prob.</span>
            </div>
            <p class="text-xs text-[var(--text-secondary)] leading-relaxed mb-2">{c.description}</p>
            <div class="flex items-center justify-between text-xs">
              <span class="font-mono text-[var(--text-dimmed)]">{formatDate(c.date)}</span>
              <span class="font-mono font-medium {c.impact === 'positive' ? 'text-[var(--green)]' : c.impact === 'negative' ? 'text-[var(--red)]' : 'text-[var(--text-muted)]'}">
                P-weighted: {c.impact === 'positive' ? '+' : c.impact === 'negative' ? '-' : ''}{pWeighted.toFixed(1)}%
              </span>
            </div>
          </div>
        {/each}
      </div>
    </section>
  </div>

  <!-- Monitoring Checklist -->
  <section aria-labelledby="checklist-heading">
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
      <h3 id="checklist-heading" class="text-sm font-medium text-[var(--text-primary)] mb-4">
        Monitoring Checklist
      </h3>
      <div class="space-y-2">
        {#each checklistItems as item, i}
          <label
            class="flex items-center gap-3 p-2 rounded-lg hover:bg-[var(--bg-elevated)] cursor-pointer transition-colors"
            aria-label="Mark {item.label} as checked"
          >
            <input
              type="checkbox"
              checked={checkedItems.has(i)}
              onchange={() => toggleCheck(i)}
              class="w-4 h-4 rounded border border-[var(--border-hover)] bg-[var(--bg-elevated)] accent-[var(--green)]"
            />
            <div class="flex-1 flex items-center justify-between gap-2">
              <span class="text-sm {checkedItems.has(i) ? 'line-through text-[var(--text-muted)]' : 'text-[var(--text-secondary)]'}">
                {item.label}
              </span>
              <span class="text-xs font-mono text-[var(--text-dimmed)] shrink-0">{formatDate(item.date)}</span>
            </div>
          </label>
        {/each}
      </div>
      <p class="text-xs text-[var(--text-dimmed)] mt-3">
        {checkedItems.size}/{checklistItems.length} items tracked
      </p>
    </div>
  </section>
</div>
