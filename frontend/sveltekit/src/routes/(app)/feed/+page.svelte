<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import { formatDate } from '$lib/utils/format';
	import type { PageData } from './$types';
	import type { FeedEvent, FeedResponse } from '$lib/types/api';
	import { api } from '$lib/api';

	let { data }: { data: PageData } = $props();

	// ─── Source filter state ─────────────────────────────────────────
	let activeSource = $state<string>('all');
	let sourceEvents = $state<FeedEvent[]>([]);
	let sourceLoading = $state<boolean>(false);

	// Per-source time windows (days) — each source has appropriate lookback
	const sourceDays: Record<string, number> = {
		all: 30,
		congress: 90,       // Congress disclosure delay means trades show up 30-45 days late
		ark: 30,
		darkpool: 30,
		insider: 30,
		institution: 180,   // 13F filings are quarterly
		superinvestor: 180, // Quarterly data from Dataroma
		short_interest: 60, // FINRA settlement dates, bi-monthly
	};

	// Fetch events when source changes
	async function loadSource(source: string) {
		if (source === 'all') {
			sourceEvents = data.feed?.events ?? [];
			return;
		}
		sourceLoading = true;
		try {
			const days = sourceDays[source] || 30;
			const resp = await api.ranking.feed({ source, days, limit: 200 }) as FeedResponse;
			sourceEvents = resp?.events ?? [];
		} catch (e) {
			console.error('Feed source load error:', e);
			sourceEvents = [];
		} finally {
			sourceLoading = false;
		}
	}

	// Initialize with all events
	$effect(() => {
		if (data.feed?.events) {
			sourceEvents = data.feed.events;
		}
	});

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
		congress: 'bg-[var(--amber)]/20 text-[var(--amber)]',
		ark: 'bg-[var(--blue)]/20 text-[var(--blue)]',
		darkpool: 'bg-purple-500/20 text-purple-400',
		insider: 'bg-orange-500/20 text-orange-400',
		institution: 'bg-[var(--green)]/20 text-[var(--green)]',
		superinvestor: 'bg-cyan-500/20 text-cyan-400',
		short_interest: 'bg-red-500/20 text-red-400',
	};

	const sourceLabels: Record<string, string> = {
		congress: 'GOV',
		ark: 'ARK',
		darkpool: 'DP',
		insider: 'INS',
		institution: '13F',
		superinvestor: 'SUP',
		short_interest: 'SI',
	};

	// Use sourceEvents directly — already filtered server-side
	let filteredEvents = $derived(sourceEvents);

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

	function sigStyle(sig: string): string {
		if (sig === 'high') return 'border-left: 3px solid var(--amber)';
		if (sig === 'medium') return 'border-left: 3px solid var(--blue)';
		return 'border-left: 3px solid transparent';
	}

	// Stats
	const highSigCount = $derived(() => filteredEvents.filter(e => e.significance === 'high').length);
	const bullishCount = $derived(() => filteredEvents.filter(e => e.sentiment === 'bullish').length);
	const bearishCount = $derived(() => filteredEvents.filter(e => e.sentiment === 'bearish').length);

	let guideOpen = $state(false);
</script>

<svelte:head>
	<title>Smart Money Feed — Meridian</title>
</svelte:head>

