<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import { formatDate } from '$lib/utils/format';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	let minScore = $state(data.filters.min_score);
	let source = $state(data.filters.source);
	let days = $state(data.filters.days);
	
	function applyFilters() {
		const params = new URLSearchParams();
		if (minScore > 0) params.set('min_score', minScore.toString());
		if (source) params.set('source', source);
		if (days !== 30) params.set('days', days.toString());
		goto(`/ranking?${params.toString()}`, { replaceState: true });
	}
	
	// Stats
	const multiSourceCount = $derived(() => data.data.data.filter(s => s.source_count >= 2).length);
	const avgScore = $derived(() => {
		const items = data.data.data;
		if (!items.length) return 0;
		return (items.reduce((sum, s) => sum + s.score, 0) / items.length).toFixed(0);
	});
	
	// Score color
	function scoreColor(score: number): string {
		if (score >= 80) return 'text-[var(--green)] font-black';
		if (score >= 60) return 'text-[var(--blue)] font-bold';
		if (score >= 40) return 'text-[var(--amber)] font-bold';
		if (score >= 20) return 'text-[var(--text-primary)] font-semibold';
		return 'text-[var(--text-muted)]';
	}
	
	function scoreBg(score: number): string {
		if (score >= 80) return 'bg-[var(--green)]/10 border-[var(--green)]/30';
		if (score >= 60) return 'bg-[var(--blue)]/10 border-[var(--blue)]/30';
		if (score >= 40) return 'bg-[var(--amber)]/10 border-[var(--amber)]/30';
		return 'bg-[var(--bg-surface)] border-[var(--border-default)]';
	}
	
	function convictionBar(value: number, max: number = 100): string {
		return `${Math.min(value / max * 100, 100)}%`;
	}
	
	const sourceColors: Record<string, string> = {
		congress: 'bg-[var(--amber)]/20 text-[var(--amber)]',
		ark: 'bg-[var(--blue)]/20 text-[var(--blue)]',
		darkpool: 'bg-purple-500/20 text-purple-400',
		institution: 'bg-[var(--green)]/20 text-[var(--green)]',
		insider: 'bg-orange-500/20 text-orange-400',
		short_interest: 'bg-red-500/20 text-red-400',
		superinvestor: 'bg-cyan-500/20 text-cyan-400'
	};

	let methodologyOpen = $state(false);
	
	const sourceLabels: Record<string, string> = {
		congress: 'GOV',
		ark: 'ARK',
		darkpool: 'DP',
		institution: '13F',
		insider: 'INS',
		short_interest: 'SI',
		superinvestor: 'SUP'
	};

	// Knowledge Hub slug mapping (source → article slug)
	const knowledgeSlugs: Record<string, string> = {
		congress: 'congress-trading-alpha',
		ark: 'ark-disruptive-innovation',
		darkpool: 'dark-pool-activity',
		institution: '13f-institutional-tracking',
		insider: 'insider-buying-signals',
		insiders: 'insider-buying-signals',
		short_interest: 'short-interest-analysis',
		superinvestors: 'superinvestor-tracking',
	};

	// Tooltip text for signal badge hover
	const signalTldr: Record<string, string> = {
		congress: 'Congress trades beat S&P by 6% over 30 days. STOCK Act disclosures = actionable window.',
		ark: 'ARK Invest conviction buys signal disruptive innovation thesis. High-conviction concentrated positions.',
		darkpool: 'Anomalous off-exchange volume reveals institutional accumulation. Z-score > 2.5 = actionable.',
		institution: '13F quarterly filings track hedge fund and institution positioning across the market.',
		insider: 'Clustered insider buying (3+ executives) generates 8.9% excess returns over 12 months.',
	};

	// Active tooltip state
	let tooltipSource = $state<string | null>(null);
	let tooltipX = $state(0);
	let tooltipY = $state(0);

	function showTooltip(e: MouseEvent, src: string) {
		tooltipSource = src;
		tooltipX = (e.currentTarget as HTMLElement).getBoundingClientRect().left;
		tooltipY = (e.currentTarget as HTMLElement).getBoundingClientRect().bottom + window.scrollY + 4;
	}

	function hideTooltip() {
		tooltipSource = null;
	}

	function handleBadgeClick(e: MouseEvent, src: string) {
		e.preventDefault();
		e.stopPropagation();
		const slug = knowledgeSlugs[src];
		if (slug) {
			goto(`/knowledge/${slug}`);
		}
	}
