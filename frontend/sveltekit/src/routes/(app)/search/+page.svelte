<script lang="ts">
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { fetchApi } from '$lib/api';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let query = $state('');
	let results = $state<{ ticker: string; company: string }[]>([]);
	let loading = $state(false);
	let searched = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout>;

	// Recent searches from localStorage
	let recentSearches = $state<string[]>([]);

	if (browser) {
		try {
			const stored = localStorage.getItem('meridian_recent_searches');
			if (stored) recentSearches = JSON.parse(stored);
		} catch {}
	}

	function saveRecent(ticker: string) {
		recentSearches = [ticker, ...recentSearches.filter(t => t !== ticker)].slice(0, 10);
		if (browser) {
			localStorage.setItem('meridian_recent_searches', JSON.stringify(recentSearches));
		}
	}

	function clearRecent() {
		recentSearches = [];
		if (browser) {
			localStorage.removeItem('meridian_recent_searches');
		}
	}

	function handleInput() {
		clearTimeout(debounceTimer);
		const q = query.trim();
		if (q.length < 1) {
			results = [];
			searched = false;
			return;
		}
		debounceTimer = setTimeout(() => doSearch(q), 200);
	}

	async function doSearch(q: string) {
		loading = true;
		searched = true;
		try {
			const resp = await fetchApi<{ results: { ticker: string; company: string }[] }>(`/ticker/search?q=${encodeURIComponent(q)}`);
			results = resp.results ?? [];
		} catch {
			results = [];
		} finally {
			loading = false;
		}
	}

	function goToTicker(symbol: string) {
		saveRecent(symbol);
		goto(`/ticker/${symbol}`);
	}

	function scoreColor(score: number): string {
		if (score >= 80) return 'var(--green)';
		if (score >= 60) return 'var(--blue)';
		if (score >= 40) return 'var(--amber)';
		return 'var(--text-muted)';
	}

	// Source colors for trending badges
	const sourceColors: Record<string, string> = {
		congress: 'source-congress',
		ark: 'source-ark',
		darkpool: 'source-darkpool',
		insider: 'source-insider',
		institution: 'source-institution',
	};

	function getSourceTags(signal: any): string[] {
		const tags: string[] = [];
		if (signal.congress_score > 0) tags.push('congress');
		if (signal.ark_score > 0) tags.push('ark');
		if (signal.darkpool_score > 0) tags.push('darkpool');
		if (signal.institution_score > 0) tags.push('institution');
		if (signal.insider_score > 0) tags.push('insider');
		return tags;
	}
</script>

<svelte:head>
	<title>Search — Meridian</title>
</svelte:head>

