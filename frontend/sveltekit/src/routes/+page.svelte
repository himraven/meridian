<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import DataFreshness from '$lib/components/ui/DataFreshness.svelte';
	import { formatCurrency, formatPercent, formatDate } from '$lib/utils/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// ─── Auto-refresh ────────────────────────────────────────────────
	let refreshInterval = $state(300000); // 5 min
	let lastRefresh = $state(new Date());

	$effect(() => {
		const timer = setInterval(() => {
			invalidateAll();
			lastRefresh = new Date();
		}, refreshInterval);
		return () => clearInterval(timer);
	});

	function fmtTime(d: Date): string {
		return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}

	// ─── Signal source text abbreviations ────────────────────────────
	function getSourceTags(signal: {
		congress_score: number;
		ark_score: number;
		darkpool_score: number;
		institution_score: number;
	}): { key: string; label: string; score: number }[] {
		const tags: { key: string; label: string; score: number }[] = [];
		if (signal.congress_score > 0) tags.push({ key: 'congress', label: 'GOV', score: signal.congress_score });
		if (signal.ark_score > 0)      tags.push({ key: 'ark',      label: 'ARK', score: signal.ark_score });
		if (signal.darkpool_score > 0) tags.push({ key: 'darkpool', label: 'DP',  score: signal.darkpool_score });
		if (signal.institution_score > 0) tags.push({ key: 'institution', label: '13F', score: signal.institution_score });
		return tags;
	}

	// ─── Signals (v2 engine, already sorted by conviction) ──────────
	let sortedSignals = $derived(data.signals?.data ?? []);
</script>

<svelte:head>
	<title>Dashboard — Meridian</title>
</svelte:head>

