<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { formatCurrency, formatPercent, formatDate, getDirectionColor } from '$lib/utils/format';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	// Tab state
	let activeTab = $state('signals');
	
	// Filter states for each tab
	let signalsMinScore = $state(0);
	let signalsDirection = $state('');
	let congressParty = $state('');
	let congressChamber = $state('');
	let congressTradeType = $state('');
	let arkFund = $state('');
	let darkpoolMinZscore = $state('');
	
	// Filter functions
	const filteredSignals = $derived(() => {
		return data.signals.data.filter(s => {
			if (signalsMinScore > 0 && s.score < signalsMinScore) return false;
			if (signalsDirection && s.direction !== signalsDirection) return false;
			return true;
		});
	});
	
	const filteredCongress = $derived(() => {
		return data.congress.data.filter(t => {
			if (congressParty && t.party !== congressParty) return false;
			if (congressChamber && t.chamber !== congressChamber) return false;
			if (congressTradeType && t.trade_type !== congressTradeType) return false;
			return true;
		});
	});
	
	const filteredArk = $derived(() => {
		return data.ark.data.filter(h => {
			if (arkFund && h.etf !== arkFund) return false;
			return true;
		});
	});
	
	const filteredDarkpool = $derived(() => {
		return data.darkpool.data.filter(d => {
			if (darkpoolMinZscore && d.z_score < parseFloat(darkpoolMinZscore)) return false;
			return true;
		});
	});
	
	// Column definitions
	const signalsColumns = [
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>` },
		{ key: 'company', label: 'Company', sortable: true },
		{ key: 'score', label: 'Score', sortable: true, class: 'text-right', render: (v: number) => `<span class="font-bold">${v}</span>` },
		{ key: 'direction', label: 'Direction', sortable: true, render: (v: string) => `<span class="px-2 py-1 rounded-full text-xs font-medium ${getDirectionColor(v)}">${v}</span>` },
		{ key: 'source_count', label: 'Sources', sortable: true, class: 'text-right' },
		{ key: 'congress_score', label: 'Congress', sortable: true, class: 'text-right' },
		{ key: 'ark_score', label: 'ARK', sortable: true, class: 'text-right' },
		{ key: 'darkpool_score', label: 'Dark Pool', sortable: true, class: 'text-right' },
		{ key: 'institution_score', label: 'Institution', sortable: true, class: 'text-right' },
		{ key: 'signal_date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) }
	];
	
	const congressColumns = [
		{ key: 'representative', label: 'Representative', sortable: true },
		{ key: 'party', label: 'Party', sortable: true, render: (v: string) => `<span class="px-2 py-1 rounded-full text-xs font-medium ${v === 'Republican' ? 'bg-red/20 text-red' : 'bg-blue/20 text-blue'}">${v[0]}</span>` },
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>` },
		{ key: 'trade_type', label: 'Type', sortable: true, render: (v: string) => `<span class="px-2 py-1 rounded-full text-xs font-medium ${v.includes('Purchase') ? 'bg-green/20 text-green' : 'bg-red/20 text-red'}">${v}</span>` },
		{ key: 'amount_range', label: 'Amount', sortable: true },
		{ key: 'transaction_date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'excess_return_pct', label: 'Excess Return', sortable: true, class: 'text-right', render: (v: number | null) => {
			if (v === null) return 'N/A';
			const color = v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-muted';
			return `<span class="${color}">${formatPercent(v, 2, true)}</span>`;
		}}
	];
	
	const arkColumns = [
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>` },
		{ key: 'etf', label: 'ETF', sortable: true },
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
		{ key: 'weight_pct', label: 'Weight', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'market_value', label: 'Market Value', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) },
		{ key: 'price', label: 'Price', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) }
	];
	
	const darkpoolColumns = [
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>` },
		{ key: 'date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'dpi', label: 'DPI', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v * 100) },
		{ key: 'short_pct', label: 'Short %', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'z_score', label: 'Z-Score', sortable: true, class: 'text-right', render: (v: number) => {
			const isAnomaly = v > 2;
			return `<span class="${isAnomaly ? 'text-[var(--amber)] font-bold' : ''}">${v.toFixed(2)}</span>`;
		}},
		{ key: 'volume', label: 'Volume', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() }
	];
	
	const tabs = [
		{ id: 'signals', label: 'Signals', count: filteredSignals().length },
		{ id: 'congress', label: 'Congress', count: filteredCongress().length },
		{ id: 'ark', label: 'ARK', count: filteredArk().length },
		{ id: 'darkpool', label: 'Dark Pool', count: filteredDarkpool().length },
		{ id: 'institutions', label: 'Institutions', count: data.institutions.data.length }
	];
