<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { formatPercent, formatDate } from '$lib/utils/format';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	let days = $state(data.filters.days);
	let minZscore = $state(data.filters.min_zscore);
	
	function applyFilters() {
		const params = new URLSearchParams();
		if (days) params.set('days', days.toString());
		if (minZscore) params.set('min_zscore', minZscore.toString());
		goto(`/darkpool?${params.toString()}`, { replaceState: true });
	}
	
	// Count anomalies (z_score > 2)
	const anomalyCount = $derived(() => {
		return data.data.data.filter(d => d.z_score > 2).length;
	});
	
	const columns = [
		{ key: 'ticker', label: 'Ticker', sortable: true, class: 'font-mono font-bold', render: (v: string) => {
			return `<a href="/ticker/${v}" class="text-blue hover:underline">${v}</a>`;
		}},
		{ key: 'company', label: 'Company', sortable: true },
		{ key: 'date', label: 'Date', sortable: true, render: (v: string) => formatDate(v) },
		{ key: 'dpi', label: 'DPI', sortable: true, class: 'text-right', render: (v: number) => {
			// DPI is a ratio (0-1), display as percentage
			return formatPercent(v * 100);
		}},
		{ key: 'off_exchange_pct', label: 'Off-Exchange %', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'short_pct', label: 'Short %', sortable: true, class: 'text-right', render: (v: number) => formatPercent(v) },
		{ key: 'z_score', label: 'Z-Score', sortable: true, class: 'text-right', render: (v: number) => {
			const isAnomaly = v > 2;
			const color = isAnomaly ? 'text-[var(--amber)] font-bold' : '';
			return `<span class="${color}">${v.toFixed(2)}</span>`;
		}},
		{ key: 'total_volume', label: 'Volume', sortable: true, class: 'text-right', render: (v: number) => {
			if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
			if (v >= 1_000) return `${(v / 1_000).toFixed(2)}K`;
			return v.toLocaleString();
		}},
		{ key: 'source', label: 'Source', sortable: true }
	];
</script>

<svelte:head>
	<title>Dark Pool Analytics — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-heading mb-1">Dark Pool Analytics</h1>
		<p class="text-[var(--text-secondary)]">Track unusual dark pool activity and off-exchange trading patterns</p>
		<p class="text-caption text-[var(--text-dimmed)] mt-2">
			Last updated: {formatDate(data.data.metadata.last_updated)}
		</p>
	</div>
	
	<!-- Stats -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Records</p>
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
					<p class="text-label mb-2">Anomalies</p>
					<p class="text-data-lg text-[var(--amber)]">{anomalyCount()}</p>
					<p class="text-caption text-[var(--text-dimmed)] mt-1">Z-score &gt; 2</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Unique Tickers</p>
					<p class="text-data-lg">
						{new Set(data.data.data.map(d => d.ticker)).size}
					</p>
				</div>
			{/snippet}
		</Card>
	</div>
	
	<!-- Info Box -->
	<Card>
		{#snippet children()}
			<div>
				<h3 class="text-subhead mb-2">About Dark Pool Analytics</h3>
				<p class="text-sm text-[var(--text-muted)] mb-2">
					Dark Pool Index (DPI) measures the ratio of off-exchange volume to total volume. 
					A high DPI combined with a high Z-score indicates unusual institutional activity.
				</p>
				<p class="text-sm text-[var(--text-muted)]">
					<strong class="text-[var(--amber)]">Anomalies (Z-score &gt; 2)</strong> represent statistically significant deviations 
					from normal trading patterns and may signal institutional positioning.
				</p>
			</div>
		{/snippet}
	</Card>
	
	<!-- Filters -->
	<Card title="Filters">
		{#snippet children()}
			<div class="flex flex-wrap gap-4">
				<div>
					<label class="text-label mb-1 block">Time Period</label>
					<select bind:value={days} onchange={applyFilters}
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)]">
						<option value={7}>Last 7 days</option>
						<option value={14}>Last 14 days</option>
						<option value={30}>Last 30 days</option>
					</select>
				</div>
				<div>
					<label class="text-label mb-1 block">Min Z-Score (optional)</label>
					<input 
						type="number" 
						bind:value={minZscore} 
						onchange={applyFilters}
						step="0.1"
						placeholder="e.g., 2.0"
						class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-3 py-2 text-sm text-[var(--text-primary)] w-32" 
					/>
				</div>
				<div class="flex items-end">
					<button 
						onclick={() => { minZscore = ''; applyFilters(); }}
						class="px-3 py-2 bg-[var(--bg-elevated)] hover:bg-[var(--border-default)] rounded text-sm text-[var(--text-primary)] transition-colors"
					>
						Clear Filters
					</button>
				</div>
			</div>
		{/snippet}
	</Card>
	
	<!-- Table -->
	<Card title="Dark Pool Activity">
		{#snippet children()}
			<div class="mb-3 text-sm text-[var(--text-muted)]">
				{#if anomalyCount() > 0}
					<span class="text-[var(--amber)]">{anomalyCount()} anomalies detected (highlighted)</span>
				{:else}
					No anomalies detected in current filter range
				{/if}
			</div>
			<DataTable columns={columns} data={data.data.data} />
		{/snippet}
	</Card>
</div>
