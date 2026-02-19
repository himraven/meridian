<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { formatCurrency, formatPercent, formatDate } from '$lib/utils/format';
	import { page } from '$app/stores';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	// Score breakdown visualization (v2 engine: 0-100 scale)
	const maxScore = 100;
	
	function renderScoreBar(score: number): string {
		if (score === 0) return '0';
		const percentage = Math.min((score / maxScore) * 100, 100);
		return percentage.toFixed(0);
	}

	function formatScore(score: number): string {
		if (score === 0) return '0';
		return score % 1 === 0 ? score.toString() : score.toFixed(1);
	}
	
	const congressColumns = [
		{ key: 'representative', label: 'Representative', sortable: true },
		{ key: 'party', label: 'Party', sortable: true, render: (v: string) => {
			const color = v === 'Republican' ? 'bg-red/20 text-red' : 'bg-blue/20 text-blue';
			return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${v[0]}</span>`;
		}},
		{ key: 'trade_type', label: 'Type', sortable: true, render: (v: string) => {
			const color = ['Buy','Purchase'].some(k => v.includes(k)) ? 'bg-green/20 text-green' : 'bg-red/20 text-red';
			return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${v}</span>`;
		}},
		{ key: 'amount_range', label: 'Amount', sortable: true },
		{ key: 'transaction_date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'excess_return_pct', label: 'Excess Return', sortable: true, class: 'text-right', render: (v: number | null) => {
			if (v === null) return '<span class="text-[var(--text-muted)]">N/A</span>';
			const color = v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-[var(--text-muted)]';
			return `<span class="${color}">${formatPercent(v, 2, true)}</span>`;
		}}
	];
	
	const arkTradesColumns = [
		{ key: 'date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'etf', label: 'ETF', sortable: true, class: 'font-bold' },
		{ key: 'trade_type', label: 'Type', sortable: true, render: (v: string) => {
			const color = v === 'Buy' ? 'bg-green/20 text-green' : 'bg-red/20 text-red';
			return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${v}</span>`;
		}},
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
		{ key: 'change_pct', label: 'Change %', sortable: true, class: 'text-right', render: (v: number) => {
			const color = v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-[var(--text-muted)]';
			return `<span class="${color}">${formatPercent(v, 2, true)}</span>`;
		}}
	];
	
	const arkHoldingsColumns = [
		{ key: 'etf', label: 'ETF', sortable: true, class: 'font-bold' },
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
		{ key: 'weight_pct', label: 'Weight', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'market_value', label: 'Market Value', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) },
		{ key: 'price', label: 'Price', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) }
	];
	
	const darkpoolColumns = [
		{ key: 'date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'dpi', label: 'DPI', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v * 100) },
		{ key: 'short_pct', label: 'Short %', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'z_score', label: 'Z-Score', sortable: true, class: 'text-right', render: (v: number) => {
			const isAnomaly = v > 2;
			const color = isAnomaly ? 'text-yellow font-bold' : '';
			return `<span class="${color}">${v.toFixed(2)}</span>`;
		}},
		{ key: 'total_volume', label: 'Volume', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() }
	];
	
	const institutionColumns = [
		{ key: 'institution', label: 'Institution', sortable: true },
		{ key: 'quarter', label: 'Quarter', sortable: true },
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
		{ key: 'value', label: 'Value', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) },
		{ key: 'pct_portfolio', label: '% Portfolio', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'filing_date', label: 'Filed', sortable: true, render: (v: string) => formatDate(v) }
	];
	
	const insiderColumns = [
		{ key: 'trade_date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'insider_name', label: 'Insider', sortable: true },
		{ key: 'title', label: 'Title', sortable: true },
		{ key: 'transaction_type', label: 'Type', sortable: true, render: (v: string) => {
			const color = v === 'Buy' ? 'bg-green/20 text-green' : 'bg-red/20 text-red';
			return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${v}</span>`;
		}},
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v?.toLocaleString() ?? '—' },
		{ key: 'value', label: 'Value', sortable: true, class: 'text-right', render: (v: number) => v ? formatCurrency(v) : '—' },
		{ key: 'price', label: 'Price', sortable: true, class: 'text-right', render: (v: number) => v ? formatCurrency(v) : '—' }
	];
</script>