<div class="space-y-6">

	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">Smart Money Feed</h1>
		<p class="text-[var(--text-secondary)]">Real-time actions from congress, institutions, and insiders</p>
		<p class="text-caption text-[var(--text-dimmed)] mt-2">
			{#if sourceLoading}
				Loading...
			{:else}
				{filteredEvents.length} events · Last {sourceDays[activeSource] || 30} days
			{/if}
		</p>
	</div>

	<!-- Error state -->
	{#if data.error}
		<Card>
			{#snippet children()}
				<div class="text-center py-8">
					<p class="text-[var(--color-down)] font-medium mb-2">Error loading feed</p>
					<p class="text-sm text-[var(--text-muted)]">{data.error}</p>
				</div>
			{/snippet}
		</Card>
	{:else}

		<!-- Stats -->
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<Card hover>
				{#snippet children()}
					<div class="text-center">
						<p class="text-label mb-2">Total Events</p>
						<p class="text-data-lg">{filteredEvents.length}</p>
					</div>
				{/snippet}
			</Card>
			<Card hover>
				{#snippet children()}
					<div class="text-center">
						<p class="text-label mb-2">High Signal</p>
						<p class="text-data-lg text-[var(--amber)]">{highSigCount()}</p>
					</div>
				{/snippet}
			</Card>
			<Card hover>
				{#snippet children()}
					<div class="text-center">
						<p class="text-label mb-2">Bullish</p>
						<p class="text-data-lg text-[var(--green)]">{bullishCount()}</p>
					</div>
				{/snippet}
			</Card>
			<Card hover>
				{#snippet children()}
					<div class="text-center">
						<p class="text-label mb-2">Bearish</p>
						<p class="text-data-lg text-[var(--color-down)]">{bearishCount()}</p>
					</div>
				{/snippet}
			</Card>
		</div>

		<!-- Reading Guide (collapsible) -->
		<div class="rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] overflow-hidden">
			<button
				onclick={() => (guideOpen = !guideOpen)}
				class="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-[var(--bg-elevated)] transition-colors"
				aria-expanded={guideOpen}
			>
				<div class="flex items-center gap-2">
					<span class="text-base font-semibold text-[var(--text-primary)]">How to Read the Feed</span>
					<span class="text-xs text-[var(--text-muted)] bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded px-2 py-0.5">Guide</span>
				</div>
				<svg
					class="w-4 h-4 text-[var(--text-muted)] transition-transform duration-200 {guideOpen ? 'rotate-180' : ''}"
					fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
				</svg>
			</button>

			{#if guideOpen}
				<div class="px-5 pb-5 border-t border-[var(--border-default)] space-y-5">
					<!-- Source badges -->
					<div class="pt-4">
						<h4 class="text-sm font-semibold text-[var(--text-primary)] mb-2">Source Badges</h4>
						<p class="text-xs text-[var(--text-muted)] mb-3">Each event is tagged with where the signal originated. Tap any badge to learn more:</p>
						<div class="flex flex-wrap gap-2 text-sm">
							<a href="/knowledge/congress-trading-alpha" class="px-2 py-1 rounded bg-[var(--amber)]/10 border border-[var(--amber)]/20 text-[var(--amber)] hover:bg-[var(--amber)]/20 transition-colors">🏛️ GOV — Congress trades →</a>
							<a href="/knowledge/ark-disruptive-innovation" class="px-2 py-1 rounded bg-[var(--blue)]/10 border border-[var(--blue)]/20 text-[var(--blue)] hover:bg-[var(--blue)]/20 transition-colors">🚀 ARK — ARK Invest →</a>
							<a href="/knowledge/dark-pool-activity" class="px-2 py-1 rounded bg-purple-500/10 border border-purple-500/20 text-purple-400 hover:bg-purple-500/20 transition-colors">🌑 DP — Dark Pool →</a>
							<a href="/knowledge/insider-buying-signals" class="px-2 py-1 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400 hover:bg-orange-500/20 transition-colors">👔 INS — Insider trades →</a>
							<a href="/knowledge/13f-institutional-tracking" class="px-2 py-1 rounded bg-[var(--green)]/10 border border-[var(--green)]/20 text-[var(--green)] hover:bg-[var(--green)]/20 transition-colors">🏦 13F — Institutional filings →</a>
							<a href="/knowledge/superinvestor-tracking" class="px-2 py-1 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20 transition-colors">💎 SUP — Superinvestors →</a>
							<a href="/knowledge/short-interest-analysis" class="px-2 py-1 rounded bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-colors">📉 SI — Short Interest →</a>
						</div>
					</div>

					<!-- Signal strength -->
					<div>
						<h4 class="text-sm font-semibold text-[var(--text-primary)] mb-2">Signal Strength</h4>
						<p class="text-xs text-[var(--text-muted)] mb-3">The colored dot and left border indicate how significant the event is:</p>
						<div class="space-y-2 text-sm">
							<div class="flex items-center gap-3">
								<span class="w-3 h-3 rounded-full bg-[var(--amber)] flex-shrink-0"></span>
								<div>
									<span class="text-[var(--amber)] font-medium">High</span>
									<span class="text-[var(--text-muted)]"> — Large volume, unusual activity, or high-profile actor. Amber left border.</span>
								</div>
							</div>
							<div class="flex items-center gap-3">
								<span class="w-3 h-3 rounded-full bg-[var(--blue)] flex-shrink-0"></span>
								<div>
									<span class="text-[var(--blue)] font-medium">Medium</span>
									<span class="text-[var(--text-muted)]"> — Notable but not extreme. Blue left border.</span>
								</div>
							</div>
							<div class="flex items-center gap-3">
								<span class="w-3 h-3 rounded-full bg-[var(--text-dimmed)] flex-shrink-0"></span>
								<div>
									<span class="text-[var(--text-secondary)] font-medium">Low</span>
									<span class="text-[var(--text-muted)]"> — Routine activity, included for completeness.</span>
								</div>
							</div>
						</div>
					</div>

					<!-- Sentiment arrows -->
					<div>
						<h4 class="text-sm font-semibold text-[var(--text-primary)] mb-2">Sentiment Direction</h4>
						<p class="text-xs text-[var(--text-muted)] mb-3">The arrow badge shows the directional bias of the event:</p>
						<div class="space-y-2 text-sm">
							<div class="flex items-center gap-3">
								<span class="px-2 py-0.5 rounded text-xs font-bold bg-[var(--green)]/20 text-[var(--green)]">↑</span>
								<span class="text-[var(--text-muted)]"><span class="text-[var(--green)] font-medium">Bullish</span> — Buying activity, accumulation, or positive positioning</span>
							</div>
							<div class="flex items-center gap-3">
								<span class="px-2 py-0.5 rounded text-xs font-bold bg-[var(--color-down)]/20 text-[var(--color-down)]">↓</span>
								<span class="text-[var(--text-muted)]"><span class="text-[var(--color-down)] font-medium">Bearish</span> — Selling, reduction, or negative positioning</span>
							</div>
							<div class="flex items-center gap-3">
								<span class="text-xs text-[var(--text-dimmed)] px-2">—</span>
								<span class="text-[var(--text-muted)]"><span class="text-[var(--text-secondary)] font-medium">Neutral</span> — No clear directional bias (no arrow shown)</span>
							</div>
						</div>
					</div>

					<!-- Tip -->
					<div class="flex gap-3 px-4 py-3 rounded-lg bg-[var(--blue)]/5 border border-[var(--blue)]/20">
						<span class="text-[var(--blue)] flex-shrink-0 mt-0.5">💡</span>
						<p class="text-xs text-[var(--text-muted)] leading-relaxed">
							<span class="font-semibold text-[var(--text-secondary)]">Tip:</span>
							Click any event card to view the full ticker detail page with all smart money signals, conviction scores, and data tables.
						</p>
					</div>
				</div>
			{/if}
		</div>

		<!-- Source filter pills -->
		<div class="flex gap-2 flex-wrap">
			{#each sourceFilters as f}
				<button
					class="text-xs font-medium px-3.5 py-1.5 rounded-full border transition-all
						{activeSource === f.key 
							? 'bg-[var(--bg-elevated)] border-[var(--border-hover)] text-[var(--text-primary)]' 
							: 'bg-[var(--bg-surface)] border-[var(--border-default)] text-[var(--text-muted)] hover:border-[var(--border-hover)] hover:text-[var(--text-primary)]'}"
					onclick={() => { activeSource = f.key; loadSource(f.key); }}
				>
					{f.label}
				</button>
			{/each}
		</div>

		<!-- Feed events grouped by date -->
		{#if sourceLoading}
			<div class="text-center py-12">
				<p class="text-[var(--text-muted)]">Loading events...</p>
			</div>
		{:else if filteredEvents.length === 0}
			<EmptyState 
				title="No Events Found" 
				message="Try changing the filter or check back later"
			/>
		{:else}
			{#each groupedEvents() as group}
				<div class="space-y-3">
					<!-- Date header -->
					<div class="text-xs font-semibold text-[var(--text-secondary)] pl-1">
						{group.label}
					</div>
					
					{#each group.events as event}
						<a href="/ticker/{event.ticker}" class="block">
							<div class="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)]
								hover:border-[var(--border-hover)] transition-all
								{event.has_score === false && event.significance === 'low' ? 'opacity-60' : ''}"
								style={sigStyle(event.significance)}>
								
								<div class="flex items-center gap-4">
									<!-- Source badge -->
									<div class="flex-shrink-0">
										<span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide
											{sourceColors[event.source] || 'bg-[var(--bg-elevated)] text-[var(--text-muted)]'}">
											{sourceLabels[event.source] || event.source.toUpperCase()}
										</span>
									</div>
									
									<!-- Ticker + Company -->
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-2 flex-wrap">
											<span class="ticker-code text-base flex-shrink-0">{event.ticker}</span>
											{#if event.company}
												<span class="text-xs text-[var(--text-muted)]">{event.company}</span>
											{/if}
										</div>
									</div>
									
									<!-- Sentiment + Significance -->
									<div class="flex items-center gap-2 flex-shrink-0">
										{#if event.significance === 'high'}
											<span class="w-2 h-2 rounded-full bg-[var(--amber)]"></span>
										{:else if event.significance === 'medium'}
											<span class="w-2 h-2 rounded-full bg-[var(--blue)]"></span>
										{:else}
											<span class="w-2 h-2 rounded-full bg-[var(--text-dimmed)]"></span>
										{/if}
										{#if event.sentiment === 'bullish'}
											<Badge variant="bullish">↑</Badge>
										{:else if event.sentiment === 'bearish'}
											<Badge variant="bearish">↓</Badge>
										{/if}
									</div>
								</div>
								
								<!-- Headline + Description -->
								<div class="mt-2 pl-0">
									<p class="text-sm font-medium text-[var(--text-secondary)] leading-relaxed">
										{event.headline}
									</p>
									{#if event.description}
										<p class="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
											{event.description}
										</p>
									{/if}
								</div>
							</div>
						</a>
					{/each}
				</div>
			{/each}
		{/if}

	{/if}
</div>
