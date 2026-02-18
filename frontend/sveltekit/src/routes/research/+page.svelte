<script lang="ts">
  import { availableReports } from '$lib/data/mock-research';

  interface ReportCard {
    ticker: string;
    name: string;
    market: string;
    signal: string;
  }

  let searchQuery = $state('');

  const allReports: ReportCard[] = availableReports.map(r => ({ ...r }));

  const filtered = $derived(
    searchQuery.trim() === ''
      ? allReports
      : allReports.filter(r =>
          r.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
          r.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
  );

  const signalColors: Record<string, string> = {
    'strong-buy': 'text-[var(--green)]',
    'buy': 'text-[var(--green)]',
    'hold': 'text-[var(--amber)]',
    'caution': 'text-[var(--amber)]',
    'avoid': 'text-[var(--red)]'
  };

  function getMarketLabel(market: string): string {
    if (market === 'CN') return 'A股';
    if (market === 'HK') return '港股';
    return market;
  }
</script>

<svelte:head>
  <title>Research Reports — Meridian</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div>
    <p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">Analysis</p>
    <h1 class="text-2xl font-semibold text-[var(--text-primary)]">Research Reports</h1>
    <p class="text-sm text-[var(--text-secondary)] mt-1">Deep-dive fundamental analysis powered by Meridian AI</p>
  </div>

  <!-- Search -->
  <div class="relative">
    <svg
      class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]"
      fill="none" stroke="currentColor" viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
    <input
      type="search"
      placeholder="Search by ticker or company name..."
      bind:value={searchQuery}
      class="w-full max-w-md pl-9 pr-4 py-2.5 bg-[var(--bg-surface)] border border-[var(--border-default)]
        rounded-lg text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]
        focus:outline-none focus:border-[var(--border-focus)] transition-colors"
      aria-label="Search research reports"
    />
  </div>

  <!-- Reports Grid -->
  {#if filtered.length > 0}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each filtered as r}
        <a
          href="/research/{r.ticker}"
          class="block bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5
            hover:border-[var(--border-hover)] transition-colors group"
          aria-label="View research report for {r.name}"
        >
          <div class="flex items-start justify-between mb-3">
            <div>
              <p class="text-base font-semibold text-[var(--text-primary)] group-hover:text-white transition-colors">
                {r.name}
              </p>
              <p class="text-xs font-mono text-[var(--text-muted)] mt-0.5">{r.ticker}</p>
            </div>
            <span class="px-2 py-0.5 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-xs font-mono text-[var(--text-muted)]">
              {getMarketLabel(r.market)}
            </span>
          </div>

          <div class="flex items-center justify-between pt-3 border-t border-[var(--border-default)]">
            <span class="text-xs font-mono uppercase tracking-wide font-semibold {signalColors[r.signal] || 'text-[var(--text-muted)]'}">
              {r.signal.replace('-', ' ')}
            </span>
            <svg class="w-4 h-4 text-[var(--text-dimmed)] group-hover:text-[var(--text-muted)] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </a>
      {/each}
    </div>
  {:else}
    <div class="text-center py-16">
      <p class="text-sm text-[var(--text-muted)]">No reports match "{searchQuery}"</p>
    </div>
  {/if}

  <!-- Footer note -->
  <p class="text-xs text-[var(--text-dimmed)]">
    {filtered.length} report{filtered.length !== 1 ? 's' : ''} available · Updated via Meridian AI
  </p>
</div>
