<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import ResponsiveTable from '$lib/components/ui/ResponsiveTable.svelte';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	let activeTab = $state('us');
	
	const hasData = $derived(data.dividend.us?.length > 0 || data.dividend.hk?.length > 0 || data.dividend.cn?.length > 0);

	const currentData = $derived(
		activeTab === 'us' ? data.dividend.us :
		activeTab === 'hk' ? data.dividend.hk :
		data.dividend.cn
	);

	const avgYield = $derived(() => {
		if (!currentData?.length) return 0;
		return currentData.reduce((s: number, r: any) => s + (r.dividend_yield || 0), 0) / currentData.length;
	});

	const avgScore = $derived(() => {
		if (!currentData?.length) return 0;
		return currentData.reduce((s: number, r: any) => s + (r.total_score || 0), 0) / currentData.length;
	});

	const updatedAgo = $derived(() => {
		if (!data.dividend.updated_at) return '';
		const diff = Date.now() - new Date(data.dividend.updated_at).getTime();
		const hours = Math.floor(diff / 3600000);
		if (hours < 1) return 'just now';
		if (hours < 24) return `${hours}h ago`;
		return `${Math.floor(hours/24)}d ago`;
	});
	
	const fmtNum = (v: number | null | undefined, decimals = 1) => v != null ? v.toFixed(decimals) : 'N/A';
	const fmtPct = (v: number | null | undefined, decimals = 2) => v != null ? `${v.toFixed(decimals)}%` : 'N/A';
	const fmtMcap = (v: number | null | undefined) => {
		if (!v) return 'N/A';
		if (v >= 1e12) return `$${(v/1e12).toFixed(1)}T`;
		if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`;
		if (v >= 1e6) return `$${(v/1e6).toFixed(0)}M`;
		return `$${v.toLocaleString()}`;
	};
	const scoreColor = (v: number) => v >= 70 ? 'color-up' : v >= 50 ? 'color-amber' : 'color-down';

	const getColumns = (market: string) => {
		return [
			{ key: 'rank', label: '#', sortable: true, class: 'text-center w-10', render: (v: number) => `${v}` },
			{ key: 'ticker', label: 'Stock', sortable: true, render: (_v: string, row: any) => 
				`<a href="/ticker/${row.ticker}" class="hover:underline"><span class="ticker-code">${row.ticker}</span><br><span class="ticker-name">${row.name || ''}</span></a>` },
			{ key: 'total_score', label: 'Score', sortable: true, class: 'text-right', render: (v: number) => 
				`<span class="${scoreColor(v)} text-data font-bold">${fmtNum(v)}</span>` },
			{ key: 'dividend_yield', label: 'Yield', sortable: true, class: 'text-right', render: (v: number) => `<span class="text-data">${fmtPct(v)}</span>` },
			{ key: 'roe', label: 'ROE', sortable: true, class: 'text-right', render: (v: number) => `<span class="text-data">${fmtPct(v, 1)}</span>` },
			{ key: 'dca_5y_return', label: 'DCA 5Y', sortable: true, class: 'text-right', render: (v: number) => 
				`<span class="${v > 0 ? 'color-up' : 'color-down'} text-data">${v > 0 ? '+' : ''}${fmtPct(v)}</span>` },
			{ key: 'max_drawdown', label: 'MaxDD', sortable: true, class: 'text-right', render: (v: number) => 
				`<span class="color-down text-data">${fmtPct(v, 1)}</span>` },
			{ key: 'max_dd_days', label: 'DD Days', sortable: true, class: 'text-right', render: (v: number) => `<span class="text-data">${v}d</span>` },
			{ key: 'price', label: 'Price', sortable: true, class: 'text-right', render: (v: number) => `<span class="text-data">$${fmtNum(v, 2)}</span>` },
			{ key: 'sector', label: 'Sector', sortable: true, class: 'text-right text-sm' },
		];
	};
</script>

<svelte:head>
	<title>Dividend Screener — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<div class="flex items-center gap-3 mb-2">
			<h1 class="text-heading">Dividend Quality Screener</h1>
		</div>
		<p class="text-[var(--text-muted)]">
			Avg Yield <span class="text-data text-[var(--text-primary)]">{avgYield().toFixed(1)}%</span> · 
			Avg Score <span class="text-data text-[var(--text-primary)]">{avgScore().toFixed(0)}</span>
			{#if updatedAgo()}
				· Updated <span class="text-[var(--text-dimmed)]">{updatedAgo()}</span>
			{/if}
		</p>
		{#if hasData}
			<div class="text-xs text-[var(--text-muted)] mt-2 flex items-center gap-4">
				<div>
					<span class="inline-block w-2 h-2 rounded-full bg-[var(--green)] mr-1"></span>
					High Score (75+)
				</div>
				<div>
					<span class="inline-block w-2 h-2 rounded-full bg-[var(--amber)] mr-1"></span>
					Medium (50-75)
				</div>
				<div>
					<span class="inline-block w-2 h-2 rounded-full bg-[var(--red)] mr-1"></span>
					Low (&lt;50)
				</div>
			</div>
		{/if}
	</div>
	
	<!-- Tabs -->
	<div>
		<div class="flex border-b border-[var(--border-default)] gap-2">
			<button
				class="px-4 py-3 text-sm font-medium relative transition-colors
					{activeTab === 'us' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
				onclick={() => activeTab = 'us'}
			>
				US Market
				{#if hasData && data.dividend.us}
					<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
						{data.dividend.us.length}
					</span>
				{/if}
				{#if activeTab === 'us'}
					<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
				{/if}
			</button>
			<button
				class="px-4 py-3 text-sm font-medium relative transition-colors
					{activeTab === 'hk' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
				onclick={() => activeTab = 'hk'}
			>
				HK Market
				{#if hasData && data.dividend.hk}
					<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
						{data.dividend.hk.length}
					</span>
				{/if}
				{#if activeTab === 'hk'}
					<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
				{/if}
			</button>
			<button
				class="px-4 py-3 text-sm font-medium relative transition-colors
					{activeTab === 'cn' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
				onclick={() => activeTab = 'cn'}
			>
				CN Market
				{#if hasData && data.dividend.cn}
					<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
						{data.dividend.cn.length}
					</span>
				{/if}
				{#if activeTab === 'cn'}
					<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
				{/if}
			</button>
		</div>
		
		<!-- Tab Content -->
		<div class="mt-6">
			{#if !hasData}
				<EmptyState 
					title="No Dividend Data Available" 
					message={data.dividend.message || "Dividend screener data is not currently available"}
				/>
			{:else if activeTab === 'us'}
				<div class="fade-in">
					{#if data.dividend.us && data.dividend.us.length > 0}
						<Card>
							{#snippet children()}
								<ResponsiveTable columns={getColumns('us')} data={data.dividend.us} />
							{/snippet}
						</Card>
					{:else}
						<EmptyState message="No US dividend data available" />
					{/if}
				</div>
			{:else if activeTab === 'hk'}
				<div class="fade-in">
					{#if data.dividend.hk && data.dividend.hk.length > 0}
						<Card>
							{#snippet children()}
								<ResponsiveTable columns={getColumns('hk')} data={data.dividend.hk} />
							{/snippet}
						</Card>
					{:else}
						<EmptyState message="No HK dividend data available" />
					{/if}
				</div>
			{:else}
				<div class="fade-in">
					{#if data.dividend.cn && data.dividend.cn.length > 0}
						<Card>
							{#snippet children()}
								<ResponsiveTable columns={getColumns('cn')} data={data.dividend.cn} />
							{/snippet}
						</Card>
					{:else}
						<EmptyState message="No CN dividend data available" />
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.fade-in {
		animation: fadeIn 0.3s ease-in;
	}
	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
