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
		insider: 'bg-orange-500/20 text-orange-400'
	};
	
	const sourceLabels: Record<string, string> = {
		congress: 'GOV',
		ark: 'ARK',
		darkpool: 'DP',
		institution: '13F',
		insider: 'INS'
	};
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
	
	<!-- Scoring Info -->
	<Card>
		{#snippet children()}
			<div>
				<h3 class="text-subhead mb-2">How Conviction Scoring Works</h3>
				<p class="text-sm text-[var(--text-muted)] mb-3">
					Each signal is scored 0-100 based on strength within its source. Multi-source alignment adds +20 bonus per source (max +40).
				</p>
				<div class="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
					<div class="flex items-center gap-2">
						<span class="px-2 py-0.5 rounded text-xs font-bold {sourceColors.congress}">GOV</span>
						<span class="text-[var(--text-muted)]">Amount × Recency × Members</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="px-2 py-0.5 rounded text-xs font-bold {sourceColors.ark}">ARK</span>
						<span class="text-[var(--text-muted)]">Funds × Shares × Position Type</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="px-2 py-0.5 rounded text-xs font-bold {sourceColors.darkpool}">DP</span>
						<span class="text-[var(--text-muted)]">Z-Score × DPI × Volume</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="px-2 py-0.5 rounded text-xs font-bold {sourceColors.institution}">13F</span>
						<span class="text-[var(--text-muted)]">Value × Change × Prestige</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="px-2 py-0.5 rounded text-xs font-bold {sourceColors.insider}">INS</span>
						<span class="text-[var(--text-muted)]">Value × Clusters × Recency</span>
					</div>
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
								
								<!-- Source Tags (with inline scores on mobile) -->
								<div class="flex items-center gap-1.5 flex-wrap">
									{#each signal.sources as src}
										{@const srcScore = src === 'congress' ? signal.congress_score : src === 'ark' ? signal.ark_score : src === 'darkpool' ? signal.darkpool_score : src === 'institution' ? signal.institution_score : src === 'insider' ? signal.insider_score : 0}
										<span class="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide {sourceColors[src] || 'bg-[var(--bg-elevated)] text-[var(--text-muted)]'}">
											{sourceLabels[src] || src.toUpperCase()}<span class="md:hidden font-normal ml-0.5">{srcScore > 0 ? srcScore.toFixed(0) : ''}</span>
										</span>
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
</div>
