<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { formatDate } from '$lib/utils/format';
	import type { PageData } from './$types';
	import type { FeedEvent } from '$lib/types/api';

	let { data }: { data: PageData } = $props();

	// ─── Source filter state ─────────────────────────────────────────
	let activeSource = $state<string>('all');

	const sourceFilters = [
		{ key: 'all', label: 'All' },
		{ key: 'congress', label: 'Congress' },
		{ key: 'ark', label: 'ARK' },
		{ key: 'darkpool', label: 'Dark Pool' },
		{ key: 'insider', label: 'Insider' },
		{ key: 'institution', label: 'Institution' },
		{ key: 'superinvestor', label: 'Super' },
		{ key: 'short_interest', label: 'Short' },
	];

	const sourceColors: Record<string, string> = {
		congress: 'source-congress',
		ark: 'source-ark',
		darkpool: 'source-darkpool',
		insider: 'source-insider',
		institution: 'source-institution',
		superinvestor: 'source-superinvestor',
		short_interest: 'source-short',
	};

	const sourceLabels: Record<string, string> = {
		congress: 'GOV',
		ark: 'ARK',
		darkpool: 'DP',
		insider: 'INS',
		institution: '13F',
		superinvestor: 'SUPER',
		short_interest: 'SHORT',
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

	function sigDotColor(sig: string): string {
		if (sig === 'high') return 'var(--amber)';
		if (sig === 'medium') return 'var(--blue)';
		return 'var(--text-dimmed)';
	}
</script>

<svelte:head>
	<title>Smart Money Feed — Meridian</title>
</svelte:head>

<div class="feed-page">

	<!-- Header -->
	<div class="feed-header">
		<div>
			<h1 class="feed-title">Smart Money Feed</h1>
			<p class="feed-subtitle">Real-time actions from congress, institutions, and insiders</p>
		</div>
		<div class="feed-meta">
			<span class="feed-count">{filteredEvents.length} events</span>
		</div>
	</div>

	<!-- Error state -->
	{#if data.error}
		<Card>
			{#snippet children()}
				<div class="text-center py-8">
					<p class="error-text">Error loading feed</p>
					<p class="error-detail">{data.error}</p>
				</div>
			{/snippet}
		</Card>
	{:else}

		<!-- Source filter pills -->
		<div class="feed-filters">
			{#each sourceFilters as f}
				<button
					class="feed-filter-pill {activeSource === f.key ? 'active' : ''}"
					onclick={() => (activeSource = f.key)}
				>
					{f.label}
				</button>
			{/each}
		</div>

		<!-- Feed events grouped by date -->
		{#if filteredEvents.length === 0}
			<div class="feed-empty">
				<p>No events found</p>
				<p class="feed-empty-sub">Try changing the filter or check back later</p>
			</div>
		{:else}
			{#each groupedEvents() as group}
				<div class="feed-date-group">
					<div class="feed-date-header">{group.label}</div>
					{#each group.events as event}
						<a href="/ticker/{event.ticker}" class="feed-card {event.significance === 'high' ? 'feed-card-high' : ''}">
							<div class="feed-card-top">
								<div class="feed-card-left">
									<span class="feed-source-badge {sourceColors[event.source]}">{sourceLabels[event.source] || event.source.toUpperCase()}</span>
									<span class="feed-ticker">{event.ticker}</span>
									{#if event.company}
										<span class="feed-company">{event.company}</span>
									{/if}
								</div>
								<div class="feed-card-right">
									<span class="feed-sig-dot" style="background: {sigDotColor(event.significance)};"></span>
									{#if event.sentiment === 'bullish'}
										<Badge variant="bullish">↑</Badge>
									{:else if event.sentiment === 'bearish'}
										<Badge variant="bearish">↓</Badge>
									{/if}
								</div>
							</div>
							<div class="feed-card-body">
								<p class="feed-headline">{event.headline}</p>
								{#if event.description}
									<p class="feed-desc">{event.description}</p>
								{/if}
							</div>
						</a>
					{/each}
				</div>
			{/each}
		{/if}

	{/if}
</div>

<style>
	.feed-page {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	/* ── Header ──────────────────────────────────────────────────── */
	.feed-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
	}

	.feed-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--text-primary);
		line-height: 1.3;
	}

	.feed-subtitle {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 2px;
	}

	.feed-meta {
		font-size: 11px;
		color: var(--text-muted);
		text-align: right;
	}

	.feed-count {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
	}

	/* ── Filters ─────────────────────────────────────────────────── */
	.feed-filters {
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
		padding-bottom: 4px;
	}

	.feed-filter-pill {
		font-size: 12px;
		font-weight: 500;
		padding: 6px 14px;
		border-radius: 20px;
		border: 1px solid var(--border-default);
		background: var(--bg-surface);
		color: var(--text-muted);
		cursor: pointer;
		transition: all 0.15s ease;
		white-space: nowrap;
	}

	.feed-filter-pill:hover {
		border-color: var(--border-hover);
		color: var(--text-primary);
	}

	.feed-filter-pill.active {
		background: var(--bg-elevated);
		border-color: var(--border-hover);
		color: var(--text-primary);
	}

	/* ── Date groups ─────────────────────────────────────────────── */
	.feed-date-group {
		margin-bottom: 8px;
	}

	.feed-date-header {
		font-size: 12px;
		font-weight: 600;
		color: var(--text-secondary);
		margin-bottom: 8px;
		padding-left: 4px;
	}

	/* ── Cards ────────────────────────────────────────────────────── */
	.feed-card {
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

	.feed-card:hover {
		border-color: var(--border-hover);
	}

	.feed-card-high {
		border-left-color: var(--amber);
	}

	.feed-card-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 6px;
	}

	.feed-card-left {
		display: flex;
		align-items: center;
		gap: 8px;
		min-width: 0;
		flex: 1;
	}

	.feed-card-right {
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
	.source-superinvestor { background: rgba(236, 72, 153, 0.15); color: #ec4899; }
	.source-short    { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

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
		max-width: 140px;
	}

	@media (max-width: 480px) {
		.feed-company {
			max-width: 80px;
		}
	}

	.feed-sig-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.feed-card-body {
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

	/* ── Empty state ─────────────────────────────────────────────── */
	.feed-empty {
		text-align: center;
		padding: 48px 16px;
		color: var(--text-muted);
		font-size: 14px;
	}

	.feed-empty-sub {
		font-size: 12px;
		color: var(--text-dimmed);
		margin-top: 4px;
	}

	/* ── Error ────────────────────────────────────────────────────── */
	.error-text {
		color: var(--color-down);
		margin-bottom: 8px;
		font-weight: 500;
	}

	.error-detail {
		font-size: 13px;
		color: var(--text-muted);
	}
</style>