</script>

<svelte:head>
	<title>Smart Money — Meridian Intelligence Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">Meridian</h1>
		<p class="text-[var(--text-secondary)]">Smart Money Intelligence Platform</p>
		<p class="text-caption text-[var(--text-dimmed)] mt-2">
			Last updated: {formatDate(data.signals.metadata.last_updated)}
		</p>
	</div>
	
	<!-- Tabs -->
	<div>
		<!-- Tab buttons -->
		<div class="flex border-b border-[var(--border-default)] overflow-x-auto scrollbar-thin">
			{#each tabs as tab}
				<button
					class="px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors relative
						{activeTab === tab.id ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
					onclick={() => activeTab = tab.id}
				>
					{tab.label}
					<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
						{tab.count}
					</span>
					{#if activeTab === tab.id}
						<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
					{/if}
				</button>
			{/each}
		</div>
		
		<!-- Tab content -->
		<div class="mt-4">
			{#if activeTab === 'signals'}
				<div class="space-y-4 fade-in">
					<Card>
						{#snippet children()}
							<div class="flex flex-wrap gap-4">
								<div>
									<label class="text-label mb-1 block">Min Score</label>
									<input type="number" bind:value={signalsMinScore} min="0" step="1"
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)] w-24" />
								</div>
								<div>
									<label class="text-label mb-1 block">Direction</label>
									<select bind:value={signalsDirection}
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
										<option value="">All</option>
										<option value="bullish">Bullish</option>
										<option value="bearish">Bearish</option>
										<option value="mixed">Mixed</option>
									</select>
								</div>
								<div class="flex items-end">
									<span class="text-sm text-[var(--text-muted)]">Showing {filteredSignals().length} of {data.signals.metadata.total} signals</span>
								</div>
							</div>
						{/snippet}
					</Card>
					<Card>
						{#snippet children()}
							<DataTable columns={signalsColumns} data={filteredSignals()} />
						{/snippet}
					</Card>
				</div>
			{:else if activeTab === 'congress'}
				<div class="space-y-4 fade-in">
					<Card>
						{#snippet children()}
							<div class="flex flex-wrap gap-4">
								<div>
									<label class="text-label mb-1 block">Party</label>
									<select bind:value={congressParty}
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
										<option value="">All</option>
										<option value="Republican">Republican</option>
										<option value="Democrat">Democrat</option>
									</select>
								</div>
								<div>
									<label class="text-label mb-1 block">Chamber</label>
									<select bind:value={congressChamber}
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
										<option value="">All</option>
										<option value="Senate">Senate</option>
										<option value="House">House</option>
									</select>
								</div>
								<div>
									<label class="text-label mb-1 block">Trade Type</label>
									<select bind:value={congressTradeType}
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
										<option value="">All</option>
										<option value="Purchase">Purchase</option>
										<option value="Sale">Sale</option>
									</select>
								</div>
								<div class="flex items-end">
									<span class="text-sm text-[var(--text-muted)]">Showing {filteredCongress().length} of {data.congress.metadata.total} trades</span>
								</div>
							</div>
						{/snippet}
					</Card>
					<Card>
						{#snippet children()}
							<DataTable columns={congressColumns} data={filteredCongress()} />
						{/snippet}
					</Card>
				</div>
			{:else if activeTab === 'ark'}
				<div class="space-y-4 fade-in">
					<Card>
						{#snippet children()}
							<div class="flex flex-wrap gap-4">
								<div>
									<label class="text-label mb-1 block">Fund</label>
									<select bind:value={arkFund}
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
									<span class="text-sm text-[var(--text-muted)]">Showing {filteredArk().length} of {data.ark.metadata.total} holdings</span>
								</div>
							</div>
						{/snippet}
					</Card>
					<Card>
						{#snippet children()}
							<DataTable columns={arkColumns} data={filteredArk()} />
						{/snippet}
					</Card>
				</div>
			{:else if activeTab === 'darkpool'}
				<div class="space-y-4 fade-in">
					<Card>
						{#snippet children()}
							<div class="flex flex-wrap gap-4">
								<div>
									<label class="text-label mb-1 block">Min Z-Score</label>
									<input type="number" bind:value={darkpoolMinZscore} step="0.1"
										placeholder="e.g., 2.0"
										class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)] w-24" />
								</div>
								<div class="flex items-end">
									<span class="text-sm text-[var(--text-muted)]">Showing {filteredDarkpool().length} of {data.darkpool.metadata.total} records</span>
								</div>
							</div>
						{/snippet}
					</Card>
					<Card>
						{#snippet children()}
							<div class="mb-2 text-sm text-[var(--amber)]">
								Anomalies (Z-score &gt; 2) highlighted
							</div>
							<DataTable columns={darkpoolColumns} data={filteredDarkpool()} />
						{/snippet}
					</Card>
				</div>
			{:else if activeTab === 'institutions'}
				<div class="space-y-4 fade-in">
					<!-- Summary Cards -->
					<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
						<Card hover>
							{#snippet children()}
								<div class="text-center">
									<p class="text-label mb-2">Total Value</p>
									<p class="text-data-lg">{formatCurrency(data.institutions.summary.total_value)}</p>
								</div>
							{/snippet}
						</Card>
						<Card hover>
							{#snippet children()}
								<div class="text-center">
									<p class="text-label mb-2">Unique Tickers</p>
									<p class="text-data-lg">{data.institutions.summary.unique_tickers}</p>
								</div>
							{/snippet}
						</Card>
						<Card hover>
							{#snippet children()}
								<div class="text-center">
									<p class="text-label mb-2">Filings</p>
									<p class="text-data-lg">{data.institutions.summary.filings_count}</p>
								</div>
							{/snippet}
						</Card>
					</div>
					
					<!-- Filings -->
					<Card title="13F Filings">
						{#snippet children()}
							<div class="space-y-4">
								{#each data.institutions.data as filing}
									<div class="p-4 bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)]">
										<div class="flex items-start justify-between mb-2">
											<div>
												<h4 class="font-semibold text-[var(--text-primary)]">{filing.fund_name}</h4>
												<p class="text-caption text-[var(--text-dimmed)]">{filing.company_name}</p>
											</div>
											<Badge variant="info">{filing.quarter}</Badge>
										</div>
										<div class="grid grid-cols-2 gap-4 text-sm">
											<div>
												<span class="text-[var(--text-muted)]">Total Value:</span>
												<span class="text-data ml-2">{formatCurrency(filing.total_value)}</span>
											</div>
											<div>
												<span class="text-[var(--text-muted)]">Holdings:</span>
												<span class="text-data ml-2">{filing.holdings_count}</span>
											</div>
											<div class="col-span-2">
												<span class="text-[var(--text-muted)]">Filed:</span>
												<span class="text-[var(--text-primary)] ml-2">{formatDate(filing.filing_date)}</span>
											</div>
										</div>
									</div>
								{/each}
							</div>
						{/snippet}
					</Card>
					
					<!-- Top Holdings -->
					<Card title="Top Holdings">
						{#snippet children()}
							<DataTable 
								columns={[
									{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>` },
									{ key: 'issuer', label: 'Company', sortable: true },
									{ key: 'institution', label: 'Institution', sortable: true },
									{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
									{ key: 'value', label: 'Value', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) },
									{ key: 'pct_portfolio', label: '% Portfolio', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) }
								]} 
								data={data.institutions.top_holdings} 
							/>
						{/snippet}
					</Card>
				</div>
			{/if}
		</div>
	</div>
</div>
