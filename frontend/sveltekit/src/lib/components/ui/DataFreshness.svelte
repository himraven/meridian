<script lang="ts">
  let { lastUpdated, label = '' }: { lastUpdated: string | null, label?: string } = $props();

  function getTimeDiff(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return { text: 'Just now', color: 'green' };
    if (mins < 60) return { text: `${mins}m ago`, color: 'green' };
    const hours = Math.floor(mins / 60);
    if (hours < 6) return { text: `${hours}h ago`, color: 'yellow' };
    return { text: `${hours}h ago`, color: 'red' };
  }

  let freshness = $derived(lastUpdated ? getTimeDiff(lastUpdated) : null);
</script>

{#if freshness}
  <span
    class="data-freshness-badge"
    style="--badge-color: var(--color-{freshness.color === 'green' ? 'up' : freshness.color === 'red' ? 'down' : 'warning'})"
    title={lastUpdated ? `Last updated: ${new Date(lastUpdated).toLocaleString()}` : ''}
  >
    <span class="dot"></span>
    {#if label}<span class="badge-label">{label}</span>{/if}
    <span class="badge-text">{freshness.text}</span>
  </span>
{/if}

<style>
  .data-freshness-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.7rem;
    color: var(--badge-color, var(--color-muted));
    padding: 2px 8px;
    border-radius: 9999px;
    background-color: color-mix(in srgb, var(--badge-color, var(--color-muted)) 15%, transparent);
    border: 1px solid color-mix(in srgb, var(--badge-color, var(--color-muted)) 30%, transparent);
    white-space: nowrap;
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--badge-color, var(--color-muted));
    flex-shrink: 0;
  }

  .badge-label {
    color: var(--text-secondary);
    font-size: 0.65rem;
  }

  .badge-text {
    font-weight: 500;
  }
</style>
