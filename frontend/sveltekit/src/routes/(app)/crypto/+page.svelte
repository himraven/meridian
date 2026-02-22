<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const overview  = $derived(data.overview as any);
	const etfData   = $derived(data.etfData as any);
	const coins     = $derived(
		[...(overview?.coins ?? [])].sort((a: any, b: any) => (b.openInterest ?? 0) - (a.openInterest ?? 0)) as any[]
	);
	const btc       = $derived(overview?.btc ?? {});
	const eth       = $derived(overview?.eth ?? {});
	const fearGreed = $derived(overview?.fear_greed ?? {});
	const meta      = $derived(overview?.metadata ?? {});
	const summary   = $derived(etfData?.crypto_etf_summary ?? {});
	const btcEtf    = $derived({
		total_aum: summary?.btc_etf_total_aum ?? null,
		daily_flow: summary?.btc_etf_daily_flow ?? null,
		weekly_flow: summary?.btc_etf_weekly_flow ?? null,
	});
	const ethEtf    = $derived({
		total_aum: summary?.eth_etf_total_aum ?? null,
		daily_flow: summary?.eth_etf_daily_flow ?? null,
		weekly_flow: summary?.eth_etf_weekly_flow ?? null,
	});

	// ── Formatters ────────────────────────────────────────────────────

	function fmtOI(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		const abs = Math.abs(v);
		if (abs >= 1_000_000_000) return `$${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `$${(abs / 1_000_000).toFixed(0)}M`;
		if (abs >= 1_000)         return `$${(abs / 1_000).toFixed(0)}K`;
		return `$${abs.toLocaleString()}`;
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

	function fmtPct(v: number | null | undefined, decimals = 2): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(decimals)}%`;
	}

	function fmtFunding(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		// funding rate is stored as decimal (e.g. 0.002617), display as %
		const pct = v * 100;
		return `${pct > 0 ? '+' : ''}${pct.toFixed(4)}%`;
	}

	function fmtChange(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
	}

	function changeColor(v: number | null | undefined): string {
		if (v === null || v === undefined) return 'var(--text-dimmed)';
		return v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-muted)';
	}

	function fearGreedColor(v: number): string {
		if (v <= 20)  return 'var(--red)';         // Extreme Fear
		if (v <= 40)  return '#f97316';             // Fear (orange)
		if (v <= 60)  return '#eab308';             // Neutral (yellow)
		if (v <= 80)  return 'var(--green)';        // Greed
		return '#22c55e';                           // Extreme Greed (bright green)
	}

	function collectedAt(ts: string | null | undefined): string {
		if (!ts) return '';
		try {
			const d = new Date(ts);
			const now = Date.now();
			const diffMin = Math.round((now - d.getTime()) / 60000);
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
		{#if meta?.oi_collected_at}
			<span class="cache-label">Updated {collectedAt(meta.oi_collected_at)}</span>
		{/if}
	</div>

	{#if data.error && !overview}
		<!-- Error state -->
		<div class="card-base">
			<p class="error-msg">⚠ Failed to load crypto data: {data.error}</p>
		</div>

	{:else if !overview}
		<!-- Loading state -->
		<div class="card-base">
			<div class="loading-state">
				<div class="spinner"></div>
				<span>Loading crypto overview…</span>
			</div>
		</div>

	{:else}

		<!-- ── KPI Cards ────────────────────────────────────────────── -->
		<div class="kpi-grid">

			<!-- BTC Card -->
			<div class="kpi-card btc-card">
				<div class="kpi-header">
					<span class="kpi-icon btc-icon">₿</span>
					<span class="kpi-title">BTC</span>
				</div>
				<div class="kpi-value">{fmtOI(btc?.openInterest)}</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">Funding</span>
					<span class="kpi-sub-val" style="color: {changeColor(btc?.avgFundingRate)}">{fmtFunding(btc?.avgFundingRate)}</span>
				</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">OI 4h</span>
					<span class="kpi-sub-val" style="color: {changeColor(btc?.h4OIChange)}">{fmtChange(btc?.h4OIChange)}</span>
				</div>
			</div>

			<!-- ETH Card -->
			<div class="kpi-card eth-card">
				<div class="kpi-header">
					<span class="kpi-icon eth-icon">Ξ</span>
					<span class="kpi-title">ETH</span>
				</div>
				<div class="kpi-value">{fmtOI(eth?.openInterest)}</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">Funding</span>
					<span class="kpi-sub-val" style="color: {changeColor(eth?.avgFundingRate)}">{fmtFunding(eth?.avgFundingRate)}</span>
				</div>
				<div class="kpi-subs">
					<span class="kpi-sub-label">OI 4h</span>
					<span class="kpi-sub-val" style="color: {changeColor(eth?.h4OIChange)}">{fmtChange(eth?.h4OIChange)}</span>
				</div>
			</div>

			<!-- Fear & Greed Card -->
			<div class="kpi-card fg-card">
				<div class="kpi-header">
					<span class="kpi-icon fg-icon">◉</span>
					<span class="kpi-title">Fear &amp; Greed</span>
				</div>
				{#if fearGreed?.value !== undefined}
					<div class="kpi-value" style="color: {fearGreedColor(fearGreed.value)}">{fearGreed.value}</div>
					<div class="kpi-subs">
						<span class="kpi-sub-val fg-label" style="color: {fearGreedColor(fearGreed.value)}">{fearGreed.label ?? '—'}</span>
					</div>
					{#if fearGreed.btc_price}
						<div class="kpi-subs">
							<span class="kpi-sub-label">BTC</span>
							<span class="kpi-sub-val dim">${fearGreed.btc_price.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
						</div>
					{/if}
				{:else}
					<div class="kpi-value dim">—</div>
				{/if}
			</div>

			<!-- Total OI Card -->
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
				{#if btc?.h4OIChange !== undefined}
					<div class="kpi-subs">
						<span class="kpi-sub-label">BTC 4h</span>
						<span class="kpi-sub-val" style="color: {changeColor(btc?.h4OIChange)}">{fmtChange(btc?.h4OIChange)}</span>
					</div>
				{/if}
			</div>

		</div>

		<!-- ── OI Table ─────────────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">Top {coins.length} Coins by Open Interest</div>

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
				<a href="/crypto/etf" class="see-more-link">Full ETF details →</a>
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
	/* ── Layout ─────────────────────────────────────────────────────── */
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

	.card-base {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 20px;
	}

	/* ── KPI Grid ────────────────────────────────────────────────────── */
	.kpi-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 14px;
	}

	@media (max-width: 900px) {
		.kpi-grid { grid-template-columns: repeat(2, 1fr); }
	}

	@media (max-width: 480px) {
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
	.fg-card   { border-top: 2px solid rgba(255, 255, 255, 0.1); }
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
	.fg-icon  { color: var(--text-muted); }
	.oi-icon  { color: var(--text-muted); }

	.kpi-title {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.kpi-value {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
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
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		flex-shrink: 0;
	}

	.kpi-sub-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 600;
		color: var(--text-secondary);
	}

	.fg-label {
		font-size: 11px;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	/* ── Section Label ───────────────────────────────────────────────── */
	.section-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
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

	.section-header .section-label {
		margin-bottom: 0;
	}

	.see-more-link {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		text-decoration: none;
		transition: color 0.15s;
	}

	.see-more-link:hover {
		color: var(--text-secondary);
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
		font-family: 'SF Mono', 'Fira Code', monospace;
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
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.dim { color: var(--text-dimmed); }

	.ticker-mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	.rank-col {
		font-family: 'SF Mono', 'Fira Code', monospace;
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
		font-family: 'SF Mono', 'Fira Code', monospace;
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
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.etf-stat-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 14px;
		font-weight: 700;
		color: var(--text-primary);
		text-align: right;
	}

	/* ── Loading & Error states ──────────────────────────────────────── */
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
