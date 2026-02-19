<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { formatDate } from '$lib/utils/format';
	import type { PageData } from './$types';
	import type { FeedEvent } from '$lib/types/api';

	let { data }: { data: PageData } = $props();

	// ─── Auto-refresh ────────────────────────────────────────────────
	let lastRefresh = $state(new Date());

	$effect(() => {
		const timer = setInterval(() => {
			invalidateAll();
			lastRefresh = new Date();
		}, 300000);
		return () => clearInterval(timer);
	});

	function fmtTime(d: Date): string {
		return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}

	// ─── Feed state ──────────────────────────────────────────────────
	let activeSource = $state<string>('all');

	const sourceFilters = [
		{ key: 'all', label: 'All' },
		{ key: 'congress', label: 'GOV' },
		{ key: 'ark', label: 'ARK' },
		{ key: 'darkpool', label: 'DP' },
		{ key: 'insider', label: 'INS' },
		{ key: 'institution', label: '13F' },
	];

	const sourceColors: Record<string, string> = {
		congress: 'source-congress',
		ark: 'source-ark',
		darkpool: 'source-darkpool',
		insider: 'source-insider',
		institution: 'source-institution',
	};

	const sourceLabels: Record<string, string> = {
		congress: 'GOV',
		ark: 'ARK',
		darkpool: 'DP',
		insider: 'INS',
		institution: '13F',
	};

	let filteredEvents = $derived(
		(data.feed?.events ?? []).filter(
			(e: FeedEvent) => activeSource === 'all' || e.source === activeSource
		)
	);

	// Group events by date
	let groupedEvents = $derived(() => {
		const groups: { date: string; label: string; events: FeedEvent[] }[] = [];
		const map = new Map<string, FeedEvent[]>();

		for (const e of filteredEvents) {
			const d = e.date || 'Unknown';
			if (!map.has(d)) map.set(d, []);
			map.get(d)!.push(e);
		}

		for (const [date, events] of map) {
			groups.push({
				date,
				label: formatDate(date, 'long'),
				events,
			});
		}

		return groups;
	});

	// ─── Ranking helpers ─────────────────────────────────────────────
	let sortedSignals = $derived(data.signals?.data ?? []);

	function getSourceTags(signal: {
		congress_score: number;
		ark_score: number;
		darkpool_score: number;
		institution_score: number;
		insider_score: number;
	}): string[] {
		const tags: string[] = [];
		if (signal.congress_score > 0) tags.push('congress');
		if (signal.ark_score > 0) tags.push('ark');
		if (signal.darkpool_score > 0) tags.push('darkpool');
		if (signal.institution_score > 0) tags.push('institution');
		if (signal.insider_score > 0) tags.push('insider');
		return tags;
	}

	function scoreColor(score: number): string {
		if (score >= 80) return 'var(--green)';
		if (score >= 60) return 'var(--blue)';
		if (score >= 40) return 'var(--amber)';
		return 'var(--text-muted)';
	}

	function convictionBar(value: number): string {
		return `${Math.min(value, 100)}%`;
	}

	function formatValue(val: number | null): string {
		if (!val) return '';
		if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
		if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
		if (val >= 1e3) return `$${(val / 1e3).toFixed(0)}K`;
		return `$${val.toFixed(0)}`;
	}
</script>

<svelte:head>
	<title>Dashboard — Meridian</title>
</svelte:head>

