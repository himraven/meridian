<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import { formatDate, formatCurrency, formatNumberWithCommas } from '$lib/utils/format';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let days = $state(data.filters.days);
	let transactionType = $state(data.filters.transaction_type);
	let clusterOnly = $state(data.filters.cluster_only);
	let minValue = $state(data.filters.min_value);

	function applyFilters() {
		const params = new URLSearchParams();
		if (days) params.set('days', days.toString());
		if (transactionType) params.set('transaction_type', transactionType);
		if (clusterOnly) params.set('cluster_only', 'true');
		if (minValue > 0) params.set('min_value', minValue.toString());
		goto(`/insiders?${params.toString()}`, { replaceState: true });
	}

	// Computed stats
	const totalTrades = $derived(data.data.metadata.filtered ?? data.data.data.length);
	const buyCount = $derived(
		data.data.metadata.buy_count ?? data.data.data.filter(t => t.transaction_type === 'Buy').length
	);
	const sellCount = $derived(
		data.data.metadata.sell_count ?? data.data.data.filter(t => t.transaction_type === 'Sale').length
	);
	const clusterCount = $derived(
		data.data.metadata.cluster_count ?? data.data.data.filter(t => t.is_cluster).length
	);
	const totalValue = $derived(
		data.data.metadata.total_value ?? data.data.data.reduce((sum, t) => sum + (t.value || 0), 0)
	);
</script>

<svelte:head>
	<title>Insider Trading — Meridian</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">Insider Trading</h1>
		<p class="text-[var(--text-secondary)]">Track corporate insider buys and sells with cluster detection</p>
		<p class="text-caption text-[var(--text-dimmed)] mt-2">
			Last updated: {formatDate(data.data.metadata.last_updated)}
		</p>
	</div>

	<!-- Stats -->
	<div class="grid grid-cols-2 md:grid-cols-5 gap-4">
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Trades</p>
					<p class="text-data-lg">{totalTrades}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Buys</p>
					<p class="text-data-lg text-[var(--green)]">{buyCount}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Sales</p>
					<p class="text-data-lg text-[var(--red)]">{sellCount}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Clusters</p>
					<p class="text-data-lg text-orange-400">{clusterCount}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Value</p>
					<p class="text-data-lg">{formatCurrency(totalValue)}</p>
				</div>
			{/snippet}
		</Card>
	</div>

	<!-- Filters -->
	<Card title="Filters">
		{#snippet children()}
			<div class="flex flex-wrap gap-4 items-end">
				<div>
					<label class="text-label mb-1 block" for="tx-type">Transaction Type</label>
					<select id="tx-type" bind:value={transactionType} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value="">All</option>
						<option value="Buy">Buy</option>
						<option value="Sale">Sale</option>
					</select>
				</div>
				<div>
					<label class="text-label mb-1 block" for="days-filter">Period</label>
					<select id="days-filter" bind:value={days} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value={7}>7 days</option>
						<option value={14}>14 days</option>
						<option value={30}>30 days</option>
						<option value={90}>90 days</option>
					</select>
				</div>
				<div>
					<label class="text-label mb-1 block" for="min-val">Min Value</label>
					<select id="min-val" bind:value={minValue} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value={0}>Any</option>
						<option value={100000}>$100K+</option>
						<option value={500000}>$500K+</option>
						<option value={1000000}>$1M+</option>
						<option value={5000000}>$5M+</option>
					</select>
				</div>
				<div class="flex items-center gap-2">
					<label class="text-label" for="cluster-toggle">Clusters Only</label>
					<button
						id="cluster-toggle"
						onclick={() => { clusterOnly = !clusterOnly; applyFilters(); }}
						class="relative w-10 h-5 rounded-full transition-colors {clusterOnly ? 'bg-orange-500' : 'bg-[var(--bg-elevated)]'}"
						role="switch"
						aria-checked={clusterOnly}
					>
						<span class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow {clusterOnly ? 'translate-x-5' : 'translate-x-0'}"></span>
					</button>
				</div>
				<div>
					<button 
						onclick={() => { days = 30; transactionType = ''; clusterOnly = false; minValue = 0; applyFilters(); }}
						class="px-3 py-2 bg-[var(--bg-elevated)] hover:bg-[var(--border-default)] rounded text-sm text-[var(--text-primary)] transition-colors"
					>
						Reset
					</button>
				</div>
			</div>
		{/snippet}
	</Card>

	<!-- Table -->
	{#if data.data.data.length > 0}
		<Card title="Insider Activity">
			{#snippet children()}
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-[var(--border-default)]">
								<th class="text-left py-3 px-3 text-label">Date</th>
								<th class="text-left py-3 px-3 text-label">Ticker</th>
								<th class="text-left py-3 px-3 text-label hidden md:table-cell">Company</th>
								<th class="text-left py-3 px-3 text-label">Insider</th>
								<th class="text-left py-3 px-3 text-label hidden lg:table-cell">Title</th>
								<th class="text-center py-3 px-3 text-label">Type</th>
								<th class="text-right py-3 px-3 text-label">Shares</th>
								<th class="text-right py-3 px-3 text-label">Value</th>
								<th class="text-center py-3 px-3 text-label">Cluster</th>
							</tr>
						</thead>
						<tbody>
							{#each data.data.data as trade}
								{@const isBuy = trade.transaction_type === 'Buy'}
								<tr class="border-b border-[var(--border-default)]/50 hover:bg-[var(--bg-elevated)]/50 transition-colors {trade.is_cluster ? 'bg-orange-500/5' : ''}">
									<td class="py-3 px-3 text-[var(--text-muted)] whitespace-nowrap">{formatDate(trade.date)}</td>
									<td class="py-3 px-3">
										<a href="/ticker/{trade.ticker}" class="ticker-code text-[var(--blue)] hover:underline">{trade.ticker}</a>
									</td>
									<td class="py-3 px-3 text-[var(--text-muted)] truncate max-w-[200px] hidden md:table-cell">{trade.company || '—'}</td>
									<td class="py-3 px-3 text-[var(--text-primary)] truncate max-w-[160px]">{trade.insider_name || '—'}</td>
									<td class="py-3 px-3 text-[var(--text-dimmed)] truncate max-w-[140px] hidden lg:table-cell">{trade.title || '—'}</td>
									<td class="py-3 px-3 text-center">
										<span class="px-2 py-1 rounded-full text-xs font-medium {isBuy ? 'bg-[var(--green)]/20 text-[var(--green)]' : 'bg-[var(--red)]/20 text-[var(--red)]'}">
											{trade.transaction_type}
										</span>
									</td>
									<td class="py-3 px-3 text-right font-mono text-[var(--text-primary)]">{formatNumberWithCommas(trade.shares)}</td>
									<td class="py-3 px-3 text-right font-mono {isBuy ? 'text-[var(--green)]' : 'text-[var(--text-muted)]'}">{formatCurrency(trade.value)}</td>
									<td class="py-3 px-3 text-center">
										{#if trade.is_cluster}
											<span class="px-2 py-1 rounded-full text-[10px] font-bold bg-orange-500/20 text-orange-400 tracking-wide">
												CLUSTER{#if trade.cluster_count} ×{trade.cluster_count}{/if}
											</span>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/snippet}
		</Card>
	{:else}
		<EmptyState 
			title="No Insider Trades Found" 
			message="Adjust filters or check back later"
		/>
	{/if}
</div>