<div class="search-page">

	<!-- Search input -->
	<div class="search-input-wrap">
		<svg class="search-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<circle cx="11" cy="11" r="8" />
			<line x1="21" y1="21" x2="16.65" y2="16.65" />
		</svg>
		<input
			type="text"
			class="search-input"
			placeholder="Search tickers... AAPL, NVDA, TSLA"
			bind:value={query}
			oninput={handleInput}
			autofocus
		/>
		{#if query}
			<button class="search-clear" onclick={() => { query = ''; results = []; searched = false; }}>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<line x1="18" y1="6" x2="6" y2="18" />
					<line x1="6" y1="6" x2="18" y2="18" />
				</svg>
			</button>
		{/if}
	</div>

	<!-- Search results -->
	{#if searched && query.trim().length > 0}
		<div class="search-results">
			{#if loading}
				<div class="search-loading">Searching...</div>
			{:else if results.length === 0}
				<div class="search-no-results">
					<p>No tickers matching "{query}"</p>
				</div>
			{:else}
				{#each results as r}
					<button class="search-result-row" onclick={() => goToTicker(r.ticker)}>
						<span class="result-ticker">{r.ticker}</span>
						<span class="result-company">{r.company || ''}</span>
						<svg class="result-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<polyline points="9 18 15 12 9 6" />
						</svg>
					</button>
				{/each}
			{/if}
		</div>
	{:else}

		<!-- Recent searches -->
		{#if recentSearches.length > 0}
			<div class="search-section">
				<div class="section-header">
					<span class="section-label">RECENT</span>
					<button class="clear-btn" onclick={clearRecent}>Clear</button>
				</div>
				<div class="recent-list">
					{#each recentSearches as ticker}
						<button class="recent-chip" onclick={() => goToTicker(ticker)}>
							{ticker}
						</button>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Trending -->
		{#if data.trending.length > 0}
			<div class="search-section">
				<div class="section-header">
					<span class="section-label">TRENDING BY SCORE</span>
				</div>
				<div class="trending-list">
					{#each data.trending as signal, i}
						<a href="/ticker/{signal.ticker}" class="trending-row" onclick={() => saveRecent(signal.ticker)}>
							<span class="trending-rank">#{i + 1}</span>
							<div class="trending-info">
								<span class="trending-ticker">{signal.ticker}</span>
								<span class="trending-company">{signal.company || ''}</span>
							</div>
							<div class="trending-sources">
								{#each getSourceTags(signal) as src}
									<span class="trending-src-dot {sourceColors[src]}"></span>
								{/each}
							</div>
							<span class="trending-score" style="color: {scoreColor(signal.score)};">
								{signal.score.toFixed(0)}
							</span>
						</a>
					{/each}
				</div>
			</div>
		{/if}

	{/if}
</div>

<style>
	.search-page {
		display: flex;
		flex-direction: column;
		gap: 20px;
		max-width: 640px;
		margin: 0 auto;
	}

	/* ── Search Input ────────────────────────────────────────────── */
	.search-input-wrap {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-input-icon {
		position: absolute;
		left: 14px;
		width: 20px;
		height: 20px;
		color: var(--text-dimmed);
		pointer-events: none;
	}

	.search-input {
		width: 100%;
		padding: 14px 44px 14px 44px;
		font-size: 16px;
		color: var(--text-primary);
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		outline: none;
		transition: border-color 0.15s ease;
	}

	.search-input::placeholder {
		color: var(--text-dimmed);
	}

	.search-input:focus {
		border-color: var(--border-hover);
	}

	.search-clear {
		position: absolute;
		right: 12px;
		width: 20px;
		height: 20px;
		color: var(--text-dimmed);
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.search-clear svg {
		width: 16px;
		height: 16px;
	}

	.search-clear:hover {
		color: var(--text-primary);
	}

	/* ── Search Results ──────────────────────────────────────────── */
	.search-results {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		overflow: hidden;
	}

	.search-loading {
		text-align: center;
		padding: 24px;
		color: var(--text-muted);
		font-size: 13px;
	}

	.search-no-results {
		text-align: center;
		padding: 32px;
		color: var(--text-muted);
		font-size: 13px;
	}

	.search-result-row {
		display: flex;
		align-items: center;
		gap: 10px;
		width: 100%;
		padding: 12px 16px;
		background: none;
		border: none;
		border-bottom: 1px solid var(--border-default);
		cursor: pointer;
		text-align: left;
		transition: background 0.1s ease;
	}

	.search-result-row:last-child {
		border-bottom: none;
	}

	.search-result-row:hover {
		background: var(--bg-elevated);
	}

	.result-ticker {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-weight: 700;
		font-size: 14px;
		color: var(--text-primary);
		letter-spacing: 0.02em;
		flex-shrink: 0;
		min-width: 60px;
	}

	.result-company {
		font-size: 13px;
		color: var(--text-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		flex: 1;
	}

	.result-arrow {
		width: 16px;
		height: 16px;
		color: var(--text-dimmed);
		flex-shrink: 0;
	}

	/* ── Sections ────────────────────────────────────────────────── */
	.search-section {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.section-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 4px;
	}

	.section-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-muted);
	}

	.clear-btn {
		font-size: 11px;
		color: var(--text-dimmed);
		background: none;
		border: none;
		cursor: pointer;
		padding: 2px 6px;
		border-radius: 4px;
	}

	.clear-btn:hover {
		color: var(--text-primary);
	}

	/* ── Recent ──────────────────────────────────────────────────── */
	.recent-list {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.recent-chip {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 12px;
		font-weight: 600;
		padding: 6px 14px;
		border-radius: 8px;
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.recent-chip:hover {
		border-color: var(--border-hover);
		color: var(--text-primary);
	}

	/* ── Trending ────────────────────────────────────────────────── */
	.trending-list {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		overflow: hidden;
	}

	.trending-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 16px;
		text-decoration: none;
		transition: background 0.1s ease;
		border-bottom: 1px solid var(--border-default);
	}

	.trending-row:last-child {
		border-bottom: none;
	}

	.trending-row:hover {
		background: var(--bg-elevated);
	}

	.trending-rank {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		width: 24px;
		text-align: right;
		flex-shrink: 0;
	}

	.trending-info {
		flex: 1;
		min-width: 0;
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.trending-ticker {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-weight: 700;
		font-size: 13px;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	.trending-company {
		font-size: 11px;
		color: var(--text-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.trending-sources {
		display: flex;
		gap: 3px;
		align-items: center;
		flex-shrink: 0;
	}

	.trending-src-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.trending-src-dot.source-congress { background: var(--amber); }
	.trending-src-dot.source-ark { background: var(--blue); }
	.trending-src-dot.source-darkpool { background: #a855f7; }
	.trending-src-dot.source-insider { background: #f97316; }
	.trending-src-dot.source-institution { background: var(--green); }

	.trending-score {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 14px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		width: 28px;
		text-align: right;
		flex-shrink: 0;
	}
</style>
