<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const flows = $derived(data.flows as any);
	const allEtfs  = $derived(flows?.flows ?? []);
	const sectorData = $derived(flows?.sector_rotation ?? {});
	const cryptoSummary = $derived(flows?.crypto_etf_summary ?? {});
	const meta = $derived(flows?.metadata ?? {});

	// ── Formatters ────────────────────────────────────────────────────

	function fmtAum(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		const abs = Math.abs(v);
		const prefix = v < 0 ? '-$' : '$';
		if (abs >= 1_000_000_000) return `${prefix}${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `${prefix}${(abs / 1_000_000).toFixed(0)}M`;
		if (abs >= 1_000)         return `${prefix}${(abs / 1_000).toFixed(0)}K`;
		return `${prefix}${abs.toLocaleString()}`;
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

	function fmtFlowPct(v: number | null | undefined): string {
		if (v === null || v === undefined || v === 0) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
	}

	function flowColor(v: number | null | undefined): string {
		if (v === null || v === undefined || v === 0) return 'var(--text-dimmed)';
		return v > 0 ? 'var(--green)' : 'var(--red)';
	}

	function fmtPrice(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return `$${v.toFixed(2)}`;
	}

	// ── ETF lookup helper ─────────────────────────────────────────────

	function getEtfs(tickers: string[]): any[] {
		return tickers
			.map(t => allEtfs.find((f: any) => f.ticker === t))
			.filter(Boolean);
	}

	function sumFlow(rows: any[], field: string): number | null {
		if (!rows.length) return null;
		let sum = 0, hasData = false;
		for (const r of rows) {
			if (r[field] !== null && r[field] !== undefined) { sum += r[field]; hasData = true; }
		}
		return hasData ? sum : null;
	}

	// ── ETF groups ────────────────────────────────────────────────────

	const CRYPTO_TICKERS   = ['IBIT', 'GBTC', 'FBTC', 'ARKB', 'BITB', 'BITO', 'ETHE', 'ETHU'];
	const SECTOR_TICKERS   = ['XLK', 'XLF', 'XLV', 'XLY', 'XLP', 'XLE', 'XLI', 'XLB', 'XLRE', 'XLU', 'XLC'];
	const MEGA_TICKERS     = ['SPY', 'QQQ', 'IWM', 'DIA', 'EEM', 'EFA', 'VTI', 'VOO'];
	const CROSSASSET_TICKERS = ['GLD', 'TLT', 'HYG', 'LQD', 'UUP', 'TIP'];
	const ASIA_TICKERS     = ['FXI', 'KWEB', 'EWJ', 'VNM'];

	const cryptoEtfs   = $derived(getEtfs(CRYPTO_TICKERS));
	const sectorEtfs   = $derived(getEtfs(SECTOR_TICKERS));
	const megaEtfs     = $derived(getEtfs(MEGA_TICKERS));
	const crossEtfs    = $derived(getEtfs(CROSSASSET_TICKERS));
	const asiaEtfs     = $derived(getEtfs(ASIA_TICKERS));

	// ── Risk Sentiment gauge ──────────────────────────────────────────

	const sentiment = $derived(sectorData?.risk_sentiment ?? 0);
	// Map -1..+1 to 0..100 for the bar position
	const sentimentPct = $derived(((sentiment + 1) / 2) * 100);

	function sentimentLabel(v: number): string {
		if (v >= 0.5)  return 'Risk-On';
		if (v >= 0.15) return 'Mild Risk-On';
		if (v > -0.15) return 'Neutral';
		if (v > -0.5)  return 'Mild Risk-Off';
		return 'Risk-Off';
	}

	function sentimentColor(v: number): string {
		if (v >= 0.5)  return 'var(--green)';
		if (v >= 0.15) return '#86efac';  /* light green */
		if (v > -0.15) return 'var(--amber)';
		if (v > -0.5)  return '#fca5a5';  /* light red */
		return 'var(--red)';
	}

	// ── Sector name shorts ─────────────────────────────────────────────
	const SECTOR_NAMES: Record<string, string> = {
		XLK: 'Technology', XLF: 'Financials', XLV: 'Health Care',
		XLY: 'Cons. Disc.', XLP: 'Cons. Staples', XLE: 'Energy',
		XLI: 'Industrials', XLB: 'Materials', XLRE: 'Real Estate',
		XLU: 'Utilities', XLC: 'Comm. Svcs.'
	};
</script>

<svelte:head>
	<title>Fund Flows — Meridian</title>
	<meta name="description" content="ETF fund flows — crypto, sector rotation, mega ETFs, cross-asset, Asia" />
</svelte:head>

<div class="space-y-6">

	<!-- Header -->
	<div class="page-header">
		<div>
			<h1 class="page-title">💰 Fund Flows</h1>
			<p class="page-subtitle">ETF money flows across crypto, sectors, mega-cap, cross-asset &amp; Asia</p>
		</div>
		{#if meta?.last_updated}
			<span class="cache-label">
				Updated {new Date(meta.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
				· {meta.etf_count ?? 0} ETFs
			</span>
		{/if}
	</div>

	{#if data.error}
		<div class="card-base">
			<p class="error-msg">Failed to load fund flows: {data.error}</p>
		</div>
	{:else if flows}

		<!-- ── Risk Sentiment Bar ──────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">MARKET RISK SENTIMENT</div>
			<div class="sentiment-wrapper">
				<div class="sentiment-track">
					<!-- gradient bar -->
					<div class="sentiment-gradient"></div>
					<!-- marker -->
					<div class="sentiment-marker" style="left: {sentimentPct}%"></div>
				</div>
				<div class="sentiment-scale">
					<span>Risk-Off</span>
					<span>Neutral</span>
					<span>Risk-On</span>
				</div>
				<div class="sentiment-readout">
					<span class="sentiment-score" style="color: {sentimentColor(sentiment)}">
						{sentiment >= 0 ? '+' : ''}{sentiment.toFixed(2)}
					</span>
					<span class="sentiment-label" style="color: {sentimentColor(sentiment)}">
						{sentimentLabel(sentiment)}
					</span>
				</div>
			</div>
			{#if sectorData?.top_inflows?.length || sectorData?.top_outflows?.length}
				<div class="rotation-hints">
					{#if sectorData.top_inflows?.length}
						<div class="rotation-group">
							<span class="rotation-tag inflow">▲ INFLOWS</span>
							{#each sectorData.top_inflows.slice(0, 3) as t}
								<span class="ticker-chip">{t}</span>
							{/each}
						</div>
					{/if}
					{#if sectorData.top_outflows?.length}
						<div class="rotation-group">
							<span class="rotation-tag outflow">▼ OUTFLOWS</span>
							{#each sectorData.top_outflows.slice(0, 3) as t}
								<span class="ticker-chip">{t}</span>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- ── Crypto ETFs ───────────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">CRYPTO ETFs</div>

			<!-- Summary row -->
			<div class="summary-bar">
				<div class="sum-stat">
					<span class="sum-label">BTC ETF TOTAL AUM</span>
					<span class="sum-val">{fmtAum(cryptoSummary?.btc_etf_total_aum)}</span>
				</div>
				<div class="sum-stat">
					<span class="sum-label">BTC DAILY FLOW</span>
					<span class="sum-val" style="color: {flowColor(cryptoSummary?.btc_etf_daily_flow ?? sumFlow(cryptoEtfs.filter((e:any) => e.category === 'crypto' && !e.ticker.startsWith('ETH')), 'net_flow_usd'))}">
						{fmtFlow(cryptoSummary?.btc_etf_daily_flow ?? sumFlow(cryptoEtfs, 'net_flow_usd'))}
					</span>
				</div>
				<div class="sum-stat">
					<span class="sum-label">ETH DAILY FLOW</span>
					<span class="sum-val" style="color: {flowColor(cryptoSummary?.eth_etf_daily_flow)}">
						{fmtFlow(cryptoSummary?.eth_etf_daily_flow)}
					</span>
				</div>
			</div>

			{#if cryptoEtfs.length}
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Ticker</th>
								<th>Name</th>
								<th class="text-right">AUM</th>
								<th class="text-right">Daily Flow</th>
								<th class="text-right">Flow % AUM</th>
								<th class="text-right">Price</th>
							</tr>
						</thead>
						<tbody>
							{#each cryptoEtfs as etf}
								<tr>
									<td><span class="ticker-mono">{etf.ticker}</span></td>
									<td class="dim truncate">{etf.name}</td>
									<td class="text-right mono">{fmtAum(etf.total_assets)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.net_flow_usd)}">{fmtFlow(etf.net_flow_usd)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.flow_pct_aum)}">{fmtFlowPct(etf.flow_pct_aum)}</td>
									<td class="text-right mono dim">{fmtPrice(etf.price)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="empty-state">No crypto ETF data available</p>
			{/if}
		</div>

		<!-- ── Sector Rotation ─────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">SECTOR ROTATION — SPDR ETFs</div>
			{#if sectorEtfs.length}
				<div class="sector-grid">
					{#each sectorEtfs as etf}
						<div class="sector-cell" style="border-color: {flowColor(etf.net_flow_usd)}20">
							<div class="sector-cell-top">
								<span class="ticker-mono">{etf.ticker}</span>
								<span class="sector-flow" style="color: {flowColor(etf.net_flow_usd)}">{fmtFlow(etf.net_flow_usd)}</span>
							</div>
							<div class="sector-name">{SECTOR_NAMES[etf.ticker] ?? etf.name}</div>
							<div class="sector-aum dim">{fmtAum(etf.total_assets)}</div>
						</div>
					{/each}
				</div>
			{:else}
				<p class="empty-state">No sector ETF data available</p>
			{/if}
		</div>

		<!-- ── Mega ETFs + Cross-Asset side by side ─────────────────── -->
		<div class="two-col">

			<!-- Mega ETFs -->
			<div class="card-base">
				<div class="section-label">MEGA ETFs</div>
				{#if megaEtfs.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th>Name</th>
									<th class="text-right">AUM</th>
									<th class="text-right">Daily Flow</th>
									<th class="text-right">Flow %</th>
								</tr>
							</thead>
							<tbody>
								{#each megaEtfs as etf}
									<tr>
										<td><span class="ticker-mono">{etf.ticker}</span></td>
										<td class="dim truncate">{etf.name}</td>
										<td class="text-right mono">{fmtAum(etf.total_assets)}</td>
										<td class="text-right mono" style="color: {flowColor(etf.net_flow_usd)}">{fmtFlow(etf.net_flow_usd)}</td>
										<td class="text-right mono" style="color: {flowColor(etf.flow_pct_aum)}">{fmtFlowPct(etf.flow_pct_aum)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No mega ETF data available</p>
				{/if}
			</div>

			<!-- Cross-Asset -->
			<div class="card-base">
				<div class="section-label">CROSS-ASSET</div>
				{#if crossEtfs.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th>Name</th>
									<th class="text-right">AUM</th>
									<th class="text-right">Daily Flow</th>
									<th class="text-right">Flow %</th>
								</tr>
							</thead>
							<tbody>
								{#each crossEtfs as etf}
									<tr>
										<td><span class="ticker-mono">{etf.ticker}</span></td>
										<td class="dim truncate">{etf.name}</td>
										<td class="text-right mono">{fmtAum(etf.total_assets)}</td>
										<td class="text-right mono" style="color: {flowColor(etf.net_flow_usd)}">{fmtFlow(etf.net_flow_usd)}</td>
										<td class="text-right mono" style="color: {flowColor(etf.flow_pct_aum)}">{fmtFlowPct(etf.flow_pct_aum)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No cross-asset ETF data available</p>
				{/if}
			</div>
		</div>

		<!-- ── Asia Markets ───────────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">ASIA MARKETS</div>
			{#if asiaEtfs.length}
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Ticker</th>
								<th>Name</th>
								<th class="text-right">AUM</th>
								<th class="text-right">Daily Flow</th>
								<th class="text-right">Flow % AUM</th>
								<th class="text-right">Price</th>
							</tr>
						</thead>
						<tbody>
							{#each asiaEtfs as etf}
								<tr>
									<td><span class="ticker-mono">{etf.ticker}</span></td>
									<td class="dim truncate">{etf.name}</td>
									<td class="text-right mono">{fmtAum(etf.total_assets)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.net_flow_usd)}">{fmtFlow(etf.net_flow_usd)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.flow_pct_aum)}">{fmtFlowPct(etf.flow_pct_aum)}</td>
									<td class="text-right mono dim">{fmtPrice(etf.price)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="empty-state">No Asia ETF data available</p>
			{/if}
		</div>

	{:else}
		<div class="card-base">
			<div class="loading-state">Loading fund flow data…</div>
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
		margin-bottom: 14px;
	}

	/* ── Risk Sentiment ──────────────────────────────────────────────── */
	.sentiment-wrapper {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.sentiment-track {
		position: relative;
		height: 12px;
		border-radius: 99px;
		overflow: visible;
	}

	.sentiment-gradient {
		position: absolute;
		inset: 0;
		border-radius: 99px;
		background: linear-gradient(to right, var(--red, #ef4444), #f59e0b 50%, var(--green, #22c55e));
		opacity: 0.75;
	}

	.sentiment-marker {
		position: absolute;
		top: 50%;
		transform: translate(-50%, -50%);
		width: 16px;
		height: 16px;
		border-radius: 50%;
		background: var(--text-primary);
		border: 2px solid var(--bg-surface);
		box-shadow: 0 0 0 2px var(--border-default);
		transition: left 600ms ease;
		z-index: 2;
	}

	.sentiment-scale {
		display: flex;
		justify-content: space-between;
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		color: var(--text-dimmed);
		letter-spacing: 0.03em;
		padding: 0 2px;
		margin-top: 4px;
	}

	.sentiment-readout {
		display: flex;
		align-items: baseline;
		gap: 10px;
		margin-top: 8px;
	}

	.sentiment-score {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 28px;
		font-weight: 700;
		line-height: 1;
	}

	.sentiment-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.03em;
	}

	.rotation-hints {
		display: flex;
		gap: 20px;
		flex-wrap: wrap;
		margin-top: 14px;
		padding-top: 14px;
		border-top: 1px solid var(--border-default);
	}

	.rotation-group {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-wrap: wrap;
	}

	.rotation-tag {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.rotation-tag.inflow  { color: var(--green); }
	.rotation-tag.outflow { color: var(--red); }

	.ticker-chip {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 600;
		padding: 2px 7px;
		border-radius: 4px;
		background: var(--bg-elevated);
		color: var(--text-secondary);
	}

	/* ── Summary bar ────────────────────────────────────────────────── */
	.summary-bar {
		display: flex;
		gap: 24px;
		flex-wrap: wrap;
		margin-bottom: 16px;
		padding: 12px 14px;
		background: var(--bg-elevated);
		border-radius: 8px;
	}

	.sum-stat {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.sum-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.sum-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 18px;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1.2;
	}

	/* ── Sector Grid ─────────────────────────────────────────────────── */
	.sector-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 8px;
	}

	.sector-cell {
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		border-radius: 8px;
		padding: 10px 12px;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.sector-cell-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 4px;
	}

	.sector-flow {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 600;
		white-space: nowrap;
	}

	.sector-name {
		font-size: 11px;
		color: var(--text-muted);
		margin-top: 2px;
	}

	.sector-aum {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
	}

	/* ── Tables ───────────────────────────────────────────────────────── */
	.table-wrap {
		overflow-x: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
	}

	.data-table.compact {
		font-size: 12px;
	}

	.data-table th {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		padding: 6px 8px;
		border-bottom: 1px solid var(--border-default);
		text-align: left;
		white-space: nowrap;
	}

	.data-table td {
		padding: 8px 8px;
		border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.04));
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.data-table.compact td {
		padding: 6px 8px;
	}

	.data-table tr:last-child td {
		border-bottom: none;
	}

	.text-right { text-align: right; }

	.mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.dim { color: var(--text-dimmed); }

	.truncate {
		max-width: 160px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.ticker-mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	/* ── States ──────────────────────────────────────────────────────── */
	.empty-state {
		color: var(--text-dimmed);
		font-size: 12px;
		padding: 12px 0;
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
</style>
