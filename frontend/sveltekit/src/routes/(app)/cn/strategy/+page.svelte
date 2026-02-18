<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import LWAreaChart from '$lib/components/charts/LWAreaChart.svelte';
	import { formatPercent, formatDate, getChangeColor } from '$lib/utils/format';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	const holdingsColumns = [
		{ key: 'rank', label: '#', sortable: true, class: 'text-right' },
		{ key: 'ts_code', label: 'Code', sortable: true, class: 'font-mono' },
		{ key: 'name', label: 'Name', sortable: true },
		{ key: 'industry', label: 'Industry', sortable: true, class: 'text-[var(--text-muted)]' },
		{ key: 'close', label: 'Price', sortable: true, class: 'text-right', render: (v: number) => v ? `¥${v.toFixed(2)}` : '-' },
		{ key: 'score', label: 'Score', sortable: true, class: 'text-right text-[var(--amber)]', render: (v: number) => v ? v.toFixed(3) : '-' },
		{ key: 'weight', label: 'Weight', sortable: true, class: 'text-right', render: (v: number) => v ? formatPercent(v * 100, 1) : '-' },
	];
	
	// Holdings already have rank from 12x30 data
	const holdingsWithRank = $derived(
		data.portfolio.holdings.map((h: any, i: number) => ({ ...h, rank: h.rank || i + 1 }))
	);
	
	// NAV data for display (first 5 and last 5)
	const navPreview = $derived(() => {
		const dates = data.nav.dates;
		const stratNav = data.nav.strategy_nav;
		const benchNav = data.nav.benchmark_nav;
		
		if (dates.length <= 10) {
			return dates.map((date, i) => ({
				date,
				strategy_nav: stratNav[i],
				benchmark_nav: benchNav[i]
			}));
		}
		
		const first5 = dates.slice(0, 5).map((date, i) => ({
			date,
			strategy_nav: stratNav[i],
			benchmark_nav: benchNav[i]
		}));
		
		const last5 = dates.slice(-5).map((date, i) => ({
			date,
			strategy_nav: stratNav[dates.length - 5 + i],
			benchmark_nav: benchNav[dates.length - 5 + i]
		}));
		
		return [...first5, { date: '...', strategy_nav: null, benchmark_nav: null }, ...last5];
	});
</script>

