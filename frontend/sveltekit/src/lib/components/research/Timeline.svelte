<script lang="ts">
  import type { CatalystEvent } from '$lib/types/research';

  interface Props {
    events: CatalystEvent[];
  }

  let { events }: Props = $props();

  const sorted = $derived([...events].sort((a, b) => a.date.localeCompare(b.date)));

  const impactConfig = {
    positive: { dot: 'bg-[var(--green)] border-[var(--green)]', text: 'text-[var(--green)]', label: 'Positive' },
    negative: { dot: 'bg-[var(--red)] border-[var(--red)]',     text: 'text-[var(--red)]',   label: 'Negative' },
    neutral:  { dot: 'bg-[var(--text-dimmed)] border-[var(--border-hover)]', text: 'text-[var(--text-muted)]', label: 'Neutral' }
  } as const;

  function formatDate(dateStr: string): string {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  function daysUntil(dateStr: string): number {
    const now = new Date();
    const d = new Date(dateStr);
    return Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  }
</script>

<div class="relative">
  <!-- Vertical line -->
  <div class="absolute left-[7px] top-2 bottom-2 w-px bg-[var(--border-default)]" aria-hidden="true"></div>

  <ol class="space-y-6 pl-6" aria-label="Event timeline">
    {#each sorted as event}
      {@const cfg = impactConfig[event.impact]}
      {@const days = daysUntil(event.date)}
      <li class="relative">
        <!-- Dot -->
        <div
          class="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full border-2 {cfg.dot}"
          aria-hidden="true"
        ></div>

        <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 hover:border-[var(--border-hover)] transition-colors">
          <div class="flex items-start justify-between gap-2 mb-2">
            <div>
              <p class="text-sm font-medium text-[var(--text-primary)]">{event.event}</p>
              <p class="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                {formatDate(event.date)}
                {#if days > 0}
                  <span class="ml-1 text-[var(--text-dimmed)]">({days}d away)</span>
                {:else}
                  <span class="ml-1 text-[var(--text-dimmed)]">(past)</span>
                {/if}
              </p>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <!-- Probability badge -->
              <span class="text-xs font-mono px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-muted)]">
                {event.probability}%
              </span>
              <!-- Impact badge -->
              <span class="text-xs font-mono {cfg.text}">{cfg.label}</span>
            </div>
          </div>
          <p class="text-xs text-[var(--text-secondary)] leading-relaxed">{event.description}</p>
        </div>
      </li>
    {/each}
  </ol>
</div>
