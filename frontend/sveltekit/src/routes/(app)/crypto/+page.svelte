<script lang="ts">
	import LWLineChart from '$lib/components/charts/LWLineChart.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const overview       = $derived(data.overview as any);
	const etfData        = $derived(data.etfData as any);
	const fgData         = $derived(data.fearGreed as any);
	const cryptoSignals  = $derived(data.cryptoSignals as any);

	// ── Overview-derived ────────────────────────────────────────────
	const coins   = $derived(
		[...(overview?.coins ?? [])].sort((a: any, b: any) => (b.openInterest ?? 0) - (a.openInterest ?? 0)) as any[]
	);
	const btcOI   = $derived(overview?.btc ?? {});
	const ethOI   = $derived(overview?.eth ?? {});
	const fgKpi   = $derived(overview?.fear_greed ?? {});
	const meta    = $derived(overview?.metadata ?? {});

	// ── ETF-derived ─────────────────────────────────────────────────
	const summary = $derived(etfData?.crypto_etf_summary ?? {});
	const btcEtf  = $derived({
		total_aum:    summary?.btc_etf_total_aum  ?? null,
		daily_flow:   summary?.btc_etf_daily_flow  ?? null,
		weekly_flow:  summary?.btc_etf_weekly_flow ?? null,
	});
	const ethEtf  = $derived({
		total_aum:    summary?.eth_etf_total_aum  ?? null,
		daily_flow:   summary?.eth_etf_daily_flow  ?? null,
		weekly_flow:  summary?.eth_etf_weekly_flow ?? null,
	});

	// ── Price cards ─────────────────────────────────────────────────
	const btcPrice = $derived(cryptoSignals?.crypto_prices?.btc);
	const ethPrice = $derived(cryptoSignals?.crypto_prices?.eth);

	// ── Smart Money ─────────────────────────────────────────────────
	const topSignals = $derived((cryptoSignals?.smart_money_signals ?? []).slice(0, 3) as any[]);

	// ── Fear & Greed ─────────────────────────────────────────────────
	const fgCurrent = $derived(fgData?.current ?? fgKpi ?? {});
	const fgChartData = $derived(
		(fgData?.entries ?? []).map((e: any) => ({ time: e.date, value: e.value }))
	);

	// ── Chart helpers ─────────────────────────────────────────────────
	function toChartData(rows: { date: string; value: number }[] | undefined | null) {
		if (!rows?.length) return [];
		return rows.map(r => ({ time: r.date, value: r.value }));
	}

	// ── Formatters ────────────────────────────────────────────────────

	function fmtOI(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		const abs = Math.abs(v);
		if (abs >= 1_000_000_000) return `$${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `$${(abs / 1_000_000).toFixed(0)}M`;
		if (abs >= 1_000)         return `$${(abs / 1_000).toFixed(0)}K`;
		return `$${abs.toLocaleString()}`;
	}

	function fmtPrice(v: number | null | undefined): string {
		if (v == null) return '—';
		if (v >= 1000) return `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
		return `$${v.toFixed(2)}`;
	}

	function fmtFlow(v: number | null | undefined): string {
		if (v === null || v === undefined || v === 0) return '—';
		const abs = Math.abs(v);
		const prefix = v > 0 ? '+$' : '-$';
		if (abs >= 1_000_000_000) return `${prefix}${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `${prefix}${(abs / 1_000_000).toFixed(0)}M`;
		if (abs >= 1_000)         return `${prefix}${(abs / 1_000).toFixed(0)}K`;
		return `${prefix}${abs.toLocaleString()}`;
	}

	function fmtFunding(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		const pct = v * 100;
		return `${pct > 0 ? '+' : ''}${pct.toFixed(4)}%`;
	}

	function fmtChange(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
	}

	function fmtScore(v: number | null | undefined): string {
		if (v == null) return '—';
		return v.toFixed(1);
	}

	function changeColor(v: number | null | undefined): string {
		if (v === null || v === undefined) return 'var(--text-dimmed)';
		return v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-muted)';
	}

	function scoreColor(v: number | null | undefined): string {
		if (v == null) return 'var(--text-dimmed)';
		if (v >= 70) return 'var(--green)';
		if (v >= 50) return 'var(--amber)';
		return 'var(--red)';
	}

	function fearGreedColor(v: number | null | undefined): string {
		if (v == null) return 'var(--text-muted)';
		if (v <= 20)  return 'var(--red)';
		if (v <= 40)  return '#f97316';
		if (v <= 60)  return '#eab308';
		if (v <= 80)  return 'var(--green)';
		return '#22c55e';
	}

	function collectedAt(ts: string | null | undefined): string {
		if (!ts) return '';
		try {
			const d = new Date(ts);
			const diffMin = Math.round((Date.now() - d.getTime()) / 60000);
			if (diffMin < 1)   return 'just now';
			if (diffMin < 60)  return `${diffMin}m ago`;
			const h = Math.floor(diffMin / 60);
			return `${h}h ago`;
		} catch {
			return '';
		}
	}
</script>

<svelte:head>
	<title>Crypto Overview — Meridian</title>
	<meta name="description" content="Crypto derivatives market overview — open interest, funding rates, fear & greed index, ETF flows" />
</svelte:head>

<div class="space-y-6">

	<!-- ── Header ──────────────────────────────────────────────────── -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Crypto Market Overview</h1>
			<p class="page-subtitle">Open interest, funding rates, fear & greed, and ETF flows</p>
		</div>
	</div>

	{#if data.error && !overview}
		<div class="card-base">
			<p class="error-msg">⚠ Failed to load crypto data: {data.error}</p>
		</div>

	{:else if !overview}
		<div class="card-base">
			<div class="loading-state">
				<div class="spinner"></div>
				<span>Loading crypto overview…</span>
			</div>
		</div>

	{:else}

		<!-- ── BTC / ETH Price Cards ────────────────────────────────── -->
		{#if cryptoSignals}
			<div class="section-ts-row">
				<span class="section-ts-label">Prices</span>
				{#if cryptoSignals.cached_at}
					<span class="section-ts">{collectedAt(cryptoSignals.cached_at)}</span>
				{/if}
			</div>
			<div class="two-col">

				<!-- BTC Price -->
				<div class="card-base price-card btc-price-card">
					<div class="price-header">
						<span class="price-symbol btc-sym">₿</span>
						<span class="price-name">BITCOIN</span>
					</div>
					<div class="price-row">
						<span class="price-value">{fmtPrice(btcPrice?.price)}</span>
						<span class="price-change" style="color: {changeColor(btcPrice?.change_24h_pct)}">
							{fmtChange(btcPrice?.change_24h_pct)}
						</span>
					</div>
					{#if btcPrice?.chart_90d?.length}
						<div class="chart-sublabel">90-Day Price</div>
						<LWLineChart
							data={toChartData(btcPrice.chart_90d)}
							height={120}
							color="#f59e0b"
						/>
					{/if}
				</div>

				<!-- ETH Price -->
				<div class="card-base price-card eth-price-card">
					<div class="price-header">
						<span class="price-symbol eth-sym">Ξ</span>
						<span class="price-name">ETHEREUM</span>
					</div>
					<div class="price-row">
						<span class="price-value">{fmtPrice(ethPrice?.price)}</span>
						<span class="price-change" style="color: {changeColor(ethPrice?.change_24h_pct)}">
							{fmtChange(ethPrice?.change_24h_pct)}
						</span>
					</div>
					{#if ethPrice?.chart_90d?.length}
						<div class="chart-sublabel">90-Day Price</div>
						<LWLineChart
							data={toChartData(ethPrice.chart_90d)}
							height={120}
							color="#818cf8"
						/>
					{/if}
				</div>

			</div>
		{/if}

		<!-- ── Fear & Greed Section ─────────────────────────────────── -->
		<div class="card-base fg-section">
			<div class="section-header-inline">
				<div class="section-label">FEAR &amp; GREED INDEX</div>
				{#if fgData?.metadata?.collected_at}
					<span class="section-ts">{collectedAt(fgData.metadata.collected_at)}</span>
				{/if}
			</div>
			<div class="fg-inner">

				<!-- Left: current reading -->
				<div class="fg-left">
					{#if fgCurrent?.value !== undefined}
						<div class="fg-big-val" style="color: {fearGreedColor(fgCurrent.value)}">
							{fgCurrent.value}
						</div>
						<div class="fg-big-label" style="color: {fearGreedColor(fgCurrent.value)}">
							{fgCurrent.label ?? '—'}
						</div>
						{#if fgCurrent.btc_price}
							<div class="fg-btc-price">
								BTC at ${fgCurrent.btc_price.toLocaleString(undefined, { maximumFractionDigits: 0 })}
							</div>
						{/if}
					{:else}
						<div class="fg-big-val dim">—</div>
					{/if}
				</div>

				<!-- Right: 30-day sparkline -->
				<div class="fg-right">
					{#if fgChartData.length}
						<div class="chart-sublabel">30-Day History</div>
						<LWLineChart
							data={fgChartData}
							height={110}
							color="#eab308"
						/>
					{:else if fgKpi?.value !== undefined}
						<!-- Fallback: no history, just show the KPI values -->
						<div class="fg-fallback">
							<span class="fg-sub-label">Current</span>
							<span class="fg-sub-val" style="color: {fearGreedColor(fgKpi.value)}">{fgKpi.value} — {fgKpi.label ?? ''}</span>
						</div>
					{/if}
				</div>

			</div>
		</div>

		<!-- ── KPI Cards (OI only — F&G has its own section) ───────── -->
		<div class="kpi-grid">

			<!-- BTC OI -->
			<div class="kpi-card btc-card">
				<div class="kpi-header">
					<span class="kpi-icon btc-icon">₿</span>
					<span class="kpi-title">BTC OI</span>
				</div>
				<div class="kpi-value">{fmtOI(btcOI?.openInterest)}</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">Funding</span>
					<span class="kpi-sub-val" style="color: {changeColor(btcOI?.avgFundingRate)}">{fmtFunding(btcOI?.avgFundingRate)}</span>
				</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">OI 4h</span>
					<span class="kpi-sub-val" style="color: {changeColor(btcOI?.h4OIChange)}">{fmtChange(btcOI?.h4OIChange)}</span>
				</div>
			</div>

			<!-- ETH OI -->
			<div class="kpi-card eth-card">
				<div class="kpi-header">
					<span class="kpi-icon eth-icon">Ξ</span>
					<span class="kpi-title">ETH OI</span>
				</div>
				<div class="kpi-value">{fmtOI(ethOI?.openInterest)}</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">Funding</span>
					<span class="kpi-sub-val" style="color: {changeColor(ethOI?.avgFundingRate)}">{fmtFunding(ethOI?.avgFundingRate)}</span>
				</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">OI 4h</span>
					<span class="kpi-sub-val" style="color: {changeColor(ethOI?.h4OIChange)}">{fmtChange(ethOI?.h4OIChange)}</span>
				</div>
			</div>

			<!-- Total OI -->
			<div class="kpi-card oi-card">
				<div class="kpi-header">
					<span class="kpi-icon oi-icon">∑</span>
					<span class="kpi-title">Total OI</span>
				</div>
				<div class="kpi-value">{fmtOI(overview?.total_oi)}</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">Coins</span>
					<span class="kpi-sub-val dim">{meta?.coin_count ?? coins.length}</span>
				</div>
				{#if btcOI?.h4OIChange !== undefined}
					<div class="kpi-subs">
						<span class="kpi-sub-label">BTC 4h</span>
						<span class="kpi-sub-val" style="color: {changeColor(btcOI?.h4OIChange)}">{fmtChange(btcOI?.h4OIChange)}</span>
					</div>
				{/if}
			</div>

		</div>

		<!-- ── Smart Money Highlight ────────────────────────────────── -->
		{#if topSignals.length}
			<div class="card-base">
				<div class="section-header">
					<div class="section-label">SMART MONEY — CRYPTO EQUITIES</div>
					<a href="/crypto/equities" class="see-more-link">View all equity signals →</a>
				</div>

				<div class="sm-rows">
					{#each topSignals as sig}
						<div class="sm-row">
							<a href="/ticker/{sig.ticker}" class="sm-ticker">{sig.ticker}</a>
							{#if sig.company}
								<span class="sm-company">{sig.company}</span>
							{/if}
							<span class="sm-score" style="color: {scoreColor(sig.score)}">{fmtScore(sig.score)}</span>
							<span
								class="sm-dir-badge"
								class:bullish={sig.direction?.toLowerCase() === 'bullish'}
								class:bearish={sig.direction?.toLowerCase() === 'bearish'}
							>{sig.direction ?? '—'}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- ── OI Table ─────────────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-header-inline">
				<div class="section-label">Top {coins.length} Coins by Open Interest</div>
				{#if meta?.oi_collected_at}
					<span class="section-ts">{collectedAt(meta.oi_collected_at)}</span>
				{/if}
			</div>

			{#if coins.length}
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>#</th>
								<th>Coin</th>
								<th class="text-right">Open Interest</th>
								<th class="text-right">Vol 24h</th>
								<th class="text-right">Funding Rate</th>
								<th class="text-right">ΔOI 1h</th>
								<th class="text-right">ΔOI 4h</th>
								<th class="text-right">ΔOI 7d</th>
								<th class="text-right">OI/Vol</th>
							</tr>
						</thead>
						<tbody>
							{#each coins as coin, i}
								<tr>
									<td class="rank-col dim">#{i + 1}</td>
									<td><span class="ticker-mono">{coin.symbol}</span></td>
									<td class="text-right mono">{fmtOI(coin.openInterest)}</td>
									<td class="text-right mono dim">{fmtOI(coin.volUsd)}</td>
									<td class="text-right mono" style="color: {changeColor(coin.avgFundingRate)}">{fmtFunding(coin.avgFundingRate)}</td>
									<td class="text-right mono" style="color: {changeColor(coin.h1OIChange)}">{fmtChange(coin.h1OIChange)}</td>
									<td class="text-right mono" style="color: {changeColor(coin.h4OIChange)}">{fmtChange(coin.h4OIChange)}</td>
									<td class="text-right mono" style="color: {changeColor(coin.oiChange7d)}">{fmtChange(coin.oiChange7d)}</td>
									<td class="text-right mono dim">{coin.oiVolRatio != null ? coin.oiVolRatio.toFixed(2) : '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="empty-state">No coin data available</p>
			{/if}
		</div>

		<!-- ── ETF Flow Summary ─────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-header">
				<div class="section-label">ETF Flow Summary</div>
				<div class="section-header-right">
					{#if etfData?.metadata?.last_updated}
						<span class="section-ts">{collectedAt(etfData.metadata.last_updated)}</span>
					{/if}
					<a href="/crypto/etf" class="see-more-link">Full ETF details →</a>
				</div>
			</div>

			{#if !etfData}
				<p class="empty-state">ETF data unavailable</p>
			{:else}
				<div class="etf-cards">

					<!-- BTC ETFs -->
					<div class="etf-card btc-etf">
						<div class="etf-card-header">
							<span class="etf-icon btc-icon">₿</span>
							<span class="etf-label">BTC ETFs</span>
						</div>
						<div class="etf-stats">
							<div class="etf-row">
								<span class="etf-stat-label">AUM</span>
								<span class="etf-stat-val">{fmtOI(btcEtf?.total_aum)}</span>
							</div>
							<div class="etf-row">
								<span class="etf-stat-label">Daily Flow</span>
								<span class="etf-stat-val" style="color: {changeColor(btcEtf?.daily_flow)}">{fmtFlow(btcEtf?.daily_flow)}</span>
							</div>
							<div class="etf-row">
								<span class="etf-stat-label">Weekly Flow</span>
								<span class="etf-stat-val" style="color: {changeColor(btcEtf?.weekly_flow)}">{fmtFlow(btcEtf?.weekly_flow)}</span>
							</div>
						</div>
					</div>

					<!-- ETH ETFs -->
					<div class="etf-card eth-etf">
						<div class="etf-card-header">
							<span class="etf-icon eth-icon">Ξ</span>
							<span class="etf-label">ETH ETFs</span>
						</div>
						<div class="etf-stats">
							<div class="etf-row">
								<span class="etf-stat-label">AUM</span>
								<span class="etf-stat-val">{fmtOI(ethEtf?.total_aum)}</span>
							</div>
							<div class="etf-row">
								<span class="etf-stat-label">Daily Flow</span>
								<span class="etf-stat-val" style="color: {changeColor(ethEtf?.daily_flow)}">{fmtFlow(ethEtf?.daily_flow)}</span>
							</div>
							<div class="etf-row">
								<span class="etf-stat-label">Weekly Flow</span>
								<span class="etf-stat-val" style="color: {changeColor(ethEtf?.weekly_flow)}">{fmtFlow(ethEtf?.weekly_flow)}</span>
							</div>
						</div>
					</div>

				</div>
			{/if}
		</div>

	{/if}

</div>

<style>
	/* ── Spacing ────────────────────────────────────────────────────── */
	.space-y-6 > * + * { margin-top: 24px; }

	/* ── Page Header ────────────────────────────────────────────────── */
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
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
		white-space: nowrap;
	}

	/* ── Card Base ──────────────────────────────────────────────────── */
	.card-base {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 20px;
	}

	/* ── Two-col grid ───────────────────────────────────────────────── */
	.two-col {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
	}

	@media (max-width: 768px) {
		.two-col { grid-template-columns: 1fr; }
	}

	/* ── BTC/ETH Price Cards ────────────────────────────────────────── */
	.price-card {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.btc-price-card { border-top: 2px solid rgba(245, 158, 11, 0.35); }
	.eth-price-card { border-top: 2px solid rgba(129, 140, 248, 0.35); }

	.price-header {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.price-symbol {
		font-size: 18px;
		font-weight: 800;
		line-height: 1;
	}

	.btc-sym { color: #f59e0b; }
	.eth-sym { color: #818cf8; }

	.price-name {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.07em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.price-row {
		display: flex;
		align-items: baseline;
		gap: 12px;
		flex-wrap: wrap;
	}

	.price-value {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 32px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: -0.02em;
		line-height: 1;
	}

	.price-change {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 16px;
		font-weight: 600;
	}

	.chart-sublabel {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		margin-top: 4px;
		margin-bottom: 6px;
	}

	/* ── Fear & Greed Section ───────────────────────────────────────── */
	.fg-section {
		/* Full-width card */
	}

	.fg-inner {
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 24px;
		align-items: center;
	}

	@media (max-width: 640px) {
		.fg-inner { grid-template-columns: 1fr; }
	}

	.fg-left {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.fg-big-val {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 64px;
		font-weight: 800;
		line-height: 1;
		letter-spacing: -0.02em;
	}

	.fg-big-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.fg-btc-price {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		margin-top: 4px;
	}

	.fg-fallback {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.fg-sub-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.fg-sub-val {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 14px;
		font-weight: 700;
	}

	.fg-right {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	/* ── KPI Grid (3 cards) ─────────────────────────────────────────── */
	.kpi-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 14px;
	}

	@media (max-width: 768px) {
		.kpi-grid { grid-template-columns: 1fr; }
	}

	.kpi-card {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 18px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.btc-card { border-top: 2px solid #f7931a50; }
	.eth-card  { border-top: 2px solid #627eea50; }
	.oi-card   { border-top: 2px solid rgba(255, 255, 255, 0.1); }

	.kpi-header {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 4px;
	}

	.kpi-icon {
		font-size: 16px;
		font-weight: 700;
		line-height: 1;
	}

	.btc-icon { color: #f7931a; }
	.eth-icon { color: #627eea; }
	.oi-icon  { color: var(--text-muted); }

	.kpi-title {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.kpi-value {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 22px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: -0.01em;
		line-height: 1.1;
	}

	.kpi-subs {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.kpi-sub-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		flex-shrink: 0;
	}

	.kpi-sub-val {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 12px;
		font-weight: 600;
		color: var(--text-secondary);
	}

	/* ── Section Labels ─────────────────────────────────────────────── */
	.section-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.07em;
		text-transform: uppercase;
		color: var(--text-muted);
		margin-bottom: 14px;
	}

	.section-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 14px;
	}

	.section-header-right {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.section-header-inline {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 14px;
	}

	.section-header-inline .section-label {
		margin-bottom: 0;
	}

	.section-ts-row {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 6px;
	}

	.section-ts-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.section-ts {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		color: var(--text-dimmed);
		opacity: 0.7;
	}

	.section-header .section-label {
		margin-bottom: 0;
	}

	.see-more-link {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		text-decoration: none;
		transition: color 0.15s;
	}

	.see-more-link:hover {
		color: var(--text-secondary);
	}

	/* ── Smart Money Highlight ──────────────────────────────────────── */
	.sm-rows {
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.sm-row {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 10px 0;
		border-bottom: 1px solid var(--border-default);
	}

	.sm-row:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}

	.sm-row:first-child {
		padding-top: 0;
	}

	.sm-ticker {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 13px;
		font-weight: 700;
		color: var(--text-primary);
		text-decoration: none;
		letter-spacing: 0.03em;
		min-width: 56px;
		transition: color 0.15s;
	}

	.sm-ticker:hover {
		color: var(--blue, #818cf8);
	}

	.sm-company {
		font-size: 12px;
		color: var(--text-dimmed);
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.sm-score {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 13px;
		font-weight: 700;
		min-width: 36px;
		text-align: right;
	}

	.sm-dir-badge {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		padding: 2px 7px;
		border-radius: 4px;
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		color: var(--text-dimmed);
		white-space: nowrap;
	}

	.sm-dir-badge.bullish {
		color: var(--green);
		background: rgba(34, 197, 94, 0.08);
		border-color: rgba(34, 197, 94, 0.2);
	}

	.sm-dir-badge.bearish {
		color: var(--red);
		background: rgba(239, 68, 68, 0.08);
		border-color: rgba(239, 68, 68, 0.2);
	}

	/* ── OI Table ────────────────────────────────────────────────────── */
	.table-wrap {
		overflow-x: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 12px;
	}

	.data-table th {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		padding: 5px 8px;
		border-bottom: 1px solid var(--border-default);
		text-align: left;
		white-space: nowrap;
	}

	.data-table td {
		padding: 7px 8px;
		border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.04));
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.data-table tr:last-child td {
		border-bottom: none;
	}

	.data-table tr:hover td {
		background: var(--bg-elevated);
	}

	.text-right { text-align: right; }

	.mono {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
	}

	.dim { color: var(--text-dimmed); }

	.ticker-mono {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	.rank-col {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		width: 32px;
		min-width: 32px;
	}

	/* ── ETF Summary ─────────────────────────────────────────────────── */
	.etf-cards {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 14px;
	}

	@media (max-width: 640px) {
		.etf-cards { grid-template-columns: 1fr; }
	}

	.etf-card {
		background: var(--bg-elevated, rgba(255,255,255,0.03));
		border: 1px solid var(--border-default);
		border-radius: 10px;
		padding: 16px;
	}

	.btc-etf { border-top: 2px solid #f7931a40; }
	.eth-etf  { border-top: 2px solid #627eea40; }

	.etf-card-header {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 12px;
	}

	.etf-icon {
		font-size: 16px;
		font-weight: 700;
	}

	.etf-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--text-primary);
	}

	.etf-stats {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.etf-row {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
	}

	.etf-stat-label {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.etf-stat-val {
		font-family: 'JetBrains Mono', 'SF Mono', monospace;
		font-size: 14px;
		font-weight: 700;
		color: var(--text-primary);
		text-align: right;
	}

	/* ── Loading & Error ─────────────────────────────────────────────── */
	.loading-state {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 40px;
		color: var(--text-muted);
		font-size: 13px;
	}

	.spinner {
		width: 18px;
		height: 18px;
		border: 2px solid var(--border-default);
		border-top-color: var(--text-muted);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		flex-shrink: 0;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error-msg {
		color: var(--red);
		font-size: 13px;
		padding: 16px;
	}

	.empty-state {
		color: var(--text-dimmed);
		font-size: 12px;
		padding: 12px 0;
	}
</style>
