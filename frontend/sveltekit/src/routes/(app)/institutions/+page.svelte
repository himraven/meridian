<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { formatCurrency, formatPercent, formatDate } from '$lib/utils/format';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	const holdingsColumns = [
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => {
			return `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>`;
		}},
		{ key: 'issuer', label: 'Company', sortable: true },
		{ key: 'institution', label: 'Institution', sortable: true },
		{ key: 'quarter', label: 'Quarter', sortable: true },
		{ key: 'shares', label: 'Shares', sortable: true, class: 'text-right', render: (v: number) => v.toLocaleString() },
		{ key: 'value', label: 'Value', sortable: true, class: 'text-right', render: (v: number) => formatCurrency(v) },
		{ key: 'pct_portfolio', label: '% Portfolio', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'filing_date', label: 'Filed', sortable: true, render: (v: string) => formatDate(v) }
	];
</script>

<svelte:head>
	<title>Institutional Filings — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">Institutional Filings</h1>
		<p class="text-[var(--text-secondary)]">13F filings from major institutional investors</p>
		<p class="text-caption text-[var(--text-dimmed)] mt-2">
			Last updated: {formatDate(data.data.metadata.last_updated)}
		</p>
	</div>
	
	<!-- Summary Stats -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Value</p>
					<p class="text-data-lg">{formatCurrency(data.data.summary.total_value)}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Unique Tickers</p>
					<p class="text-data-lg">{data.data.summary.unique_tickers}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Filings</p>
					<p class="text-data-lg">{data.data.summary.filings_count}</p>
				</div>
			{/snippet}
		</Card>
	</div>
	
	<!-- Info Box -->
	<Card>
		{#snippet children()}
			<div>
				<h3 class="text-subhead mb-2">About 13F Filings</h3>
				<p class="text-sm text-[var(--text-muted)]">
					13F filings are quarterly reports filed by institutional investment managers with over $100M in assets under management. 
					These reports provide insights into what the smartest institutional investors are buying and selling.
				</p>
			</div>
		{/snippet}
	</Card>
	
	<!-- Filings Cards -->
	<div class="space-y-4">
		<h2 class="text-subhead">Recent Filings</h2>
		
		{#each data.data.data as filing}
			<Card hover>
				{#snippet children()}
					<div class="space-y-4">
						<!-- Filing Header -->
						<div class="flex items-start justify-between">
							<div class="flex-1">
								<h3 class="text-lg font-bold text-[var(--text-primary)] mb-1">{filing.fund_name}</h3>
								<p class="text-sm text-[var(--text-muted)] mb-2">{filing.company_name}</p>
								<div class="flex items-center gap-2">
									<Badge variant="info">{filing.quarter}</Badge>
									<Badge variant="neutral">CIK: {filing.cik}</Badge>
								</div>
							</div>
							<div class="text-right">
								<p class="text-label mb-1">Filed</p>
								<p class="text-[var(--text-primary)] font-semibold">{formatDate(filing.filing_date)}</p>
							</div>
						</div>
						
						<!-- Filing Stats -->
						<div class="grid grid-cols-2 gap-4 p-4 bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)]">
							<div>
								<p class="text-label mb-1">Total Portfolio Value</p>
								<p class="text-data-lg">{formatCurrency(filing.total_value)}</p>
							</div>
							<div>
								<p class="text-label mb-1">Number of Holdings</p>
								<p class="text-data-lg">{filing.holdings_count.toLocaleString()}</p>
							</div>
						</div>
					</div>
				{/snippet}
			</Card>
		{/each}
	</div>
	
	<!-- Top Holdings Table -->
	<Card title={`Top Holdings (${data.data.top_holdings.length})`}>
		{#snippet children()}
			<p class="text-sm text-[var(--text-muted)] mb-4">
				Combined top holdings across all filings
			</p>
			<DataTable columns={holdingsColumns} data={data.data.top_holdings} />
		{/snippet}
	</Card>
</div>
