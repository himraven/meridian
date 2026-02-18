<script lang="ts">
  import { page } from '$app/stores';
</script>

<svelte:head>
  <title>Report Not Found — Research — Meridian</title>
</svelte:head>

<div class="flex flex-col items-center justify-center py-24 text-center">
  <p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-3">Research</p>
  <h1 class="text-xl font-semibold text-[var(--text-primary)] mb-2">Report Not Found</h1>
  <p class="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
    No research report found for <span class="font-mono text-[var(--text-primary)]">{$page.params.ticker}</span>.
    This ticker may not be covered yet.
  </p>
  {#if $page.error?.message}
    <p class="text-xs text-[var(--text-muted)] mb-6 font-mono">{$page.error.message}</p>
  {/if}
  <a
    href="/research"
    class="px-4 py-2 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-lg
      text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)]
      transition-colors"
  >
    Browse All Reports
  </a>
</div>