<svelte:head>
	<title>{data.data.ticker} — {data.data.company} — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Back Button -->
	<div>
		<a href="/signals" class="text-blue hover:text-blue/80 text-sm transition-colors">
			← Back to Signals
		</a>
	</div>
	
	<!-- Header -->
	<div class="bg-[var(--bg-surface)] rounded-lg border border-[var(--border-default)] p-6">
		<div class="flex items-start justify-between mb-4">
			<div>
				<h1 class="ticker-code text-3xl mb-2">{data.data.ticker}</h1>
				<p class="ticker-name text-xl">{data.data.company}</p>
			</div>
			{#if data.data.metadata.has_confluence}
				<Badge variant="success">
					Active Signal
				</Badge>
			{/if}
		</div>
		
		<!-- Overview Stats -->
		<div class="grid grid-cols-2 md:grid-cols-6 gap-4 pt-4 border-t border-[var(--border-default)]">
			<div class="text-center">
				<p class="text-label mb-1">Congress Trades</p>
				<p class="text-data-lg">{data.data.congress.count}</p>
			</div>
			<div class="text-center">
				<p class="text-label mb-1">ARK Trades</p>
				<p class="text-data-lg">{data.data.ark.trade_count}</p>
			</div>
			<div class="text-center">
				<p class="text-label mb-1">ARK ETFs</p>
				<p class="text-data-lg">{data.data.ark.holding_etfs}</p>
			</div>
			<div class="text-center">
				<p class="text-label mb-1">Dark Pool Events</p>
				<p class="text-data-lg">{data.data.darkpool.count}</p>
			</div>
			<div class="text-center">
				<p class="text-label mb-1">Insider Trades</p>
				<p class="text-data-lg">{data.data.insiders?.count ?? 0}</p>
			</div>
			<div class="text-center">
				<p class="text-label mb-1">Institutions</p>
				<p class="text-data-lg">{data.data.institutions.count}</p>
			</div>
		</div>
	</div>
	
	<!-- Confluence Score Breakdown -->
	{#if data.data.metadata.has_confluence}
		{@const conf = data.data.confluence}
		<Card title="Signal Confluence Breakdown">
			{#snippet children()}
				<div class="space-y-6">
					<!-- Overall Score -->
					<div class="text-center pb-4 border-b border-[var(--border-default)]">
						<p class="text-label mb-2">Total Confluence Score</p>
						<p class="text-5xl font-bold text-[var(--text-primary)] mb-2">{formatScore(conf.score ?? 0)}</p>
						{#if conf.direction}
							<Badge variant={conf.direction.toLowerCase() === 'bullish' ? 'bullish' : conf.direction.toLowerCase() === 'bearish' ? 'bearish' : 'warning'}>
								{conf.direction.toUpperCase()}
							</Badge>
						{/if}
						<p class="text-caption text-[var(--text-muted)] mt-2">
							From {conf.source_count ?? 0} source{(conf.source_count ?? 0) !== 1 ? 's' : ''}{conf.signal_date ? ` · ${formatDate(conf.signal_date)}` : ''}
						</p>
					</div>
					
					<!-- Score Breakdown Bars -->
					<div class="space-y-4">
						<!-- Congress -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<span class="text-label">Congress</span>
								<span class="text-data">{formatScore(conf.congress_score ?? 0)} / {maxScore}</span>
							</div>
							<div class="progress-bar">
								<div 
									class="h-full bg-yellow transition-all duration-500 rounded-full" 
									style="width: {renderScoreBar(conf.congress_score ?? 0)}%"
								></div>
							</div>
						</div>
						
						<!-- ARK -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<span class="text-label">ARK Invest</span>
								<span class="text-data">{formatScore(conf.ark_score ?? 0)} / {maxScore}</span>
							</div>
							<div class="progress-bar">
								<div 
									class="h-full bg-blue transition-all duration-500 rounded-full" 
									style="width: {renderScoreBar(conf.ark_score ?? 0)}%"
								></div>
							</div>
						</div>
						
						<!-- Dark Pool -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<span class="text-label">Dark Pool</span>
								<span class="text-data">{formatScore(conf.darkpool_score ?? 0)} / {maxScore}</span>
							</div>
							<div class="progress-bar">
								<div 
									class="h-full bg-purple-500 transition-all duration-500 rounded-full" 
									style="width: {renderScoreBar(conf.darkpool_score ?? 0)}%"
								></div>
							</div>
						</div>
						
						<!-- Insiders -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<span class="text-label">Insiders</span>
								<span class="text-data">{formatScore(conf.insider_score ?? 0)} / {maxScore}</span>
							</div>
							<div class="progress-bar">
								<div 
									class="h-full bg-orange-500 transition-all duration-500 rounded-full" 
									style="width: {renderScoreBar(conf.insider_score ?? 0)}%"
								></div>
							</div>
						</div>
						
						<!-- Institutions -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<span class="text-label">Institutions</span>
								<span class="text-data">{formatScore(conf.institution_score ?? 0)} / {maxScore}</span>
							</div>
							<div class="progress-bar">
								<div 
									class="h-full bg-green transition-all duration-500 rounded-full" 
									style="width: {renderScoreBar(conf.institution_score ?? 0)}%"
								></div>
							</div>
						</div>
					</div>
					
					<!-- Details (array of {source, description, date, conviction}) -->
					{#if conf.details && Array.isArray(conf.details) && conf.details.length > 0}
						<div class="pt-4 border-t border-[var(--border-default)]">
							<p class="text-label mb-3">Signal Details</p>
							<div class="space-y-2">
								{#each conf.details as detail}
									<div class="flex items-start gap-3 text-sm">
										<span class="px-2 py-0.5 rounded text-xs font-medium shrink-0 {
											detail.source === 'congress' ? 'bg-yellow/20 text-yellow' :
											detail.source === 'ark' ? 'bg-blue/20 text-blue' :
											detail.source === 'darkpool' ? 'bg-purple-500/20 text-purple-500' :
											detail.source === 'insider' ? 'bg-orange-500/20 text-orange-500' :
											detail.source === 'institution' ? 'bg-green/20 text-green' :
											'bg-[var(--bg-elevated)] text-[var(--text-muted)]'
										}">
											{detail.source}
										</span>
										<span class="text-[var(--text-secondary)]">{detail.description}</span>
										{#if detail.date}
											<span class="text-[var(--text-muted)] text-xs shrink-0 ml-auto">{formatDate(detail.date)}</span>
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{:else if conf.details && typeof conf.details === 'string'}
						<div class="pt-4 border-t border-[var(--border-default)]">
							<p class="text-sm text-[var(--text-muted)] whitespace-pre-line">{conf.details}</p>
						</div>
					{/if}
				</div>
			{/snippet}
		</Card>
	{/if}
	
	<!-- Congress Trades -->
	{#if data.data.congress.count > 0}
		<Card title="Congress Trades" badge={data.data.congress.count}>
			{#snippet children()}
				<DataTable columns={congressColumns} data={data.data.congress.trades} />
			{/snippet}
		</Card>
	{/if}
	
	<!-- ARK Activity -->
	{#if data.data.ark.trade_count > 0 || data.data.ark.holding_etfs > 0}
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<!-- ARK Trades -->
			{#if data.data.ark.trade_count > 0}
				<Card title="ARK Trades" badge={data.data.ark.trade_count}>
					{#snippet children()}
						<DataTable columns={arkTradesColumns} data={data.data.ark.trades} />
					{/snippet}
				</Card>
			{/if}
			
			<!-- ARK Holdings -->
			{#if data.data.ark.holding_etfs > 0}
				<Card title="ARK Holdings" badge={data.data.ark.holding_etfs}>
					{#snippet children()}
						<DataTable columns={arkHoldingsColumns} data={data.data.ark.holdings} />
					{/snippet}
				</Card>
			{/if}
		</div>
	{/if}
	
	<!-- Dark Pool Activity -->
	{#if data.data.darkpool.count > 0}
		<Card title="Dark Pool Activity" badge={data.data.darkpool.count}>
			{#snippet children()}
				<p class="text-sm text-[var(--text-muted)] mb-4">
					{data.data.darkpool.anomalies.filter(d => d.z_score > 2).length} anomalies detected (Z-score &gt; 2)
				</p>
				<DataTable columns={darkpoolColumns} data={data.data.darkpool.anomalies} />
			{/snippet}
		</Card>
	{/if}
	
	<!-- Institutional Holdings -->
	{#if data.data.institutions.count > 0}
		<Card title="Institutional Holdings" badge={data.data.institutions.count}>
			{#snippet children()}
				<DataTable columns={institutionColumns} data={data.data.institutions.holdings} />
			{/snippet}
		</Card>
	{/if}
	
	<!-- Insider Trades -->
	{#if data.data.insiders?.count > 0}
		<Card title="Insider Trades" badge={data.data.insiders.count}>
			{#snippet children()}
				{#if data.data.insiders.has_cluster}
					<p class="text-sm text-orange-500 mb-4">
						⚡ Cluster activity detected — multiple insiders trading near the same time
					</p>
				{/if}
				<DataTable columns={insiderColumns} data={data.data.insiders.trades} />
			{/snippet}
		</Card>
	{/if}
	
	<!-- External Links -->
	<Card title="External Research Links">
		{#snippet children()}
			<div class="flex flex-wrap gap-3">
				<a
					href="https://www.tradingview.com/chart/?symbol={data.data.ticker}"
					target="_blank"
					rel="noopener"
					class="flex items-center gap-2 px-4 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg
						hover:bg-[var(--bg-elevated)] transition-colors text-sm text-[var(--text-primary)]"
				>
					<span>TradingView</span>
					<svg class="w-3 h-3 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
					</svg>
				</a>
				<a
					href="https://finance.yahoo.com/quote/{data.data.ticker}"
					target="_blank"
					rel="noopener"
					class="flex items-center gap-2 px-4 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg
						hover:bg-[var(--bg-elevated)] transition-colors text-sm text-[var(--text-primary)]"
				>
					<span>Yahoo Finance</span>
					<svg class="w-3 h-3 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
					</svg>
				</a>
				<a
					href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={data.data.ticker}&type=10-K&dateb=&owner=include&count=40"
					target="_blank"
					rel="noopener"
					class="flex items-center gap-2 px-4 py-2 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg
						hover:bg-[var(--bg-elevated)] transition-colors text-sm text-[var(--text-primary)]"
				>
					<span>SEC EDGAR</span>
					<svg class="w-3 h-3 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
					</svg>
				</a>
			</div>
		{/snippet}
	</Card>

	<!-- Empty State -->
	{#if data.data.metadata.total_signals === 0}
		<Card>
			{#snippet children()}
				<div class="text-center py-12">
					<h3 class="text-subhead mb-2">No Smart Money Activity</h3>
					<p class="text-sm text-[var(--text-muted)]">
						This ticker has no recent activity from Congress, ARK, Dark Pools, Insiders, or Institutional filings.
					</p>
				</div>
			{/snippet}
		</Card>
	{/if}
</div>
