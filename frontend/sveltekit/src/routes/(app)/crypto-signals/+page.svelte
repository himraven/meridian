<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import LWLineChart from '$lib/components/charts/LWLineChart.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const d = $derived(data.data);

	function toChartData(rows: {date: string; value: number}[] | undefined) {
		if (!rows) return [];
		return rows.map(r => ({ time: r.date, value: r.value }));
	}

	function fmtPrice(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		if (v >= 1000) return `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
		return `$${v.toFixed(2)}`;
	}

	function fmtChange(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
	}

	function changeColor(v: number | null | undefined): string {
		if (v === null || v === undefined) return 'var(--text-muted)';
		return v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-muted)';
	}

	function fmtScore(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return v.toFixed(1);
	}

	function scoreColor(v: number | null | undefined): string {
		if (v === null || v === undefined) return 'var(--text-muted)';
		if (v >= 70) return 'var(--green)';
		if (v >= 50) return 'var(--amber)';
		return 'var(--red)';
	}

	function fmtVol(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}B`;
		if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
		if (v >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
		return v.toLocaleString();
	}

	function fmtPct(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`;
	}

	function fmtDpi(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return (v * 100).toFixed(1) + '%';
	}

	function fmtMoney(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
		if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
		return `$${v.toLocaleString()}`;
	}

	function fmtDtc(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return v.toFixed(1) + 'd';
	}

	function fmtSiPct(v: number | null | undefined): string {
		if (v === null || v === undefined || v === 0) return '—';
		return v.toFixed(1) + '%';
	}
</script>

<svelte:head>
	<title>Crypto Signals — Meridian</title>
	<meta name="description" content="Crypto-adjacent smart money signals — ARK trades, insider activity, dark pool, short interest across crypto equities" />
</svelte:head>

<div class="space-y-6">

	<!-- Header -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Crypto Signals</h1>
			<p class="page-subtitle">Smart money activity across crypto-adjacent equities · BTC/ETH · ARK · Insiders · Dark Pool · Short Interest</p>
		</div>
		{#if d?.cached_at}
			<span class="cache-label">Updated {new Date(d.cached_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
		{/if}
	</div>

	{#if data.error}
		<Card>
			{#snippet children()}
				<p class="error-msg">Failed to load crypto signals: {data.error}</p>
			{/snippet}
		</Card>
	{:else if d}

		<!-- Row 1: BTC + ETH Price Cards -->
		<div class="two-col">
			<!-- BTC -->
			<div class="card-base">
				<div class="section-label">BITCOIN</div>
				<div class="price-hero">
					<div class="price-main">
						<span class="price-ticker">BTC</span>
						<span class="price-value">{fmtPrice(d.crypto_prices?.btc?.price)}</span>
					</div>
					<span class="price-change" style="color: {changeColor(d.crypto_prices?.btc?.change_24h_pct)}">
						{fmtChange(d.crypto_prices?.btc?.change_24h_pct)}
					</span>
				</div>
				{#if d.crypto_prices?.btc?.chart_90d?.length}
					<div class="mini-chart-label">90 DAY PRICE</div>
					<LWLineChart
						data={toChartData(d.crypto_prices.btc.chart_90d)}
						height={130}
						color="#f59e0b"
						class="mini-chart"
					/>
				{/if}
			</div>

			<!-- ETH -->
			<div class="card-base">
				<div class="section-label">ETHEREUM</div>
				<div class="price-hero">
					<div class="price-main">
						<span class="price-ticker">ETH</span>
						<span class="price-value">{fmtPrice(d.crypto_prices?.eth?.price)}</span>
					</div>
					<span class="price-change" style="color: {changeColor(d.crypto_prices?.eth?.change_24h_pct)}">
						{fmtChange(d.crypto_prices?.eth?.change_24h_pct)}
					</span>
				</div>
				{#if d.crypto_prices?.eth?.chart_90d?.length}
					<div class="mini-chart-label">90 DAY PRICE</div>
					<LWLineChart
						data={toChartData(d.crypto_prices.eth.chart_90d)}
						height={130}
						color="#818cf8"
						class="mini-chart"
					/>
				{/if}
			</div>
		</div>

		<!-- Row 2: Summary Card -->
		<div class="card-base">
			<div class="section-label">SIGNAL SUMMARY</div>
			<div class="summary-stats">
				<div class="stat-chip">
					<span class="stat-val">{d.summary?.total_signals ?? 0}</span>
					<span class="stat-label">Signals</span>
				</div>
				<div class="stat-chip">
					<span class="stat-val" style="color: var(--green)">{d.summary?.bullish_signals ?? 0}</span>
					<span class="stat-label">Bullish</span>
				</div>
				<div class="stat-chip">
					<span class="stat-val" style="color: var(--red)">{d.summary?.bearish_signals ?? 0}</span>
					<span class="stat-label">Bearish</span>
				</div>
				{#if d.summary?.most_active_ticker}
					<div class="stat-chip">
						<span class="stat-val">{d.summary.most_active_ticker}</span>
						<span class="stat-label">Most Active</span>
					</div>
				{/if}
				</div>
			{#if d.ark_sentiment}
				<div class="ark-sentiment-row">
					<span class="ark-label">ARK 30d</span>
					<span class="ark-badge" style="color: {d.ark_sentiment.net === 'bullish' ? 'var(--green)' : d.ark_sentiment.net === 'bearish' ? 'var(--red)' : 'var(--amber)'}">
						{d.ark_sentiment.net?.toUpperCase()}
					</span>
					<span class="ark-detail">({d.ark_sentiment.buys}B / {d.ark_sentiment.sells}S)</span>
				</div>
			{/if}
			{#if d.summary?.narrative}
				<p class="summary-narrative">{d.summary.narrative}</p>
			{/if}
		</div>

		<!-- Row 3: Smart Money Signals (stocks only) -->
		{#if d.smart_money_signals?.length}
			<div class="card-base">
				<div class="section-label">SMART MONEY SIGNALS — CRYPTO STOCKS</div>
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Ticker</th>
								<th>Company</th>
								<th class="text-right">Score</th>
								<th>Direction</th>
								<th>Sources</th>
							</tr>
						</thead>
						<tbody>
							{#each d.smart_money_signals as sig}
								<tr>
									<td>
										<a href="/ticker/{sig.ticker}" class="ticker-link">{sig.ticker}</a>
									</td>
									<td class="text-muted">{sig.company || '—'}</td>
									<td class="text-right">
										<span class="score-badge" style="color: {scoreColor(sig.score)}">
											{fmtScore(sig.score)}
										</span>
									</td>
									<td>
										<span class="direction-badge" class:bullish={sig.direction?.toLowerCase() === 'bullish'} class:bearish={sig.direction?.toLowerCase() === 'bearish'}>
											{sig.direction || '—'}
										</span>
									</td>
									<td class="text-muted source-tags">
										{#each (sig.sources || []) as src}
											<span class="source-tag">{src}</span>
										{/each}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}

		<!-- Row 4: ARK Trades + Insider Activity -->
		<div class="two-col">
			<!-- ARK Trades -->
			<div class="card-base">
				<div class="section-label">ARK INVEST — CRYPTO STOCK TRADES</div>
				{#if d.ark_trades?.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Date</th>
									<th>Ticker</th>
									<th>ETF</th>
									<th>Type</th>
									<th class="text-right">Shares</th>
									<th class="text-right">Weight %</th>
								</tr>
							</thead>
							<tbody>
								{#each d.ark_trades.slice(0, 20) as trade}
									<tr>
										<td class="mono dim">{trade.date?.slice(5) || '—'}</td>
										<td>
											<a href="/ticker/{trade.ticker}" class="ticker-link">{trade.ticker}</a>
										</td>
										<td class="dim">{trade.etf || '—'}</td>
										<td>
											<span class="trade-type" class:buy={trade.trade_type === 'Buy' || trade.change_type === 'INCREASED' || trade.change_type === 'NEW_POSITION'} class:sell={trade.trade_type === 'Sell' || trade.change_type === 'DECREASED' || trade.change_type === 'SOLD_OUT'}>
												{trade.trade_type || trade.change_type || '—'}
											</span>
										</td>
										<td class="text-right mono">{fmtVol(trade.shares)}</td>
										<td class="text-right mono dim">{trade.weight_pct ? trade.weight_pct.toFixed(2) + '%' : '—'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No recent ARK crypto stock trades</p>
				{/if}
			</div>

			<!-- Insider Trades -->
			<div class="card-base">
				<div class="section-label">INSIDER ACTIVITY</div>
				{#if d.insider_trades?.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th>Insider</th>
									<th>Type</th>
									<th class="text-right">Value</th>
								</tr>
							</thead>
							<tbody>
								{#each d.insider_trades.slice(0, 15) as trade}
									<tr>
										<td>
											<a href="/ticker/{trade.ticker}" class="ticker-link">{trade.ticker}</a>
										</td>
										<td class="text-muted truncate">{trade.insider_name || '—'}{#if trade.title}<span class="insider-title"> · {trade.title}</span>{/if}</td>
										<td>
											<span class="trade-type" class:buy={trade.transaction_type === 'Purchase'} class:sell={trade.transaction_type === 'Sale'}>
												{trade.transaction_type || '—'}
											</span>
										</td>
										<td class="text-right mono">{fmtMoney(trade.value)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No recent insider trades in crypto equities</p>
				{/if}
			</div>
		</div>

		<!-- Row 5: Short Interest + Dark Pool -->
		<div class="two-col">
			<!-- Short Interest -->
			<div class="card-base">
				<div class="section-label">SHORT INTEREST</div>
				{#if d.short_interest?.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th class="text-right">Short Interest</th>
									<th class="text-right">Change</th>
									<th class="text-right">DTC</th>
									<th class="text-right">% Float</th>
								</tr>
							</thead>
							<tbody>
								{#each d.short_interest.slice(0, 15) as si}
									<tr>
										<td>
											<a href="/ticker/{si.ticker}" class="ticker-link">{si.ticker}</a>
										</td>
										<td class="text-right mono">{fmtVol(si.short_interest)}</td>
										<td class="text-right mono" style="color: {si.change_pct > 0 ? 'var(--red)' : si.change_pct < 0 ? 'var(--green)' : 'var(--text-muted)'}">
											{fmtPct(si.change_pct)}
										</td>
										<td class="text-right mono">{fmtDtc(si.days_to_cover)}</td>
										<td class="text-right mono">{fmtSiPct(si.short_pct_float)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No short interest data for crypto equities</p>
				{/if}
			</div>

			<!-- Dark Pool -->
			<div class="card-base">
				<div class="section-label">DARK POOL ACTIVITY</div>
				{#if d.darkpool?.length}
					<div class="table-wrap">
						<table class="data-table compact">
							<thead>
								<tr>
									<th>Ticker</th>
									<th class="text-right">Total Vol</th>
									<th class="text-right">DPI</th>
									<th class="text-right">Off-Exch %</th>
									<th class="text-right">Short %</th>
								</tr>
							</thead>
							<tbody>
								{#each d.darkpool as dp}
									<tr>
										<td>
											<a href="/ticker/{dp.ticker}" class="ticker-link">{dp.ticker}</a>
										</td>
										<td class="text-right mono">{fmtVol(dp.total_volume)}</td>
										<td class="text-right mono">{fmtDpi(dp.dpi)}</td>
										<td class="text-right mono">{fmtPct(dp.off_exchange_pct)}</td>
										<td class="text-right mono">{fmtPct(dp.short_pct)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No dark pool data for crypto equities</p>
				{/if}
			</div>
		</div>

		<!-- Row 6: Congress Trades -->
		<div class="card-base">
			<div class="section-label">CONGRESS TRADES</div>
			{#if d.congress_trades?.length}
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Date</th>
								<th>Representative</th>
								<th>Party</th>
								<th>Ticker</th>
								<th>Type</th>
								<th class="text-right">Amount</th>
							</tr>
						</thead>
						<tbody>
							{#each d.congress_trades as trade}
								<tr>
									<td class="mono dim">{trade.transaction_date || '—'}</td>
									<td>{trade.representative || '—'}</td>
									<td class="dim">{trade.party?.charAt(0) || '—'}</td>
									<td>
										<a href="/ticker/{trade.ticker}" class="ticker-link">{trade.ticker}</a>
									</td>
									<td>
										<span class="trade-type" class:buy={trade.trade_type === 'Buy' || trade.trade_type === 'Purchase'} class:sell={trade.trade_type === 'Sell' || trade.trade_type === 'Sale'}>
											{trade.trade_type || '—'}
										</span>
									</td>
									<td class="text-right mono dim">{trade.amount_range || '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="empty-congress">
					<p class="empty-state-main">No recent crypto-related Congress trades</p>
					<p class="empty-state-sub">This section populates when members disclose positions in crypto-adjacent stocks (COIN, MSTR, IBIT, MARA, etc.)</p>
				</div>
			{/if}
		</div>

		<!-- Row 7: 13F Institution Holdings -->
		{#if d.institution_holdings?.length}
			<div class="card-base">
				<div class="section-label">INSTITUTIONAL HOLDINGS (13F)</div>
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Institution</th>
								<th>Ticker</th>
								<th class="text-right">Value</th>
								<th>Filing Date</th>
							</tr>
						</thead>
						<tbody>
							{#each d.institution_holdings as holding}
								<tr>
									<td class="truncate">{holding.institution || '—'}</td>
									<td>
										<a href="/ticker/{holding.ticker}" class="ticker-link">{holding.ticker}</a>
									</td>
									<td class="text-right mono">{fmtMoney(holding.value)}</td>
									<td class="mono dim">{holding.filing_date || '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}

	{:else}
		<Card>
			{#snippet children()}
				<div class="loading-state">Loading crypto signals…</div>
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

	/* Price hero */
	.price-hero {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
	}

	.price-main {
		display: flex;
		align-items: baseline;
		gap: 10px;
	}

	.price-ticker {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--text-dimmed);
	}

	.price-value {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 28px;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1;
	}

	.price-change {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 16px;
		font-weight: 600;
	}

	/* Summary */
	.summary-stats {
		display: flex;
		gap: 24px;
		flex-wrap: wrap;
		margin-bottom: 12px;
	}

	.stat-chip {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.stat-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 24px;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1;
	}

	.stat-label {
		font-size: 11px;
		color: var(--text-dimmed);
		letter-spacing: 0.03em;
	}

	.ark-sentiment-row {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 12px;
		padding: 8px 12px;
		background: var(--bg-elevated);
		border-radius: 8px;
	}

	.ark-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.04em;
		color: var(--text-dimmed);
	}

	.ark-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 0.03em;
	}

	.ark-detail {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
	}

	.summary-narrative {
		font-size: 13px;
		color: var(--text-muted);
		line-height: 1.6;
	}

	/* Tables */
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
	.text-muted { color: var(--text-muted); }

	.mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.dim { color: var(--text-dimmed); }

	.truncate {
		max-width: 160px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.insider-title {
		font-size: 10px;
		color: var(--text-dimmed);
	}

	.ticker-link {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-weight: 600;
		color: var(--text-primary);
		text-decoration: none;
		letter-spacing: 0.02em;
	}

	.ticker-link:hover {
		color: var(--accent, #818cf8);
	}

	.score-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-weight: 700;
	}

	.trade-type {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--text-muted);
	}

	.trade-type.buy { color: var(--green); }
	.trade-type.sell { color: var(--red); }

	.direction-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--text-muted);
	}

	.direction-badge.bullish { color: var(--green); }
	.direction-badge.bearish { color: var(--red); }

	.source-tags {
		display: flex;
		gap: 4px;
		flex-wrap: wrap;
	}

	.source-tag {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.03em;
		padding: 2px 6px;
		border-radius: 4px;
		background: var(--bg-elevated);
		color: var(--text-dimmed);
		white-space: nowrap;
	}

	/* Empty states */
	.empty-state {
		color: var(--text-dimmed);
		font-size: 12px;
		padding: 12px 0;
	}

	.empty-congress {
		text-align: center;
		padding: 20px 0;
	}

	.empty-state-main {
		color: var(--text-muted);
		font-size: 13px;
		margin-bottom: 4px;
	}

	.empty-state-sub {
		color: var(--text-dimmed);
		font-size: 11px;
	}
</style>