<div class="space-y-6">

	<!-- ── Header ──────────────────────────────────────────────────────── -->
	<div class="dash-header">
		<div>
			<h1 class="dash-title">Smart Money Dashboard</h1>
			<p class="dash-subtitle">Where smart money converges</p>
		</div>
		<div class="dash-refresh">
			<span>Auto-refresh 5m</span>
			<span>Last: {fmtTime(lastRefresh)}</span>
		</div>
	</div>

	<!-- ── Error State ─────────────────────────────────────────────────── -->
	{#if data.error}
		<Card>
			{#snippet children()}
				<div class="text-center py-8">
					<p class="error-text">Error loading dashboard data</p>
					<p class="error-detail">{data.error}</p>
				</div>
			{/snippet}
		</Card>
	{:else}

		<!-- ── Split Layout ────────────────────────────────────────────── -->
		<div class="split-layout">

			<!-- ── Left: Signal Feed ───────────────────────────────────── -->
			<div class="feed-col">
				<div class="section-label">SIGNAL FEED</div>

				<!-- Source filter tabs -->
				<div class="feed-filters">
					{#each sourceFilters as f}
						<button
							class="feed-filter-btn {activeSource === f.key ? 'active' : ''}"
							onclick={() => (activeSource = f.key)}
						>
							{f.label}
						</button>
					{/each}
				</div>

				<!-- Feed events grouped by date -->
				{#if filteredEvents.length === 0}
					<Card>
						{#snippet children()}
							<div class="text-center py-8">
								<p class="text-sm" style="color: var(--text-muted);">No events in this period</p>
							</div>
						{/snippet}
					</Card>
				{:else}
					{#each groupedEvents() as group}
						<div class="feed-date-group">
							<div class="feed-date-header">{group.label}</div>
							{#each group.events as event}
								<a href="/ticker/{event.ticker}" class="feed-item {event.significance === 'high' ? 'feed-item-high' : ''}">
									<div class="feed-item-top">
										<span class="feed-source-badge {sourceColors[event.source]}">{sourceLabels[event.source]}</span>
										<span class="feed-ticker">{event.ticker}</span>
										{#if event.company}
											<span class="feed-company">{event.company}</span>
										{/if}
										<div class="feed-item-right">
											{#if event.significance === 'high'}
												<span class="feed-sig-badge sig-high">HIGH</span>
											{:else if event.significance === 'medium'}
												<span class="feed-sig-badge sig-medium">MED</span>
											{/if}
											{#if event.sentiment === 'bullish'}
												<Badge variant="bullish">↑</Badge>
											{:else if event.sentiment === 'bearish'}
												<Badge variant="bearish">↓</Badge>
											{/if}
										</div>
									</div>
									<div class="feed-item-body">
										<p class="feed-headline">{event.headline}</p>
										<p class="feed-desc">{event.description}</p>
									</div>
								</a>
							{/each}
						</div>
					{/each}
				{/if}
			</div>

			<!-- ── Right: Meridian Ranking ─────────────────────────────── -->
			<div class="ranking-col">
				<div class="section-label">MERIDIAN RANKING</div>
				<div class="ranking-panel">
					{#if sortedSignals.length === 0}
						<div class="text-center py-6">
							<p class="text-sm" style="color: var(--text-muted);">No rankings yet</p>
						</div>
					{:else}
						<div class="ranking-list">
							{#each sortedSignals.slice(0, 20) as signal, i}
								<a href="/ticker/{signal.ticker}" class="ranking-row">
									<span class="ranking-rank">#{i + 1}</span>
									<div class="ranking-info">
										<span class="ranking-ticker">{signal.ticker}</span>
										<div class="ranking-sources">
											{#each getSourceTags(signal) as src}
												<span class="ranking-src-dot {sourceColors[src]}"></span>
											{/each}
										</div>
									</div>
									<div class="ranking-score-area">
										<div class="ranking-bar-track">
											<div
												class="ranking-bar-fill"
												style="width: {convictionBar(signal.score)}; background: {scoreColor(signal.score)};"
											></div>
										</div>
										<span class="ranking-score" style="color: {scoreColor(signal.score)};">
											{signal.score.toFixed(0)}
										</span>
									</div>
								</a>
							{/each}
						</div>
						{#if sortedSignals.length > 20}
							<a href="/signals" class="ranking-see-all">
								See all rankings →
							</a>
						{/if}
					{/if}
				</div>
			</div>
		</div>

	{/if}
</div>

<style>
	/* ── Header ──────────────────────────────────────────────────── */
	.dash-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
	}

	.dash-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--text-primary);
		line-height: 1.3;
	}

	.dash-subtitle {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 2px;
	}

	.dash-refresh {
		font-size: 11px;
		color: var(--text-muted);
		text-align: right;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.section-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-muted);
		margin-bottom: 8px;
	}

	.error-text {
		color: var(--color-down);
		margin-bottom: 8px;
		font-weight: 500;
	}

	.error-detail {
		font-size: 13px;
		color: var(--text-muted);
	}

	/* ── Split Layout ────────────────────────────────────────────── */
	.split-layout {
		display: flex;
		gap: 24px;
	}

	.feed-col {
		flex: 3;
		min-width: 0;
	}

	.ranking-col {
		flex: 2;
		min-width: 0;
	}

	@media (max-width: 768px) {
		.split-layout {
			flex-direction: column;
		}
	}

	/* ── Feed Filters ────────────────────────────────────────────── */
	.feed-filters {
		display: flex;
		gap: 4px;
		margin-bottom: 16px;
		flex-wrap: wrap;
	}

	.feed-filter-btn {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.04em;
		padding: 5px 12px;
		border-radius: 6px;
		border: 1px solid var(--border-default);
		background: var(--bg-surface);
		color: var(--text-muted);
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.feed-filter-btn:hover {
		border-color: var(--border-hover);
		color: var(--text-primary);
	}

	.feed-filter-btn.active {
		background: var(--bg-elevated);
		border-color: var(--border-hover);
		color: var(--text-primary);
	}

	/* ── Feed Date Groups ────────────────────────────────────────── */
	.feed-date-group {
		margin-bottom: 16px;
	}

	.feed-date-header {
		font-size: 12px;
		font-weight: 600;
		color: var(--text-secondary);
		margin-bottom: 8px;
		padding-left: 4px;
	}

	/* ── Feed Items ──────────────────────────────────────────────── */
	.feed-item {
		display: block;
		padding: 12px 14px;
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 10px;
		text-decoration: none;
		transition: border-color 0.1s ease;
		margin-bottom: 8px;
		border-left: 3px solid transparent;
	}

	.feed-item:hover {
		border-color: var(--border-hover);
	}

	.feed-item-high {
		border-left-color: var(--amber);
	}

	.feed-item-top {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 6px;
	}

	.feed-item-right {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
	}

	.feed-source-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.04em;
		padding: 2px 6px;
		border-radius: 4px;
		flex-shrink: 0;
	}

	.source-congress { background: rgba(245, 158, 11, 0.15); color: var(--amber); }
	.source-ark      { background: rgba(96, 165, 250, 0.15); color: var(--blue); }
	.source-darkpool { background: rgba(168, 85, 247, 0.15); color: #a855f7; }
	.source-insider  { background: rgba(249, 115, 22, 0.15); color: #f97316; }
	.source-institution { background: rgba(34, 197, 94, 0.15); color: var(--green); }

	.feed-ticker {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-weight: 700;
		font-size: 13px;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	.feed-company {
		font-size: 11px;
		color: var(--text-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: 120px;
	}

	.feed-sig-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 0.05em;
		padding: 1px 5px;
		border-radius: 3px;
	}

	.sig-high {
		background: rgba(245, 158, 11, 0.15);
		color: var(--amber);
	}

	.sig-medium {
		background: rgba(255, 255, 255, 0.06);
		color: var(--text-dimmed);
	}

	.feed-item-body {
		padding-left: 1px;
	}

	.feed-headline {
		font-size: 13px;
		font-weight: 500;
		color: var(--text-secondary);
		line-height: 1.4;
	}

	.feed-desc {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 2px;
		line-height: 1.4;
	}

	/* ── Ranking Panel ───────────────────────────────────────────── */
	.ranking-panel {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		overflow: hidden;
		position: sticky;
		top: 24px;
	}

	.ranking-list {
		padding: 8px 0;
	}

	.ranking-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 16px;
		text-decoration: none;
		transition: background 0.1s ease;
	}

	.ranking-row:hover {
		background: var(--bg-elevated);
	}

	.ranking-rank {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		width: 26px;
		text-align: right;
		flex-shrink: 0;
	}

	.ranking-info {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
		flex: 1;
	}

	.ranking-ticker {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-weight: 700;
		font-size: 13px;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	.ranking-sources {
		display: flex;
		gap: 3px;
		align-items: center;
	}

	.ranking-src-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.ranking-src-dot.source-congress { background: var(--amber); }
	.ranking-src-dot.source-ark      { background: var(--blue); }
	.ranking-src-dot.source-darkpool { background: #a855f7; }
	.ranking-src-dot.source-insider  { background: #f97316; }
	.ranking-src-dot.source-institution { background: var(--green); }

	.ranking-score-area {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}

	.ranking-bar-track {
		width: 60px;
		height: 4px;
		background: var(--bg-elevated);
		border-radius: 2px;
		overflow: hidden;
	}

	.ranking-bar-fill {
		height: 100%;
		border-radius: 2px;
		transition: width 0.3s ease;
	}

	.ranking-score {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 13px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		width: 28px;
		text-align: right;
	}

	.ranking-see-all {
		display: block;
		text-align: center;
		padding: 12px;
		font-size: 13px;
		color: var(--blue);
		text-decoration: none;
		border-top: 1px solid var(--border-default);
		transition: color 0.1s ease;
	}

	.ranking-see-all:hover {
		color: var(--text-secondary);
	}
</style>