</script>

<svelte:head>
	<title>Meridian Ranking — Smart Money Conviction Scores</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">Meridian Ranking</h1>
		<p class="text-[var(--text-secondary)]">Multi-source conviction scoring — the more signals converge, the higher the rank</p>
		<p class="text-caption text-[var(--text-dimmed)] mt-2">
			Engine v2 · {formatDate(data.data.metadata.last_updated)}
		</p>
	</div>
	
	<!-- Stats -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Ranked</p>
					<p class="text-data-lg">{data.data.metadata.filtered}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Multi-Source</p>
					<p class="text-data-lg text-[var(--green)]">{multiSourceCount()}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Avg Conviction</p>
					<p class="text-data-lg">{avgScore()}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">High Conviction</p>
					<p class="text-data-lg text-[var(--blue)]">{data.data.data.filter(s => s.score >= 60).length}</p>
					<p class="text-caption text-[var(--text-dimmed)]">Score ≥ 60</p>
				</div>
			{/snippet}
		</Card>
	</div>
	
	<!-- Methodology (collapsible) -->
	<div class="rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] overflow-hidden">
		<button
			onclick={() => (methodologyOpen = !methodologyOpen)}
			class="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-[var(--bg-elevated)] transition-colors"
			aria-expanded={methodologyOpen}
		>
			<div class="flex items-center gap-2">
				<span class="text-base font-semibold text-[var(--text-primary)]">How Smart Money Score Works</span>
				<span class="text-xs text-[var(--text-muted)] bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded px-2 py-0.5">Methodology</span>
			</div>
			<svg
				class="w-4 h-4 text-[var(--text-muted)] transition-transform duration-200 {methodologyOpen ? 'rotate-180' : ''}"
				fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
			</svg>
		</button>

		{#if methodologyOpen}
			<div class="px-5 pb-5 border-t border-[var(--border-default)] space-y-5">
				<!-- Signal sources -->
				<div class="pt-4">
					<p class="text-sm text-[var(--text-secondary)] mb-3">
						We track <span class="text-[var(--text-primary)] font-semibold">7 independent signal sources</span> where institutional &amp; insider capital flows:
					</p>
					<div class="flex flex-wrap gap-2 text-sm text-[var(--text-muted)]">
						<span class="px-2 py-1 rounded bg-[var(--amber)]/10 border border-[var(--amber)]/20 text-[var(--amber)]">🏛️ Congress Trades</span>
						<span class="px-2 py-1 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400">👔 Insider Activity</span>
						<span class="px-2 py-1 rounded bg-[var(--blue)]/10 border border-[var(--blue)]/20 text-[var(--blue)]">🚀 ARK Invest</span>
						<span class="px-2 py-1 rounded bg-[var(--green)]/10 border border-[var(--green)]/20 text-[var(--green)]">🏦 Institutional 13F</span>
						<span class="px-2 py-1 rounded bg-purple-500/10 border border-purple-500/20 text-purple-400">🌑 Dark Pool</span>
						<span class="px-2 py-1 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-muted)]">🎯 Superinvestors</span>
						<span class="px-2 py-1 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-muted)]">📉 Short Interest</span>
					</div>
				</div>

				<!-- Scoring logic -->
				<div>
					<h4 class="text-sm font-semibold text-[var(--text-primary)] mb-2">Scoring Logic</h4>
					<ul class="space-y-1.5 text-sm text-[var(--text-muted)]">
						<li class="flex gap-2">
							<span class="text-[var(--text-dimmed)] mt-0.5 flex-shrink-0">•</span>
							<span>Each source generates a <span class="text-[var(--text-secondary)]">conviction score (0–100)</span> based on signal strength, recency, and quality</span>
						</li>
						<li class="flex gap-2">
							<span class="text-[var(--text-dimmed)] mt-0.5 flex-shrink-0">•</span>
							<span>The ranking algorithm measures <span class="text-[var(--text-secondary)]">signal confluence</span> — how many sources agree on direction</span>
						</li>
						<li class="flex gap-2">
							<span class="text-[var(--text-dimmed)] mt-0.5 flex-shrink-0">•</span>
							<span><span class="text-[var(--green)]">Aligned</span> directional signals boost each other; <span class="text-red-400">opposing</span> signals create penalties</span>
						</li>
						<li class="flex gap-2">
							<span class="text-[var(--text-dimmed)] mt-0.5 flex-shrink-0">•</span>
							<span>Neutral/unknown direction data is <span class="text-[var(--text-secondary)]">discounted</span> to prevent score inflation</span>
						</li>
					</ul>
				</div>

				<!-- Score tiers -->
				<div>
					<h4 class="text-sm font-semibold text-[var(--text-primary)] mb-2">Score Tiers</h4>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
						<div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-[var(--green)]/5 border border-[var(--green)]/20">
							<span class="text-lg">🔥</span>
							<div>
								<span class="font-semibold text-[var(--green)]">60+</span>
								<span class="text-[var(--text-secondary)] font-medium"> Strong</span>
								<p class="text-xs text-[var(--text-muted)] mt-0.5">Multiple aligned smart money sources. Worth immediate attention</p>
							</div>
						</div>
						<div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-[var(--blue)]/5 border border-[var(--blue)]/20">
							<span class="text-lg">✅</span>
							<div>
								<span class="font-semibold text-[var(--blue)]">40–60</span>
								<span class="text-[var(--text-secondary)] font-medium"> Watch</span>
								<p class="text-xs text-[var(--text-muted)] mt-0.5">Notable activity detected. Add to watchlist</p>
							</div>
						</div>
						<div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)]">
							<span class="text-lg">⚪</span>
							<div>
								<span class="font-semibold text-[var(--text-secondary)]">20–40</span>
								<span class="text-[var(--text-secondary)] font-medium"> Low</span>
								<p class="text-xs text-[var(--text-muted)] mt-0.5">Some activity, low confluence</p>
							</div>
						</div>
						<div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)]">
							<span class="text-lg">—</span>
							<div>
								<span class="font-semibold text-[var(--text-dimmed)]">Below 20</span>
								<p class="text-xs text-[var(--text-muted)] mt-0.5">Background noise</p>
							</div>
						</div>
					</div>
				</div>

				<!-- Disclaimer -->
				<div class="flex gap-3 px-4 py-3 rounded-lg bg-[var(--amber)]/5 border border-[var(--amber)]/20">
					<span class="text-[var(--amber)] flex-shrink-0 mt-0.5">⚠️</span>
					<p class="text-xs text-[var(--text-muted)] leading-relaxed">
						<span class="font-semibold text-[var(--text-secondary)]">Important:</span>
						Scores are attention filters, not buy/sell recommendations. A high score means smart money is active and aligned on this ticker — it's a starting point for your own research.
					</p>
				</div>
			</div>
		{/if}
	</div>

	<!-- Scoring Info -->
	<Card>
		{#snippet children()}
			<div>
				<h3 class="text-subhead mb-2">How Conviction Scoring Works</h3>
				<p class="text-sm text-[var(--text-muted)] mb-3">
					Each signal is scored 0-100 based on conviction strength. Scores are amplified by source confluence — the more independent signals converge on a ticker, the higher it ranks.
				</p>
				<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 text-sm">
					{#each [
						{ href: '/knowledge/congress-trading-alpha', label: 'GOV', color: sourceColors.congress, desc: 'Amount × Recency × Members' },
						{ href: '/knowledge/ark-disruptive-innovation', label: 'ARK', color: sourceColors.ark, desc: 'Funds × Shares × Position' },
						{ href: '/knowledge/dark-pool-activity', label: 'DP', color: sourceColors.darkpool, desc: 'Z-Score × DPI × Volume' },
						{ href: '/knowledge/13f-institutional-tracking', label: '13F', color: sourceColors.institution, desc: 'Value × Change × Prestige' },
						{ href: '/knowledge/insider-buying-signals', label: 'INS', color: sourceColors.insider, desc: 'Value × Clusters × Recency' },
						{ href: '/knowledge/short-interest-analysis', label: 'SI', color: sourceColors.short_interest, desc: 'SI Ratio × Days to Cover' },
						{ href: '/knowledge/superinvestor-tracking', label: 'SUP', color: sourceColors.superinvestor, desc: 'Managers × Position × Size' },
					] as item}
						<a href={item.href} class="flex items-start gap-2 group p-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors">
							<span class="px-2 py-0.5 rounded text-xs font-bold {item.color} shrink-0 min-w-[2.5rem] text-center">{item.label}</span>
							<span class="text-xs text-[var(--text-muted)] group-hover:text-[var(--text-secondary)] leading-tight">{item.desc}</span>
						</a>
					{/each}
				</div>
			</div>
		{/snippet}
	</Card>
	
	<!-- Filters -->
	<Card title="Filters">
		{#snippet children()}
			<div class="flex flex-wrap gap-4">
				<div>
					<label class="text-label mb-1 block" for="min-score">Min Score</label>
					<input 
						id="min-score"
						type="number" 
						bind:value={minScore} 
						onchange={applyFilters}
						min="0" max="100" step="10"
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)] w-24" 
					/>
				</div>
				<div>
					<label class="text-label mb-1 block" for="source-filter">Source</label>
					<select id="source-filter" bind:value={source} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value="">All</option>
						<option value="congress">Congress</option>
						<option value="ark">ARK</option>
						<option value="darkpool">Dark Pool</option>
						<option value="institution">Institutions</option>
						<option value="insider">Insiders</option>
					</select>
				</div>
				<div>
					<label class="text-label mb-1 block" for="days-filter">Period</label>
					<select id="days-filter" bind:value={days} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value={7}>7 days</option>
						<option value={14}>14 days</option>
						<option value={30}>30 days</option>
						<option value={60}>60 days</option>
					</select>
				</div>
				<div class="flex items-end">
					<button 
						onclick={() => { minScore = 0; source = ''; days = 30; applyFilters(); }}
						class="px-3 py-2 bg-[var(--bg-elevated)] hover:bg-[var(--border-default)] rounded text-sm text-[var(--text-primary)] transition-colors"
					>
						Reset
					</button>
				</div>
			</div>
		{/snippet}
	</Card>
	
	<!-- Signal Cards -->
	{#if data.data.data.length > 0}
		<div class="space-y-3">
			{#each data.data.data as signal, i}
				<a href="/ticker/{signal.ticker}" class="block">
					<div class="p-4 rounded-xl border {scoreBg(signal.score)} hover:border-[var(--border-hover)] transition-all">
						<div class="flex items-center gap-4">
							<!-- Rank -->
							<div class="flex-shrink-0 w-8 text-center text-sm text-[var(--text-dimmed)] font-mono">
								{i + 1}
							</div>
							
							<!-- Score -->
							<div class="flex-shrink-0 w-14 text-center">
								<div class="text-2xl {scoreColor(signal.score)}">{signal.score.toFixed(0)}</div>
							</div>
							
							<!-- Ticker + Company -->
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2 mb-1">
									<span class="ticker-code text-base">{signal.ticker}</span>
									<span class="text-xs text-[var(--text-muted)] truncate">{signal.company || ''}</span>
								</div>
								
								<!-- Source Tags (with inline scores on mobile) — clickable → Knowledge Hub -->
								<div class="flex items-center gap-1.5 flex-wrap">
									{#each signal.sources as src}
										{@const srcScore = src === 'congress' ? signal.congress_score : src === 'ark' ? signal.ark_score : src === 'darkpool' ? signal.darkpool_score : src === 'institution' ? signal.institution_score : src === 'insider' ? signal.insider_score : 0}
										{@const hasKnowledge = !!knowledgeSlugs[src]}
										<button
											class="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide
												{sourceColors[src] || 'bg-[var(--bg-elevated)] text-[var(--text-muted)]'}
												{hasKnowledge ? 'cursor-pointer hover:opacity-80 hover:scale-105 transition-all' : 'cursor-default'}"
											onmouseenter={(e) => hasKnowledge && showTooltip(e, src)}
											onmouseleave={hideTooltip}
											onclick={(e) => hasKnowledge && handleBadgeClick(e, src)}
											title={hasKnowledge ? `Learn about ${sourceLabels[src] || src} signals` : undefined}
										>
											{sourceLabels[src] || src.toUpperCase()}<span class="md:hidden font-normal ml-0.5">{srcScore > 0 ? srcScore.toFixed(0) : ''}</span>
										</button>
									{/each}
									{#if signal.source_count >= 2}
										<span class="text-[10px] text-[var(--green)] font-semibold ml-1">
											+{signal.multi_source_bonus.toFixed(0)} bonus
										</span>
									{/if}
								</div>
							</div>
							
							<!-- Conviction Bars -->
							<div class="hidden md:flex flex-shrink-0 gap-2 items-center">
								{#if signal.congress_score > 0}
									<div class="w-16 text-center">
										<div class="text-[10px] text-[var(--text-dimmed)] mb-0.5">GOV</div>
										<div class="h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
											<div class="h-full bg-[var(--amber)] rounded-full transition-all" style="width: {convictionBar(signal.congress_score)}"></div>
										</div>
										<div class="text-[10px] text-[var(--text-muted)] mt-0.5">{signal.congress_score.toFixed(0)}</div>
									</div>
								{/if}
								{#if signal.ark_score > 0}
									<div class="w-16 text-center">
										<div class="text-[10px] text-[var(--text-dimmed)] mb-0.5">ARK</div>
										<div class="h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
											<div class="h-full bg-[var(--blue)] rounded-full transition-all" style="width: {convictionBar(signal.ark_score)}"></div>
										</div>
										<div class="text-[10px] text-[var(--text-muted)] mt-0.5">{signal.ark_score.toFixed(0)}</div>
									</div>
								{/if}
								{#if signal.darkpool_score > 0}
									<div class="w-16 text-center">
										<div class="text-[10px] text-[var(--text-dimmed)] mb-0.5">DP</div>
										<div class="h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
											<div class="h-full bg-purple-400 rounded-full transition-all" style="width: {convictionBar(signal.darkpool_score)}"></div>
										</div>
										<div class="text-[10px] text-[var(--text-muted)] mt-0.5">{signal.darkpool_score.toFixed(0)}</div>
									</div>
								{/if}
								{#if signal.institution_score > 0}
									<div class="w-16 text-center">
										<div class="text-[10px] text-[var(--text-dimmed)] mb-0.5">13F</div>
										<div class="h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
											<div class="h-full bg-[var(--green)] rounded-full transition-all" style="width: {convictionBar(signal.institution_score)}"></div>
										</div>
										<div class="text-[10px] text-[var(--text-muted)] mt-0.5">{signal.institution_score.toFixed(0)}</div>
									</div>
								{/if}
								{#if signal.insider_score > 0}
									<div class="w-16 text-center">
										<div class="text-[10px] text-[var(--text-dimmed)] mb-0.5">INS</div>
										<div class="h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
											<div class="h-full bg-orange-400 rounded-full transition-all" style="width: {convictionBar(signal.insider_score)}"></div>
										</div>
										<div class="text-[10px] text-[var(--text-muted)] mt-0.5">{signal.insider_score.toFixed(0)}</div>
									</div>
								{/if}
							</div>
							
							<!-- Date -->
							<div class="flex-shrink-0 text-right">
								<div class="text-xs text-[var(--text-dimmed)]">{formatDate(signal.signal_date)}</div>
							</div>
						</div>
						
						<!-- Details (mobile: show conviction bars) -->
						<div class="md:hidden mt-3 flex gap-2">
							{#if signal.congress_score > 0}
								<div class="flex-1">
									<div class="flex items-center justify-between text-[10px] mb-0.5">
										<span class="text-[var(--amber)]">GOV</span>
										<span class="text-[var(--text-muted)]">{signal.congress_score.toFixed(0)}</span>
									</div>
									<div class="h-1 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
										<div class="h-full bg-[var(--amber)] rounded-full" style="width: {convictionBar(signal.congress_score)}"></div>
									</div>
								</div>
							{/if}
							{#if signal.ark_score > 0}
								<div class="flex-1">
									<div class="flex items-center justify-between text-[10px] mb-0.5">
										<span class="text-[var(--blue)]">ARK</span>
										<span class="text-[var(--text-muted)]">{signal.ark_score.toFixed(0)}</span>
									</div>
									<div class="h-1 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
										<div class="h-full bg-[var(--blue)] rounded-full" style="width: {convictionBar(signal.ark_score)}"></div>
									</div>
								</div>
							{/if}
							{#if signal.darkpool_score > 0}
								<div class="flex-1">
									<div class="flex items-center justify-between text-[10px] mb-0.5">
										<span class="text-purple-400">DP</span>
										<span class="text-[var(--text-muted)]">{signal.darkpool_score.toFixed(0)}</span>
									</div>
									<div class="h-1 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
										<div class="h-full bg-purple-400 rounded-full" style="width: {convictionBar(signal.darkpool_score)}"></div>
									</div>
								</div>
							{/if}
							{#if signal.institution_score > 0}
								<div class="flex-1">
									<div class="flex items-center justify-between text-[10px] mb-0.5">
										<span class="text-[var(--green)]">13F</span>
										<span class="text-[var(--text-muted)]">{signal.institution_score.toFixed(0)}</span>
									</div>
									<div class="h-1 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
										<div class="h-full bg-[var(--green)] rounded-full" style="width: {convictionBar(signal.institution_score)}"></div>
									</div>
								</div>
							{/if}
							{#if signal.insider_score > 0}
								<div class="flex-1">
									<div class="flex items-center justify-between text-[10px] mb-0.5">
										<span class="text-orange-400">INS</span>
										<span class="text-[var(--text-muted)]">{signal.insider_score.toFixed(0)}</span>
									</div>
									<div class="h-1 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
										<div class="h-full bg-orange-400 rounded-full" style="width: {convictionBar(signal.insider_score)}"></div>
									</div>
								</div>
							{/if}
						</div>
						
						<!-- Signal Details -->
						{#if signal.details?.length}
							<div class="mt-2 pt-2 border-t border-[var(--border-default)]/50">
								{#each signal.details as detail}
									<div class="text-xs text-[var(--text-muted)] flex items-center gap-2 mt-1">
										<span class="font-mono text-[10px] {sourceColors[detail.source] || ''} px-1 rounded">{sourceLabels[detail.source] || detail.source}</span>
										<span class="truncate">{detail.description}</span>
										<span class="text-[var(--text-dimmed)] flex-shrink-0">{formatDate(detail.date)}</span>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</a>
			{/each}
		</div>
	{:else}
		<EmptyState 
			title="No Rankings Found" 
			message="Adjust filters or check back later"
		/>
	{/if}

	<!-- Knowledge Hub link -->
	<div class="pt-4 border-t border-[var(--border-default)] flex items-center justify-between">
		<p class="text-xs text-[var(--text-dimmed)]">
			Tip: click any signal badge (GOV, ARK, DP…) to learn how that signal works.
		</p>
		<a href="/knowledge" class="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-1">
			📚 Knowledge Hub
			<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
			</svg>
		</a>
	</div>
</div>

<!-- Signal badge tooltip (fixed position) -->
{#if tooltipSource && signalTldr[tooltipSource]}
	<div
		class="fixed z-50 max-w-xs pointer-events-none"
		style="top: {tooltipY}px; left: {Math.min(tooltipX, window.innerWidth - 280)}px;"
	>
		<div class="bg-[var(--bg-elevated)] border border-[var(--border-hover)] rounded-lg p-3 shadow-xl">
			<p class="text-[11px] font-semibold text-[var(--text-primary)] mb-1">
				{sourceLabels[tooltipSource] ?? tooltipSource.toUpperCase()} Signal
			</p>
			<p class="text-xs text-[var(--text-secondary)] leading-relaxed mb-2">
				{signalTldr[tooltipSource]}
			</p>
			<p class="text-[10px] text-[var(--blue)]">Click to learn more →</p>
		</div>
	</div>
{/if}
