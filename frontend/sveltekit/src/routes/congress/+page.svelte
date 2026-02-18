<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import ResponsiveTable from '$lib/components/ui/ResponsiveTable.svelte';
	import { formatPercent, formatDate } from '$lib/utils/format';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	let days = $state(data.filters.days);
	let party = $state(data.filters.party);
	let chamber = $state(data.filters.chamber);
	let tradeType = $state(data.filters.trade_type);
	
	function applyFilters() {
		const params = new URLSearchParams();
		if (days) params.set('days', days.toString());
		if (party) params.set('party', party);
		if (chamber) params.set('chamber', chamber);
		if (tradeType) params.set('trade_type', tradeType);
		goto(`/congress?${params.toString()}`, { replaceState: true });
	}
	
	const columns = [
		{ key: 'representative', label: 'Representative', sortable: true },
		{ key: 'party', label: 'Party', sortable: true, render: (v: string) => {
			const color = v === 'Republican' ? 'bg-red/20 text-red' : 'bg-blue/20 text-blue';
			return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${v[0]}</span>`;
		}},
		{ key: 'chamber', label: 'Chamber', sortable: true, render: (v: string) => {
			return `<span class="text-sm">${v}</span>`;
		}},
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => {
			return `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>`;
		}},
		{ key: 'company', label: 'Company', sortable: true },
		{ key: 'trade_type', label: 'Type', sortable: true, render: (v: string) => {
			const isPurchase = v.includes('Purchase');
			const color = isPurchase ? 'bg-green/20 text-green' : 'bg-red/20 text-red';
			return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${v}</span>`;
		}},
		{ key: 'amount_range', label: 'Amount', sortable: true },
		{ key: 'transaction_date', label: 'Transaction Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'filing_date', label: 'Filed', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'excess_return_pct', label: 'Excess Return', sortable: true, class: 'text-right', render: (v: number | null) => {
			if (v === null) return '<span class="text-[var(--text-dimmed)]">N/A</span>';
			const color = v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-[var(--text-muted)]';
			const sign = v > 0 ? '+' : '';
			return `<span class="${color} font-semibold">${sign}${formatPercent(v, 2)}</span>`;
		}}
	];
</script>

<svelte:head>
	<title>Congress Trades — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">Congress Trading</h1>
		<p class="text-[var(--text-secondary)]">Track congressional stock trades with real-time performance metrics</p>
		<p class="text-caption text-[var(--text-dimmed)] mt-2">
			Last updated: {formatDate(data.data.metadata.last_updated)}
		</p>
	</div>
	
	<!-- Stats -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Trades</p>
					<p class="text-data-lg">{data.data.metadata.total}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Filtered</p>
					<p class="text-data-lg">{data.data.metadata.filtered}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Purchases</p>
					<p class="text-data-lg text-[var(--green)]">
						{data.data.data.filter(t => t.trade_type.includes('Purchase')).length}
					</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Sales</p>
					<p class="text-data-lg text-[var(--red)]">
						{data.data.data.filter(t => t.trade_type.includes('Sale')).length}
					</p>
				</div>
			{/snippet}
		</Card>
	</div>
	
	<!-- Filters -->
	<Card title="Filters">
		{#snippet children()}
			<div class="flex flex-wrap gap-4">
				<div>
					<label class="text-label mb-1 block">Time Period</label>
					<select bind:value={days} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value={7}>Last 7 days</option>
						<option value={30}>Last 30 days</option>
						<option value={90}>Last 90 days</option>
						<option value={180}>Last 6 months</option>
						<option value={365}>Last year</option>
					</select>
				</div>
				<div>
					<label class="text-label mb-1 block">Party</label>
					<select bind:value={party} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value="">All</option>
						<option value="Republican">Republican</option>
						<option value="Democrat">Democrat</option>
					</select>
				</div>
				<div>
					<label class="text-label mb-1 block">Chamber</label>
					<select bind:value={chamber} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value="">All</option>
						<option value="Senate">Senate</option>
						<option value="House">House</option>
					</select>
				</div>
				<div>
					<label class="text-label mb-1 block">Trade Type</label>
					<select bind:value={tradeType} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value="">All</option>
						<option value="Purchase">Purchase</option>
						<option value="Sale">Sale</option>
						<option value="Sale (Partial)">Sale (Partial)</option>
					</select>
				</div>
			</div>
		{/snippet}
	</Card>
	
	<!-- Table -->
	<Card title="Trading Activity">
		{#snippet children()}
			<ResponsiveTable columns={columns} data={data.data.data} />
		{/snippet}
	</Card>
</div>
