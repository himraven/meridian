<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import LWLineChart from '$lib/components/charts/LWLineChart.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const d = $derived(data.data);

	// Format chart data: {date, value} → {time, value}
	function toChartData(rows: {date: string; value: number}[] | undefined) {
		if (!rows) return [];
		return rows.map(r => ({ time: r.date, value: r.value }));
	}

	// Yield chart: {date, spread} → {time, value}
	function toSpreadChart(rows: {date: string; spread: number}[] | undefined) {
		if (!rows) return [];
		return rows.map(r => ({ time: r.date, value: r.spread }));
	}

	// Correlation label + color
	function corrLabel(v: number | null): string {
		if (v === null || v === undefined) return 'N/A';
		const abs = Math.abs(v);
		if (abs < 0.1) return 'Uncorrelated';
		if (abs < 0.3) return v > 0 ? 'Weak positive' : 'Weak negative';
		if (abs < 0.6) return v > 0 ? 'Moderate positive' : 'Moderate negative';
		return v > 0 ? 'Strong positive' : 'Strong negative';
	}

	function corrColor(v: number | null): string {
		if (v === null || v === undefined) return 'var(--text-muted)';
		const abs = Math.abs(v);
		if (abs < 0.1) return 'var(--text-muted)';
		if (abs < 0.3) return 'var(--amber)';
		if (v > 0) return 'var(--green)';
		return 'var(--red)';
	}

	function yieldStatusColor(status: string | undefined): string {
		return status === 'inverted' ? 'var(--red)' : 'var(--green)';
	}

	function m2Color(yoy: number | null): string {
		if (yoy === null || yoy === undefined) return 'var(--text-muted)';
		if (yoy > 8) return 'var(--red)';
		if (yoy > 4) return 'var(--amber)';
		if (yoy > 0) return 'var(--green)';
		return 'var(--blue)'; // deflation
	}

	function fgColor(score: number | undefined): string {
		if (!score) return 'var(--text-muted)';
		if (score >= 75) return 'var(--green)';
		if (score >= 55) return 'var(--amber)';
		if (score >= 35) return '#f97316';
		return 'var(--red)';
	}

	function fmt(v: number | null | undefined, decimals = 2): string {
		if (v === null || v === undefined) return '—';
		return v.toFixed(decimals);
	}

	function fmtBig(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}T`;
		if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}B`;
		return `$${v.toFixed(0)}B`;
	}
</script>

<svelte:head>
	<title>Cross-Asset Signals — Meridian</title>
</svelte:head>

