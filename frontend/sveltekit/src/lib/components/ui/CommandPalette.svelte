<script lang="ts">
  import { goto } from '$app/navigation';
  import { paletteOpen, closePalette } from '$lib/stores/commandPalette';

  // Local state
  let query = $state('');
  let selectedIndex = $state(0);
  let searchResult = $state<{ ticker: string; company: string; total_signals: number } | null>(null);
  let searchLoading = $state(false);
  let inputEl = $state<HTMLInputElement | null>(null);

  // Recent tickers
  function getRecentTickers(): string[] {
    if (typeof localStorage === 'undefined') return [];
    try {
      return JSON.parse(localStorage.getItem('recentTickers') || '[]');
    } catch {
      return [];
    }
  }

  function addRecentTicker(symbol: string) {
    if (typeof localStorage === 'undefined') return;
    const recent = getRecentTickers().filter((t: string) => t !== symbol);
    recent.unshift(symbol);
    localStorage.setItem('recentTickers', JSON.stringify(recent.slice(0, 5)));
  }

  let recentTickers = $state<string[]>([]);

  // Pages — plain text labels, no emoji
  const pages = [
    { name: 'Dashboard',       path: '/',            hint: 'Home' },
    { name: 'Congress Trades', path: '/congress',    hint: 'GOV' },
    { name: 'ARK Invest',      path: '/ark',         hint: 'ARK' },
    { name: 'Dark Pool',       path: '/darkpool',    hint: 'DP' },
    { name: 'Institutions',    path: '/institutions', hint: '13F' },
    { name: 'Ranking',         path: '/ranking',     hint: 'RNK' },
    { name: 'HK Market',       path: '/hk',          hint: 'HK' },
    { name: 'CN Strategy',     path: '/cn',          hint: 'CN' },
    { name: 'Research',        path: '/research',    hint: 'RES' },
    { name: 'Dividend',        path: '/dividend',    hint: 'DIV' },
  ];

  // Filtered pages
  let filteredPages = $derived(
    query.trim()
      ? pages.filter(p => p.name.toLowerCase().includes(query.trim().toLowerCase()))
      : pages
  );

  // Full items list for keyboard navigation
  type ResultItem = {
    type: 'page' | 'recent' | 'result';
    label: string;
    hint?: string;
    path: string;
    ticker?: string;
    company?: string;
    total_signals?: number;
  };

  let allItems = $derived<ResultItem[]>((): ResultItem[] => {
    const result: ResultItem[] = [];
    if (!query.trim()) {
      for (const t of recentTickers) {
        result.push({ type: 'recent', label: t, hint: 'Recent', path: `/ticker/${t}`, ticker: t });
      }
      for (const p of pages) {
        result.push({ type: 'page', label: p.name, hint: p.hint, path: p.path });
      }
    } else {
      for (const p of filteredPages) {
        result.push({ type: 'page', label: p.name, hint: p.hint, path: p.path });
      }
      if (searchResult) {
        result.push({
          type: 'result',
          label: searchResult.ticker,
          hint: 'Ticker',
          path: `/ticker/${searchResult.ticker}`,
          ticker: searchResult.ticker,
          company: searchResult.company,
          total_signals: searchResult.total_signals
        });
      }
    }
    return result;
  });

  // Debounce ticker search
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  $effect(() => {
    const q = query.trim().toUpperCase();
    if (!q || !/^[A-Z0-9]{1,6}$/.test(q)) {
      searchResult = null;
      searchLoading = false;
      return;
    }
    if (debounceTimer) clearTimeout(debounceTimer);
    searchLoading = true;
    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/ticker/${q}`);
        if (res.ok) {
          const json = await res.json();
          searchResult = {
            ticker: json.data?.ticker ?? q,
            company: json.data?.company ?? 'Unknown',
            total_signals: json.data?.metadata?.total_signals ?? 0
          };
        } else {
          searchResult = null;
        }
      } catch {
        searchResult = null;
      } finally {
        searchLoading = false;
      }
    }, 350);
  });

  // Reset selectedIndex when items change
  $effect(() => {
    allItems;
    selectedIndex = 0;
  });

  // When palette opens, reload recent tickers and focus input
  $effect(() => {
    if ($paletteOpen) {
      recentTickers = getRecentTickers();
      query = '';
      selectedIndex = 0;
      searchResult = null;
      setTimeout(() => inputEl?.focus(), 50);
    }
  });

  function handleClose() {
    closePalette();
    query = '';
    searchResult = null;
    selectedIndex = 0;
  }

  function selectItem(item: ResultItem) {
    if (item.ticker) addRecentTicker(item.ticker);
    goto(item.path);
    handleClose();
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      handleClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, allItems.length - 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
    } else if (e.key === 'Enter') {
      const item = allItems[selectedIndex];
      if (item) selectItem(item);
    }
  }

  function onGlobalKeydown(e: KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      paletteOpen.update(v => !v);
    }
  }
</script>

<svelte:window onkeydown={onGlobalKeydown} />

{#if $paletteOpen}
  <!-- Backdrop — NO blur, just dim overlay -->
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="palette-backdrop"
    onclick={handleClose}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="palette-modal"
      onclick={(e) => e.stopPropagation()}
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
    >
      <!-- Search Input -->
      <div class="palette-search">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          bind:this={inputEl}
          bind:value={query}
          onkeydown={onKeydown}
          type="text"
          placeholder="Search ticker or navigate..."
          class="palette-input"
          autocomplete="off"
          autocorrect="off"
          spellcheck="false"
        />
        {#if searchLoading}
          <span class="search-loading">⟳</span>
        {/if}
        <!-- svelte-ignore a11y_interactive_supports_focus -->
        <kbd class="esc-badge" role="button" onclick={handleClose}>esc</kbd>
      </div>

      <!-- Results -->
      <div class="palette-results">
        {#if !query.trim()}
          {#if recentTickers.length > 0}
            <div class="result-group-label">Recent</div>
            {#each recentTickers as ticker, i}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <div
                class="result-item {selectedIndex === i ? 'selected' : ''}"
                onclick={() => selectItem({ type: 'recent', label: ticker, hint: 'Recent', path: `/ticker/${ticker}`, ticker })}
                onmouseenter={() => (selectedIndex = i)}
              >
                <span class="result-hint">RECENT</span>
                <span class="result-label mono-label">{ticker}</span>
              </div>
            {/each}
          {/if}
          <div class="result-group-label">Pages</div>
          {#each pages as p, i}
            {@const idx = recentTickers.length + i}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
              class="result-item {selectedIndex === idx ? 'selected' : ''}"
              onclick={() => selectItem({ type: 'page', label: p.name, hint: p.hint, path: p.path })}
              onmouseenter={() => (selectedIndex = idx)}
            >
              <span class="result-hint">{p.hint}</span>
              <span class="result-label">{p.name}</span>
              <span class="result-path">{p.path}</span>
            </div>
          {/each}
        {:else}
          {#if filteredPages.length > 0}
            <div class="result-group-label">Pages</div>
            {#each filteredPages as p, i}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <div
                class="result-item {selectedIndex === i ? 'selected' : ''}"
                onclick={() => selectItem({ type: 'page', label: p.name, hint: p.hint, path: p.path })}
                onmouseenter={() => (selectedIndex = i)}
              >
                <span class="result-hint">{p.hint}</span>
                <span class="result-label">{p.name}</span>
                <span class="result-path">{p.path}</span>
              </div>
            {/each}
          {/if}

          {#if searchResult}
            <div class="result-group-label">Ticker</div>
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
              class="result-item {selectedIndex === filteredPages.length ? 'selected' : ''}"
              onclick={() => searchResult && selectItem({
                type: 'result',
                label: searchResult.ticker,
                hint: 'Ticker',
                path: `/ticker/${searchResult.ticker}`,
                ticker: searchResult.ticker
              })}
              onmouseenter={() => (selectedIndex = filteredPages.length)}
            >
              <span class="result-hint">TICK</span>
              <div class="result-ticker-info">
                <span class="result-label mono-label">{searchResult.ticker}</span>
                <span class="result-company">{searchResult.company}</span>
              </div>
              <span class="result-count">{searchResult.total_signals} signals</span>
            </div>
          {:else if query.trim().length >= 1 && !searchLoading && /^[A-Z0-9]{1,6}$/i.test(query.trim())}
            <div class="result-empty">No ticker found for "{query.trim().toUpperCase()}"</div>
          {:else if !filteredPages.length}
            <div class="result-empty">No results for "{query}"</div>
          {/if}
        {/if}
      </div>

      <!-- Footer -->
      <div class="palette-footer">
        <span><kbd>↑↓</kbd> navigate</span>
        <span><kbd>↵</kbd> select</span>
        <span><kbd>⌘K</kbd> toggle</span>
        <span><kbd>ESC</kbd> close</span>
      </div>
    </div>
  </div>
{/if}

<style>
  .palette-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 80px;
    background: rgba(0, 0, 0, 0.70);
    /* NO backdrop-filter here — that's navbar's job */
  }

  .palette-modal {
    width: 100%;
    max-width: 580px;
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    border-radius: 16px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    max-height: 70vh;
  }

  .palette-search {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border-default);
  }

  .search-icon {
    width: 17px;
    height: 17px;
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .palette-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 15px;
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
  }

  .palette-input::placeholder {
    color: var(--text-dimmed);
  }

  .search-loading {
    color: var(--text-muted);
    font-size: 1.1rem;
    display: inline-block;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .esc-badge {
    background: transparent;
    border: 1px solid var(--border-default);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
    cursor: pointer;
    user-select: none;
    letter-spacing: 0.02em;
  }

  .palette-results {
    flex: 1;
    overflow-y: auto;
    padding: 6px 0;
  }

  .result-group-label {
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dimmed);
    padding: 10px 16px 4px;
  }

  .result-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    cursor: pointer;
    transition: background 80ms;
    border-radius: 8px;
    margin: 1px 6px;
  }

  .result-item.selected,
  .result-item:hover {
    background: var(--bg-surface);
  }

  .result-hint {
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: var(--text-dimmed);
    padding: 2px 6px;
    border-radius: 3px;
    min-width: 36px;
    text-align: center;
    flex-shrink: 0;
  }

  .result-label {
    flex: 1;
    color: var(--text-secondary);
    font-size: 14px;
  }

  .mono-label {
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--text-primary);
  }

  .result-path {
    font-size: 11px;
    color: var(--text-dimmed);
    font-family: 'JetBrains Mono', monospace;
  }

  .result-ticker-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .result-company {
    font-size: 11px;
    color: var(--text-muted);
  }

  .result-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    white-space: nowrap;
  }

  .result-empty {
    padding: 20px 16px;
    text-align: center;
    color: var(--text-muted);
    font-size: 13px;
  }

  .palette-footer {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 8px 16px;
    border-top: 1px solid var(--border-default);
    font-size: 11px;
    color: var(--text-dimmed);
  }

  .palette-footer kbd {
    background: transparent;
    border: 1px solid var(--border-default);
    border-radius: 3px;
    padding: 1px 5px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
  }
</style>