<div class="space-y-6">

	<!-- ── Compact Header ──────────────────────────────────────────────── -->
	<div class="dash-header">
		<div>
			<h1 class="dash-title">Smart Money Dashboard</h1>
			<p class="dash-subtitle">Where smart money signals converge</p>
		</div>
		<div class="dash-refresh">
			<span>Auto-refresh 5m</span>
			<span>Last: {fmtTime(lastRefresh)}</span>
		</div>
	</div>

	<!-- ── Error State ─────────────────────────────────────────────────── -->
	{#if data.error}
		<Card>
			{#snippet children()}
				<div class="text-center py-8">
					<p class="error-text">Error loading dashboard data</p>
					<p class="error-detail">{data.error}</p>
				</div>
			{/snippet}
		</Card>
	{:else}

		<!-- ── KPI Cards ──────────────────────────────────────────────────── -->
		<div class="section-label">MARKET OVERVIEW</div>
		<div class="grid grid-cols-2 md:grid-cols-3 gap-4">

			<!-- CN 12×30 Return -->
			{#if data.cnMetrics}
				<a href="/cn/strategy" class="block">
					<Card hover>
						{#snippet children()}
							<div class="kpi-header">
								<span class="label-mono">CN 12×30</span>
							</div>
							<p class="kpi-value {data.cnMetrics.total_return >= 0 ? 'color-up' : 'color-down'}">
								{formatPercent(data.cnMetrics.total_return, 2, true)}
							</p>
							<p class="kpi-sub">Sharpe: {data.cnMetrics.sharpe.toFixed(2)}</p>
							<DataFreshness lastUpdated={data.cnMetrics.updated_at ?? null} />
						{/snippet}
					</Card>
				</a>
			{/if}

			<!-- HK VMQ Picks -->
			{#if data.hkSignals}
				<a href="/hk" class="block">
					<Card hover>
						{#snippet children()}
							<div class="kpi-header">
								<span class="label-mono">HK VMQ Picks</span>
							</div>
							<p class="kpi-value" style="color: var(--blue);">{data.hkSignals.picks.length}</p>
							<p class="kpi-sub">{data.hkSignals.date}</p>
							<DataFreshness lastUpdated={data.hkSignals.updated_at ?? null} />
						{/snippet}
					</Card>
				</a>
			{/if}

			<!-- Smart Money Signals -->
			{#if data.signals}
				<a href="/signals" class="block">
					<Card hover>
						{#snippet children()}
							<div class="kpi-header">
								<span class="label-mono">Smart Money</span>
							</div>
							<p class="kpi-value" style="color: var(--blue);">{data.signals.metadata.filtered}</p>
							<p class="kpi-sub">
								{data.signals.data.filter(s => s.score >= 60).length} high conviction
							</p>
						{/snippet}
					</Card>
				</a>
			{/if}
		</div>

		<!-- ── Strategy Detail Row ────────────────────────────────────────── -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">

			<!-- CN 12×30 Detail -->
			{#if data.cnMetrics}
				<Card title="CN 12×30 Strategy">
					{#snippet children()}
						<div class="grid grid-cols-3 gap-3 text-center">
							<div>
								<p class="stat-label">Return</p>
								<p class="stat-value {data.cnMetrics.total_return >= 0 ? 'color-up' : 'color-down'}">
									{formatPercent(data.cnMetrics.total_return, 2, true)}
								</p>
							</div>
							<div>
								<p class="stat-label">Sharpe</p>
								<p class="stat-value" style="color: var(--text-primary);">{data.cnMetrics.sharpe.toFixed(2)}</p>
							</div>
							<div>
								<p class="stat-label">Max DD</p>
								<p class="stat-value color-down">
									{formatPercent(data.cnMetrics.max_drawdown, 2, true)}
								</p>
							</div>
						</div>
					{/snippet}
				</Card>
			{/if}

			<!-- HK Top 3 Picks Preview -->
			{#if data.hkSignals?.picks?.length}
				<Card title="HK VMQ Top 3">
					{#snippet children()}
						<div class="space-y-2">
							{#each data.hkSignals.picks.slice(0, 3) as pick}
								<div class="flex items-center justify-between text-sm">
									<div class="flex items-center gap-2">
										<span class="font-mono font-bold text-[var(--blue)]">{pick.ticker}</span>
										<span class="text-[var(--text-muted)] text-xs truncate max-w-[100px]">{pick.name}</span>
									</div>
									<span class="font-semibold text-[var(--text-primary)]">{pick.vmq_score?.toFixed(1)}</span>
								</div>
							{/each}
						</div>
					{/snippet}
				</Card>
			{/if}
		</div>

		<!-- ── Recent Smart Money Signals ───────────────────────────────── -->
		{#if sortedSignals.length > 0}
			<div>
				<div class="section-label">SIGNALS</div>
				<Card badge={String(data.signals?.metadata.total ?? '')}>
					{#snippet children()}
						<div class="space-y-2">
							{#each sortedSignals.slice(0, 5) as signal}
								<a
									href="/ticker/{signal.ticker}"
									class="signal-row"
								>
									<div class="signal-top">
										<div class="signal-left">
											<span class="signal-ticker">{signal.ticker}</span>
											<span class="signal-company">{signal.company}</span>
											<span class="signal-sources">
												{#each getSourceTags(signal) as tag}
													<span class="source-tag">{tag.label}</span>
												{/each}
											</span>
										</div>
										<div class="signal-right">
											<Badge variant={signal.direction === 'bullish' ? 'bullish' : signal.direction === 'bearish' ? 'bearish' : 'neutral'}>
												{signal.direction}
											</Badge>
											<span class="signal-score">{signal.score.toFixed(0)}</span>
										</div>
									</div>
									<div class="signal-scores">
										<span>GOV {signal.congress_score}</span>
										<span>ARK {signal.ark_score}</span>
										<span>DP {signal.darkpool_score}</span>
										<span>13F {signal.institution_score}</span>
										<span class="signal-date">{formatDate(signal.signal_date)}</span>
									</div>
								</a>
							{/each}
							{#if sortedSignals.length > 5}
								<a
									href="/signals"
									class="signals-more-link"
								>
									View all {data.signals?.metadata.total} signals →
								</a>
							{/if}
						</div>
					{/snippet}
				</Card>
			</div>
		{/if}

	{/if}
</div>

<style>
	.dash-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
	}

	.dash-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--text-primary);
		line-height: 1.3;
	}

	.dash-subtitle {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 2px;
	}

	.dash-refresh {
		font-size: 11px;
		color: var(--text-muted);
		text-align: right;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.section-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-muted);
		margin-bottom: 8px;
	}

	.kpi-header {
		margin-bottom: 8px;
	}

	.kpi-value {
		font-size: 26px;
		font-weight: 700;
		line-height: 1.2;
		font-variant-numeric: tabular-nums;
		letter-spacing: -0.02em;
	}

	.kpi-sub {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 4px;
	}

	.stat-label {
		font-size: 11px;
		color: var(--text-muted);
		margin-bottom: 4px;
	}

	.stat-value {
		font-size: 17px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.error-text {
		color: var(--color-down);
		margin-bottom: 8px;
		font-weight: 500;
	}

	.error-detail {
		font-size: 13px;
		color: var(--text-muted);
	}

	.signal-row {
		display: block;
		padding: 12px 14px;
		background: var(--bg-page);
		border: 1px solid var(--border-default);
		border-radius: 10px;
		text-decoration: none;
		transition: border-color 0.1s ease;
	}

	.signal-row:hover {
		border-color: var(--border-hover);
	}

	.signal-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 6px;
	}

	.signal-left {
		display: flex;
		align-items: center;
		gap: 8px;
		flex: 1;
		min-width: 0;
	}

	.signal-ticker {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-weight: 700;
		font-size: 14px;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	.signal-company {
		font-size: 12px;
		color: var(--text-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: 140px;
	}

	.signal-sources {
		display: flex;
		gap: 4px;
	}

	.source-tag {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.04em;
		padding: 1px 5px;
		border-radius: 3px;
		background: rgba(255, 255, 255, 0.06);
		color: var(--text-dimmed);
	}

	.signal-right {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}

	.signal-score {
		font-size: 16px;
		font-weight: 700;
		color: var(--text-primary);
		font-variant-numeric: tabular-nums;
	}

	.signal-scores {
		display: flex;
		align-items: center;
		gap: 12px;
		font-size: 11px;
		color: var(--text-muted);
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-variant-numeric: tabular-nums;
	}

	.signal-date {
		margin-left: auto;
		color: var(--text-dimmed);
	}

	.signals-more-link {
		display: block;
		text-align: center;
		padding: 10px;
		font-size: 13px;
		color: var(--color-blue);
		text-decoration: none;
		transition: color 0.1s ease;
	}

	.signals-more-link:hover {
		color: var(--text-secondary);
	}
</style>