<div class="space-y-6">

	<!-- Header -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Cross-Asset Signals</h1>
			<p class="page-subtitle">Gold/BTC correlation · M2 money supply · Treasury curve · Fear & Greed</p>
		</div>
		{#if d?.cached_at}
			<span class="cache-label">Updated {new Date(d.cached_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
		{/if}
	</div>

	{#if data.error}
		<Card>
			{#snippet children()}
				<p class="error-msg">Failed to load cross-asset data: {data.error}</p>
			{/snippet}
		</Card>
	{:else if d}

		<!-- Row 1: Gold/BTC Correlation + Fear & Greed -->
		<div class="two-col">

			<!-- Gold vs BTC Correlation -->
			<div class="card-base">
				<div class="section-label">GOLD vs BTC CORRELATION</div>
				<div class="asset-prices">
					{#if d.gold_btc_correlation?.gld_price}
						<div class="asset-price-chip">
							<span class="asset-ticker">GLD</span>
							<span class="asset-price">${d.gold_btc_correlation.gld_price?.toFixed(2)}</span>
						</div>
					{/if}
					{#if d.gold_btc_correlation?.btc_price}
						<div class="asset-price-chip">
							<span class="asset-ticker">BTC</span>
							<span class="asset-price">${d.gold_btc_correlation.btc_price?.toLocaleString()}</span>
						</div>
					{/if}
				</div>

				<div class="corr-grid">
					{#each (['30d', '90d', '180d'] as const) as window}
						{@const val = (d.gold_btc_correlation as any)?.[window] ?? null}
						<div class="corr-card">
							<span class="corr-window">{window}</span>
							<span class="corr-value" style="color: {corrColor(val)}">
								{val !== null && val !== undefined ? Number(val).toFixed(3) : '—'}
							</span>
							<span class="corr-label" style="color: {corrColor(val)}">{corrLabel(val)}</span>
						</div>
					{/each}
				</div>

				<p class="section-note">Rolling Pearson correlation between GLD and BTC-USD daily returns</p>

				<!-- Mini chart: BTC 90d -->
				{#if d.gold_btc_correlation?.btc_chart?.length}
					<div class="mini-chart-label">BTC Price (90d)</div>
					<LWLineChart
						data={toChartData(d.gold_btc_correlation.btc_chart)}
						height={120}
						color="#f59e0b"
						class="mini-chart"
					/>
				{/if}
			</div>

			<!-- Fear & Greed -->
			<div class="card-base fear-greed-card">
				<div class="section-label">FEAR & GREED PROXY</div>
				{#if d.fear_greed}
					<div class="fg-hero">
						<div class="fg-gauge">
							<div class="fg-score" style="color: {fgColor(d.fear_greed.score)}">
								{d.fear_greed.score}
							</div>
							<div class="fg-score-label">/100</div>
						</div>
						<div class="fg-info">
							<span class="fg-label" style="color: {fgColor(d.fear_greed.score)}">
								{d.fear_greed.label}
							</span>
							<div class="fg-vix-row">
								<span class="fg-vix-label">VIX</span>
								<span class="fg-vix-val">{d.fear_greed.vix?.toFixed(1)}</span>
							</div>
						</div>
					</div>

					<!-- Gauge bar -->
					<div class="fg-bar-track">
						<div
							class="fg-bar-fill"
							style="width: {d.fear_greed.score}%; background: linear-gradient(90deg, var(--red), var(--amber) 50%, var(--green))"
						></div>
						<div
							class="fg-bar-needle"
							style="left: {d.fear_greed.score}%"
						></div>
					</div>
					<div class="fg-bar-labels">
						<span>Extreme Fear</span>
						<span>Neutral</span>
						<span>Extreme Greed</span>
					</div>

					<p class="fg-narrative">{d.fear_greed.narrative}</p>

					<div class="fg-note">
						Based on VIX (CBOE Volatility Index). Lower VIX = more greed. Higher VIX = more fear.
					</div>
				{/if}
			</div>
		</div>

		<!-- Row 2: M2 Money Supply + Treasury Yields -->
		<div class="two-col">

			<!-- M2 Money Supply -->
			<div class="card-base">
				<div class="section-label">M2 MONEY SUPPLY</div>
				{#if d.m2}
					<div class="m2-hero">
						<div>
							<div class="m2-value">{fmtBig(d.m2.current)}</div>
							<div class="m2-unit">{d.m2.unit ?? 'billions USD'} · FRED: {d.m2.series}</div>
						</div>
						{#if d.m2.yoy_growth_pct !== null && d.m2.yoy_growth_pct !== undefined}
							<div class="m2-yoy" style="color: {m2Color(d.m2.yoy_growth_pct)}">
								<span class="m2-yoy-sign">{d.m2.yoy_growth_pct > 0 ? '+' : ''}</span>{d.m2.yoy_growth_pct.toFixed(1)}% YoY
							</div>
						{/if}
					</div>
					<div class="m2-legend">
						<div class="m2-legend-item">
							<span class="legend-dot" style="background: var(--red)"></span>
							<span>&gt;8% — Inflationary expansion</span>
						</div>
						<div class="m2-legend-item">
							<span class="legend-dot" style="background: var(--amber)"></span>
							<span>4–8% — Moderate growth</span>
						</div>
						<div class="m2-legend-item">
							<span class="legend-dot" style="background: var(--green)"></span>
							<span>0–4% — Normal range</span>
						</div>
						<div class="m2-legend-item">
							<span class="legend-dot" style="background: var(--blue)"></span>
							<span>&lt;0% — Contraction / QT</span>
						</div>
					</div>
					{#if d.m2.chart?.length}
						<div class="mini-chart-label">M2 Supply (36 months)</div>
						<LWLineChart
							data={toChartData(d.m2.chart)}
							height={140}
							color="#60a5fa"
							class="mini-chart"
						/>
					{/if}
				{:else}
					<p class="no-data">M2 data unavailable</p>
				{/if}
			</div>

			<!-- Treasury Yields -->
			<div class="card-base">
				<div class="section-label">TREASURY YIELD CURVE</div>
				{#if d.treasury_yields}
					<div class="yield-hero">
						<div class="yield-status-badge" style="color: {yieldStatusColor(d.treasury_yields.status)}; border-color: {yieldStatusColor(d.treasury_yields.status)}">
							{d.treasury_yields.label ?? '—'}
						</div>
					</div>
					<div class="yield-stats">
						<div class="yield-stat">
							<span class="yield-stat-label">2Y Yield</span>
							<span class="yield-stat-val">{fmt(d.treasury_yields.yield_2y)}%</span>
						</div>
						<div class="yield-divider"></div>
						<div class="yield-stat">
							<span class="yield-stat-label">10Y Yield</span>
							<span class="yield-stat-val">{fmt(d.treasury_yields.yield_10y)}%</span>
						</div>
						<div class="yield-divider"></div>
						<div class="yield-stat">
							<span class="yield-stat-label">10Y−2Y Spread</span>
							<span class="yield-stat-val" style="color: {yieldStatusColor(d.treasury_yields.status)}">
								{d.treasury_yields.spread !== null && d.treasury_yields.spread !== undefined
									? (d.treasury_yields.spread > 0 ? '+' : '') + d.treasury_yields.spread.toFixed(2) + '%'
									: '—'}
							</span>
						</div>
					</div>

					{#if d.treasury_yields.chart?.length}
						<div class="mini-chart-label">10Y−2Y Spread (24 months)</div>
						<LWLineChart
							data={toSpreadChart(d.treasury_yields.chart)}
							height={130}
							color={d.treasury_yields.status === 'inverted' ? '#f87171' : '#22c55e'}
							class="mini-chart"
						/>
					{/if}

					<div class="yield-note">
						<span class="yield-invert-note">
							{#if d.treasury_yields.status === 'inverted'}
								⚠️ Yield curve inverted — historically precedes recession by 12–18 months.
							{:else}
								✓ Normal yield curve — longer-term bonds yield more than short-term.
							{/if}
						</span>
					</div>
					<p class="section-note">Source: FRED GS2 and GS10 series (monthly)</p>
				{:else}
					<p class="no-data">Treasury yield data unavailable</p>
				{/if}
			</div>
		</div>

		<!-- Gold Chart (full width) -->
		{#if d.gold_btc_correlation?.gld_chart?.length}
			<div class="card-base">
				<div class="section-label">GOLD (GLD ETF) — 90 DAYS</div>
				<LWLineChart
					data={toChartData(d.gold_btc_correlation.gld_chart)}
					height={180}
					color="#f59e0b"
					class="mini-chart"
				/>
				<p class="section-note mt-2">SPDR Gold Shares ETF — proxy for gold spot price</p>
			</div>
		{/if}

	{:else}
		<Card>
			{#snippet children()}
				<div class="loading-state">Loading cross-asset data…</div>
			{/snippet}
		</Card>
	{/if}
</div>

<style>
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
	}

	.page-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.page-subtitle {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 2px;
	}

	.cache-label {
		font-size: 11px;
		color: var(--text-dimmed);
		flex-shrink: 0;
	}

	.error-msg {
		color: var(--red);
		font-size: 13px;
		padding: 16px;
	}

	.loading-state {
		text-align: center;
		padding: 32px;
		color: var(--text-muted);
		font-size: 13px;
	}

	.no-data {
		color: var(--text-muted);
		font-size: 13px;
		margin-top: 12px;
	}

	.card-base {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 20px;
	}

	.two-col {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
	}

	@media (max-width: 768px) {
		.two-col { grid-template-columns: 1fr; }
	}

	.section-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-muted);
		margin-bottom: 12px;
	}

	.section-note {
		font-size: 11px;
		color: var(--text-dimmed);
		margin-top: 8px;
	}

	.mt-2 { margin-top: 8px; }

	.mini-chart-label {
		font-size: 11px;
		color: var(--text-dimmed);
		margin-bottom: 6px;
		margin-top: 14px;
		font-family: 'SF Mono', 'Fira Code', monospace;
		letter-spacing: 0.04em;
	}

	:global(.mini-chart) {
		border-radius: 6px;
		overflow: hidden;
	}

	/* Asset prices */
	.asset-prices {
		display: flex;
		gap: 12px;
		margin-bottom: 16px;
		flex-wrap: wrap;
	}

	.asset-price-chip {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--bg-elevated);
		border-radius: 8px;
		padding: 6px 12px;
	}

	.asset-ticker {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--text-dimmed);
	}

	.asset-price {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 13px;
		font-weight: 600;
		color: var(--text-primary);
	}

	/* Correlation */
	.corr-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 10px;
		margin-bottom: 10px;
	}

	.corr-card {
		display: flex;
		flex-direction: column;
		gap: 4px;
		background: var(--bg-elevated);
		border-radius: 8px;
		padding: 10px 12px;
	}

	.corr-window {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.corr-value {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 22px;
		font-weight: 700;
		line-height: 1;
	}

	.corr-label {
		font-size: 11px;
		font-weight: 500;
	}

	/* Fear & Greed */
	.fear-greed-card {}

	.fg-hero {
		display: flex;
		align-items: center;
		gap: 20px;
		margin-bottom: 16px;
	}

	.fg-gauge {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 88px;
		height: 88px;
		border-radius: 50%;
		background: var(--bg-elevated);
		flex-shrink: 0;
	}

	.fg-score {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 30px;
		font-weight: 700;
		line-height: 1;
	}

	.fg-score-label {
		font-size: 11px;
		color: var(--text-dimmed);
	}

	.fg-info {
		flex: 1;
	}

	.fg-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 15px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		display: block;
		margin-bottom: 8px;
	}

	.fg-vix-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.fg-vix-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.fg-vix-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 14px;
		font-weight: 600;
		color: var(--text-secondary);
	}

	.fg-bar-track {
		position: relative;
		width: 100%;
		height: 6px;
		border-radius: 3px;
		background: var(--bg-elevated);
		overflow: visible;
		margin-bottom: 4px;
	}

	.fg-bar-fill {
		height: 100%;
		border-radius: 3px;
		pointer-events: none;
	}

	.fg-bar-needle {
		position: absolute;
		top: -3px;
		transform: translateX(-50%);
		width: 2px;
		height: 12px;
		background: var(--text-primary);
		border-radius: 1px;
	}

	.fg-bar-labels {
		display: flex;
		justify-content: space-between;
		font-size: 10px;
		color: var(--text-dimmed);
		margin-bottom: 12px;
	}

	.fg-narrative {
		font-size: 12px;
		color: var(--text-muted);
		line-height: 1.5;
		margin-bottom: 10px;
	}

	.fg-note {
		font-size: 11px;
		color: var(--text-dimmed);
	}

	/* M2 */
	.m2-hero {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 14px;
		flex-wrap: wrap;
		gap: 10px;
	}

	.m2-value {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 28px;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1;
	}

	.m2-unit {
		font-size: 11px;
		color: var(--text-dimmed);
		margin-top: 4px;
	}

	.m2-yoy {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 20px;
		font-weight: 700;
		text-align: right;
	}

	.m2-yoy-sign { font-size: 16px; }

	.m2-legend {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-bottom: 12px;
	}

	.m2-legend-item {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 11px;
		color: var(--text-muted);
	}

	.legend-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	/* Treasury yields */
	.yield-hero {
		margin-bottom: 14px;
	}

	.yield-status-badge {
		display: inline-block;
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		padding: 4px 10px;
		border: 1px solid;
		border-radius: 6px;
	}

	.yield-stats {
		display: flex;
		align-items: center;
		gap: 16px;
		margin-bottom: 14px;
		flex-wrap: wrap;
	}

	.yield-stat {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.yield-stat-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.yield-stat-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 18px;
		font-weight: 700;
		color: var(--text-primary);
	}

	.yield-divider {
		width: 1px;
		height: 32px;
		background: var(--border-default);
	}

	.yield-note {
		margin-top: 10px;
	}

	.yield-invert-note {
		font-size: 12px;
		color: var(--text-muted);
	}
</style>