<svelte:head>
	<title>CN 12×30 Strategy — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6" data-market-style="cn">
	<!-- Header -->
	<div class="flex items-center justify-between flex-wrap gap-4">
		<div>
			<div class="flex items-center gap-3 mb-2">
				<h1 class="text-heading">CN 12×30 Factor Strategy</h1>
				{#if data.sensitivity.confidence_score}
					<Badge variant="success">
						Confidence: {data.sensitivity.confidence_score.score}/{data.sensitivity.confidence_score.max}
					</Badge>
				{/if}
			</div>
			<p class="text-[var(--text-muted)]">12-Factor Contrarian Low-Liquidity · Monthly Rebalance · TOP 30 Holdings</p>
		</div>
		<div class="text-right text-sm text-[var(--text-muted)]">
			<div>Portfolio Date: <span class="text-[var(--text-primary)]">{formatDate(data.portfolio.date)}</span></div>
			<div class="mt-1">Rebalance: <span class="color-up">Every 10 days</span></div>
		</div>
	</div>
	
	<!-- Key Metrics -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Total Return</p>
					<p class="text-data-lg color-up">{formatPercent(data.metrics.total_return, 2, true)}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Max Drawdown</p>
					<p class="text-data-lg color-down">{formatPercent(data.metrics.max_drawdown, 2)}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Sharpe Ratio</p>
					<p class="text-data-lg" class:color-up={data.metrics.sharpe > 1} class:color-amber={data.metrics.sharpe <= 1}>
						{data.metrics.sharpe.toFixed(2)}
					</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Excess Return</p>
					<p class="text-data-lg color-up">{formatPercent(data.metrics.excess_return || 0, 2, true)}</p>
				</div>
			{/snippet}
		</Card>
	</div>
	
	{#if data.metrics.evolution}
		<div class="text-sm text-[var(--text-muted)]">
			Evolution: <span class="text-[var(--text-primary)] font-mono">{data.metrics.evolution}</span>
			{#if data.metrics.oos_sharpe_2025}
				· OOS Sharpe (2025): <span class="color-up font-mono">{data.metrics.oos_sharpe_2025.toFixed(2)}</span>
			{/if}
			· Factors: <span class="text-[var(--text-primary)]">{data.metrics.factors || 12}</span>
			· Backtest: <span class="text-[var(--text-primary)]">{data.metrics.months || 0} months</span>
		</div>
	{/if}
	
	<!-- NAV Chart -->
	<Card title="Net Asset Value (NAV) Performance">
		{#snippet children()}
			<div class="flex items-center justify-between mb-4 text-sm">
				<div class="flex gap-4">
					<div class="flex items-center gap-2">
						<div class="w-3 h-1 bg-[var(--green)] rounded"></div>
						<span class="text-[var(--text-primary)]">Strategy</span>
						<span class="color-up">{formatPercent(data.nav.total_return_pct, 2, true)}</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="w-3 h-1 bg-[var(--text-muted)] rounded"></div>
						<span class="text-[var(--text-primary)]">Benchmark</span>
						<span class="color-muted">{formatPercent(data.nav.benchmark_return_pct, 2, true)}</span>
					</div>
				</div>
			</div>
			<LWAreaChart
				data={data.nav.dates.map((d: string, i: number) => ({ time: d.length <= 7 ? d + '-01' : d, value: data.nav.strategy_nav[i] }))}
				secondaryData={data.nav.dates.map((d: string, i: number) => ({ time: d.length <= 7 ? d + '-01' : d, value: data.nav.benchmark_nav[i] }))}
				height={400}
				color="#22c55e"
				secondaryColor="#71717a"
				showLegend={false}
			/>
		{/snippet}
	</Card>
	
	<!-- Holdings -->
	<Card title="Current Holdings (TOP {data.portfolio.top_n})">
		{#snippet children()}
			<div class="mb-4 text-sm text-[var(--text-muted)]">
				Per stock capital: ¥{(data.portfolio.per_stock / 10000).toFixed(2)}万 · 
				Initial capital: ¥{(data.portfolio.initial_capital / 10000).toFixed(2)}万
			</div>
			<DataTable columns={holdingsColumns} data={holdingsWithRank} />
		{/snippet}
	</Card>
	
	<!-- Sensitivity Analysis Summary -->
	{#if data.sensitivity.recommendation}
		<Card title="Strategy Assessment">
			{#snippet children()}
				<div class="space-y-4">
					<!-- Monte Carlo -->
					{#if data.sensitivity.monte_carlo}
						<div class="grid grid-cols-2 md:grid-cols-5 gap-3">
							<div class="bg-[var(--bg-surface)] rounded-lg p-3 text-center border border-[var(--border-default)]">
								<div class="text-label">Mean Return</div>
								<div class="text-data">{formatPercent(data.sensitivity.monte_carlo.mean * 100, 2)}</div>
							</div>
							<div class="bg-[var(--bg-surface)] rounded-lg p-3 text-center border border-[var(--border-default)]">
								<div class="text-label">Std Dev</div>
								<div class="text-data">{formatPercent(data.sensitivity.monte_carlo.std * 100, 2)}</div>
							</div>
							<div class="bg-[var(--bg-surface)] rounded-lg p-3 text-center border border-[var(--border-default)]">
								<div class="text-label">Min</div>
								<div class="text-data color-down">{formatPercent(data.sensitivity.monte_carlo.min * 100, 2)}</div>
							</div>
							<div class="bg-[var(--bg-surface)] rounded-lg p-3 text-center border border-[var(--border-default)]">
								<div class="text-label">Max</div>
								<div class="text-data color-up">{formatPercent(data.sensitivity.monte_carlo.max * 100, 2)}</div>
							</div>
							<div class="bg-[var(--bg-surface)] rounded-lg p-3 text-center border border-[var(--border-default)]">
								<div class="text-label">Simulations</div>
								<div class="text-data">{data.sensitivity.monte_carlo.n}</div>
							</div>
						</div>
					{/if}
					
					<!-- Recommendation -->
					<div class="bg-[var(--blue)]/10 border border-[var(--blue)]/30 rounded-lg p-4">
						<div class="text-sm font-semibold text-[var(--blue)] mb-2">Recommendation</div>
						<div class="text-sm text-[var(--text-primary)]">{data.sensitivity.recommendation}</div>
					</div>
					
					<!-- Confidence Reasons -->
					{#if data.sensitivity.confidence_score?.reasons}
						<div>
							<div class="text-label mb-2">Confidence Factors</div>
							<ul class="space-y-1">
								{#each data.sensitivity.confidence_score.reasons as reason}
									<li class="text-sm text-[var(--text-muted)] flex items-start gap-2">
										<span class="text-[var(--green)]">✓</span>
										<span>{reason}</span>
									</li>
								{/each}
							</ul>
						</div>
					{/if}
				</div>
			{/snippet}
		</Card>
	{/if}
</div>

<style>
	.glow-green {
		box-shadow: 0 0 20px rgba(0, 184, 148, 0.15);
	}
	.glow-red {
		box-shadow: 0 0 20px rgba(231, 76, 60, 0.15);
	}
</style>
