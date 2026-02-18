<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { formatCurrency, formatPercent, formatDate } from '$lib/utils/format';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	// Tab state
	let activeTab = $state('trades');
	
	// Filter states
	let tradesFund = $state('');
	let tradesDirection = $state('');
	let holdingsFund = $state('');
	
	// Filter functions
	const filteredTrades = $derived(() => {
		return data.trades.data.filter(t => {
			if (tradesFund && t.etf !== tradesFund) return false;
			if (tradesDirection && t.trade_type !== tradesDirection) return false;
			return true;
		});
	});
	
	const filteredHoldings = $derived(() => {
		return data.holdings.data.filter(h => {
			if (holdingsFund && h.etf !== holdingsFund) return false;
			return true;
		});
	});
	
	// Group holdings by ETF
	const holdingsByEtf = $derived(() => {
		const grouped: Record<string, typeof data.holdings.data> = {};
		filteredHoldings().forEach(h => {
			if (!grouped[h.etf]) grouped[h.etf] = [];
			grouped[h.etf].push(h);
		});
		return grouped;
	});
	
	// Stats
	const etfStats = $derived(() => {
		const stats: Record<string, { count: number; totalValue: number; avgWeight: number }> = {};
		Object.entries(holdingsByEtf()).forEach(([etf, holdings]) => {
			stats[etf] = {
				count: holdings.length,
				totalValue: holdings.reduce((sum, h) => sum + h.market_value, 0),
				avgWeight: holdings.reduce((sum, h) => sum + h.weight_pct, 0) / holdings.length
			};
		});
		return stats;
	});
	
	const tradesColumns = [
		{ key: 'date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'etf', label: 'ETF', sortable: true, class: 'font-bold' },
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>` },
		{ key: 'company', label: 'Company', sortable: true },
		{ key: 'trade_type', label: 'Type', sortable: true, render: (v: string) => {
			const color = v === 'Buy' ? 'bg-green/20 text-green' : 'bg-red/20 text-red';
			return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${v}</span>`;
		}},
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
		{ key: 'change_pct', label: 'Change %', sortable: true, class: 'text-right', render: (v: number) => {
			const color = v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-[var(--text-muted)]';
			return `<span class="${color}">${formatPercent(v, 2, true)}</span>`;
		}},
		{ key: 'weight_pct', label: 'Weight', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'return_pct', label: 'Return', sortable: true, class: 'text-right', render: (v: number | null) => {
			if (v === null) return '<span class="text-[var(--text-dimmed)]">N/A</span>';
			const color = v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-[var(--text-muted)]';
			return `<span class="${color}">${formatPercent(v, 2, true)}</span>`;
		}}
	];
	
	const holdingsColumns = [
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>` },
		{ key: 'company', label: 'Company', sortable: true },
		{ key: 'etf', label: 'ETF', sortable: true, class: 'font-bold' },
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
		{ key: 'weight_pct', label: 'Weight', sortable: true, class: 'text-right', render: (v: number, row: any) => {
			// Color code by weight
			let color = 'bg-[var(--text-muted)]/20';
			if (v > 5) color = 'bg-green/40';
			else if (v > 2) color = 'bg-blue/30';
			else if (v > 1) color = 'bg-[var(--amber)]/20';
			return `<div class="flex items-center gap-2"><div class="h-2 ${color} rounded" style="width: ${Math.min(v * 10, 100)}%"></div><span>${formatPercent(v)}</span></div>`;
		}},
		{ key: 'market_value', label: 'Market Value', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) },
		{ key: 'price', label: 'Price', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) }
	];
</script>

<svelte:head>
	<title>ARK Invest — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">ARK Invest</h1>
		<p class="text-[var(--text-secondary)]">Track Cathie Wood's portfolio trades and current holdings</p>
	</div>
	
	<!-- Stats -->
	<div class="grid grid-cols-2 md:grid-cols-5 gap-4">
		{#each ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF'] as etf}
			{@const stats = etfStats()[etf]}
			{#if stats}
				<Card hover>
					{#snippet children()}
						<div class="text-center">
							<p class="text-label mb-1">{etf}</p>
							<p class="text-caption text-[var(--text-muted)] mb-1">{stats.count} holdings</p>
							<p class="text-data">{formatCurrency(stats.totalValue)}</p>
						</div>
					{/snippet}
				</Card>
			{/if}
		{/each}
	</div>
	
	<!-- Tabs -->
	<div>
		<!-- Tab buttons -->
		<div class="flex border-b border-[var(--border-default)] overflow-x-auto scrollbar-thin">
			<button
				class="px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors relative
					{activeTab === 'trades' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
				onclick={() => activeTab = 'trades'}
			>
				Recent Trades
				<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
					{filteredTrades().length}
				</span>
				{#if activeTab === 'trades'}
					<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
				{/if}
			</button>
			
			<button
				class="px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors relative
					{activeTab === 'holdings' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
				onclick={() => activeTab = 'holdings'}
			>
				Current Holdings
				<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
					{filteredHoldings().length}
				</span>
				{#if activeTab === 'holdings'}
					<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
				{/if}
			</button>
		</div>
		
		<!-- Tab content -->
		<div class="mt-4">
			{#if activeTab === 'trades'}
				<div class="space-y-4 fade-in">
					<!-- Filters -->
					<Card>
						{#snippet children()}
							<div class="flex flex-wrap gap-4">
								<div>
									<label class="text-label mb-1 block">Fund</label>
									<select bind:value={tradesFund}
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
										<option value="">All</option>
										<option value="ARKK">ARKK</option>
										<option value="ARKQ">ARKQ</option>
										<option value="ARKW">ARKW</option>
										<option value="ARKG">ARKG</option>
										<option value="ARKF">ARKF</option>
									</select>
								</div>
								<div>
									<label class="text-label mb-1 block">Direction</label>
									<select bind:value={tradesDirection}
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
										<option value="">All</option>
										<option value="Buy">Buy</option>
										<option value="Sell">Sell</option>
									</select>
								</div>
								<div class="flex items-end">
									<span class="text-sm text-[var(--text-muted)]">Showing {filteredTrades().length} of {data.trades.metadata.total} trades</span>
								</div>
							</div>
						{/snippet}
					</Card>
					
					<!-- Table -->
					<Card>
						{#snippet children()}
							<DataTable columns={tradesColumns} data={filteredTrades()} />
						{/snippet}
					</Card>
				</div>
			{:else if activeTab === 'holdings'}
				<div class="space-y-4 fade-in">
					<!-- Filters -->
					<Card>
						{#snippet children()}
							<div class="flex flex-wrap gap-4">
								<div>
									<label class="text-label mb-1 block">Fund</label>
									<select bind:value={holdingsFund}
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
										<option value="">All</option>
										<option value="ARKK">ARKK</option>
										<option value="ARKQ">ARKQ</option>
										<option value="ARKW">ARKW</option>
										<option value="ARKG">ARKG</option>
										<option value="ARKF">ARKF</option>
									</select>
								</div>
								<div class="flex items-end">
									<span class="text-sm text-[var(--text-muted)]">Showing {filteredHoldings().length} of {data.holdings.metadata.total} holdings</span>
								</div>
							</div>
						{/snippet}
					</Card>
					
					<!-- Table -->
					<Card>
						{#snippet children()}
							<DataTable columns={holdingsColumns} data={filteredHoldings()} />
						{/snippet}
					</Card>
				</div>
			{/if}
		</div>
	</div>
</div>
